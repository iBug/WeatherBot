#!/usr/bin/python3


import logger

import argparse
import datetime
import io
import json
import logging
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
import sys
import telegram
import time

import texts
from telegram.utils.helpers import escape_markdown

from classes import CaiYun, SaveData


DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(DIR, "config.json")
DATA_FILE = os.path.join(DIR, "data.json")


def setup():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    bot = telegram.Bot(token=config['telegram']['token'])
    caiyun = CaiYun(config['caiyun'])
    api_data = caiyun.fetch_api()
    if not api_data:
        return config, bot, None
    return config, bot, api_data


def extract_daily(daily_data, days=0):
    daily = {}
    for key in daily_data:
        if isinstance(daily_data[key], list):
            daily[key] = daily_data[key][days]
        elif isinstance(daily_data[key], dict):
            daily[key] = extract_daily(daily_data[key], days)
        else:
            daily[key] = daily_data[key]
    return daily


def plot_precipitation(api_data):
    try:
        precipitation = api_data['result']['minutely']['precipitation_2h']
        matplotlib.rc("font", **{'family': "sans-serif", 'size': 13, 'sans-serif': ["Amazon Ember", "Gotham", "DejaVu Sans"]})
        plt.figure(figsize=(6, 3))
        # plt.xlabel("Time (min)")
        plt.plot(np.arange(120), np.array(precipitation))
        plt.ylim(bottom=0)
        if plt.axis()[3] > 0.03:
            plt.hlines(0.03, 0, 120, colors='skyblue', linestyles='dashed')
        if plt.axis()[3] > 0.25:
            plt.hlines(0.25, 0, 120, colors='blue', linestyles='dashed')
        if plt.axis()[3] > 0.35:
            plt.hlines(0.35, 0, 120, colors='orange', linestyles='dashed')
        if plt.axis()[3] > 0.48:
            plt.hlines(0.48, 0, 120, colors='darkred', linestyles='dashed')

        plt.title("Precipitation in 2 hours", weight="bold")

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close('all')
        return buf.read()
    except Exception:
        return None


def update_realtime():
    config, bot, api_data = setup()
    data = api_data['result']['realtime']
    if data['status'] != "ok":
        return

    date = datetime.datetime.fromtimestamp(api_data['server_time'])
    date_s = date.strftime("%Y 年 %m 月 %d 日 {} %H:%M").format(texts.weekday(date.weekday()))
    temperature = data['temperature']
    humidity = data['humidity']
    skycon = data['skycon']
    precipitation_d = data['precipitation']['local']
    precipitation_s = ""
    if precipitation_d['status'] == 'ok':
        precipitation_s = f"\n降水：{texts.prec_level(precipitation_d['intensity'])}"
    visibility = data['visibility']
    aqi_s = data['air_quality']['description']['chn']
    ultraviolet = data['life_index']['ultraviolet']['desc']
    comfort = data['life_index']['comfort']['desc']

    heading = "*{}*".format(f"实时天气：{temperature:.0f}°C  {texts.skycon(skycon)}")
    text = f"\n湿度：{humidity:.0%}" \
           f"{precipitation_s}" \
           f"\n能见度：{visibility:.1f} km" \
           f"\n空气质量：{aqi_s}" \
           f"\n紫外线：{ultraviolet}" \
           f"\n舒适度：{comfort}" \
           ""
    text = heading + escape_markdown(text, 2) + f"\n\n*{date_s}*\n[未来 2 小时降水](https://t.me/ustc_weather/{config['telegram']['precipitation_id']})"
    bot.edit_message_text(chat_id=config['telegram']['target'], message_id=config['telegram']['realtime_id'],
                          text=text, parse_mode="MarkdownV2", disable_web_page_preview=True)
    #title = f"USTC Weather: {temperature:.0f}°C {texts.skycon(skycon)}"
    #bot.set_chat_title(chat_id=config['telegram']['target'], title=title)


def update_precipitation():
    config, bot, api_data = setup()
    data = api_data['result']['minutely']
    if data['status'] != "ok":
        return

    date = datetime.datetime.fromtimestamp(api_data['server_time'])
    date_s = date.strftime("%Y 年 %m 月 %d 日 {} %H:%M").format(texts.weekday(date.weekday()))

    buf = plot_precipitation(api_data)
    caption = api_data['result']['forecast_keypoint'] + f"\n*{date_s}*"
    media = telegram.InputMediaPhoto(buf, caption=caption, parse_mode="MarkdownV2")

    bot.edit_message_media(chat_id=config['telegram']['target'], message_id=config['telegram']['precipitation_id'], media=media)


def update_alert():
    config, bot, api_data = setup()
    alert_data = api_data['result']['alert']
    if alert_data['status'] != "ok":
        return

    save_data = SaveData(DATA_FILE)
    last_timestamp = save_data.data.get('alert_timestamp', 0)
    next_timestamp = last_timestamp

    for content in alert_data['content']:
        timestamp = content['pubtimestamp']
        if timestamp <= last_timestamp:
            # Already processed
            return
        date = datetime.datetime.fromtimestamp(timestamp)
        date_s = date.strftime("%Y 年 %m 月 %d 日 {} %H:%M:%S").format(texts.weekday(date.weekday()))
        text = "*【{}】*\n".format(escape_markdown(content['title'], 2))
        text += escape_markdown(content['description'], 2) + f"\n\n*发布时间*：{escape_markdown(date_s, 2)}\n\\#预警"
        bot.send_message(chat_id=config['telegram']['target'], text=text, parse_mode="MarkdownV2",
                         disable_web_page_preview=True)
        if timestamp > next_timestamp:
            next_timestamp = timestamp 
    save_data.data['alert_timestamp'] = next_timestamp
    save_data.save()


def send_forecast():
    config, bot, api_data = setup()
    daily_data = api_data['result']['daily']
    if daily_data['status'] != "ok":
        return
    daily = extract_daily(daily_data, 1)

    date = datetime.datetime.fromisoformat(daily['skycon']['date'])
    date_s = date.strftime("%Y 年 %m 月 %d 日 ") + texts.weekday(date.weekday())
    skycon_day = daily['skycon_08h_20h']['value']
    skycon_night = daily['skycon_20h_32h']['value']
    temp_high = daily['temperature']['max']
    temp_low = daily['temperature']['min']
    hum_high = daily['humidity']['max']
    hum_low = daily['humidity']['min']
    hum_avg = daily['humidity']['avg']
    aqi = daily['air_quality']['aqi']['avg']['chn']
    sunrise_time = daily['astro']['sunrise']['time']
    sunset_time = daily['astro']['sunset']['time']
    ultraviolet = daily['life_index']['ultraviolet']['desc']
    comfort = daily['life_index']['comfort']['desc']

    text = f"" \
           f"\n温度：{temp_low:.1f}°C - {temp_high:.1f}°C" \
           f"\n湿度：{hum_avg:.0%}" \
           f"\n白天天气：{texts.skycon(skycon_day)}" \
           f"\n夜间天气：{texts.skycon(skycon_night)}" \
           f"\n空气质量：{aqi:.0f}" \
           f"\n日出日落：{sunrise_time} - {sunset_time}" \
           f"\n紫外线：{ultraviolet}" \
           f"\n舒适度：{comfort}" \
           ""
    text = f"\\#天气预报\n*{date_s}*" + escape_markdown(text, 2)
    bot.send_message(chat_id=config['telegram']['target'], text=text, parse_mode="MarkdownV2",
                     disable_web_page_preview=True)  # , disable_notification=True)


def lambda_main(event, context):
    pass


def main(args):
    logger.logger.setLevel(logger.level_s[args.verbose.upper()])
    if not args.action:
        logging.warning(f"No action specified, exiting")
        return
    action = args.action
    logging.info(f"Action: {action}")
    if action == "cron":
        try:
            update_realtime()
        except Exception:
            pass
        try:
            update_alert()
        except Exception:
            pass
        try:
            update_precipitation()
        except Exception:
            pass
        return
    elif action == "forecast":
        return send_forecast()
    elif action == "realtime":
        return update_realtime()
    elif action == "alert":
        return update_alert()
    elif action == "precipitation":
        return update_precipitation()
    else:
        raise ValueError(f"Unknown action {action}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="a Telegram weather bot")
    parser.add_argument("action", type=str, nargs="?")
    parser.add_argument("-v", "--verbose", metavar="level", type=str, nargs="?", const="debug", default="warning",
                        choices=[x.lower() for x in logger.level_s], help="logging/verbosity level")
    args = parser.parse_args()
    main(args)
