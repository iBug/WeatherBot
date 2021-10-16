#!/usr/bin/python3

import datetime
import json
import logging
import matplotlib
import matplotlib.pyplot as plt
import os
import requests
import sys
import telegram
import time

import texts
from telegram.utils.helpers import escape_markdown


DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(DIR, "config.json")

logger = logging.getLogger(__name__)


class CaiYun:
    def __init__(self, config):
        self.config = dict(config)
        self.cache_file = os.path.join(DIR, config['cache_file'])
        self.cache_ttl = config['cache_ttl']

    def get_cache(self):
        if not os.path.exists(self.cache_file):
            return False
        with open(self.cache_file, "r") as f:
            now = time.time()
            data = json.load(f)
        if now < data['server_time'] + self.cache_ttl:
            return data
        return None  # cache expired

    def fetch_api(self):
        cache = self.get_cache()
        if cache:
            return cache

        url = 'https://api.caiyunapp.com/v2.5/{}/{},{}/weather.json?lang=zh_CN&alert=true'.format(
            self.config['token'], self.config['longitude'], self.config['latitude'])
        for _ in range(self.config['retry']):
            try:
                res = requests.get(url)
                res.raise_for_status()
                data = res.json()
                if data['status'] == 'ok':
                    break
            except Exception:
                exc_type, exc_val, exc_tb = sys.exc_info()
                print(f"{exc_type.__name__}: {exc_val}", file=sys.stderr)
                time.sleep(1)
        else:
            return None
        with open(self.cache_file, "w") as f:
            json.dump(data, f, separators=(',', ':'))
        return data


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
    text = heading + escape_markdown(text, 2) + f"\n*{date_s}*"
    bot.edit_message_text(chat_id=config['telegram']['target'], message_id=config['telegram']['realtime_id'],
                          text=text, parse_mode="MarkdownV2", disable_web_page_preview=True)
    return

    title = f"USTC Weather: {temperature:.0f}°C {texts.skycon(skycon)}"
    bot.set_chat_title(chat_id=config['telegram']['target'], title=title)


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
    text = f"【天气预报】\n*{date_s}*" + telegram.utils.helpers.escape_markdown(text, 2)
    bot.send_message(chat_id=config['telegram']['target'], text=text, parse_mode="MarkdownV2",
                     disable_web_page_preview=True)  # , disable_notification=True)


def lambda_main(event, context):
    send_forecast()


def main():
    if len(sys.argv) == 1:
        return send_forecast()
    action = sys.argv[1]
    if action == "realtime":
        return update_realtime()
    else:
        raise ValueError(f"Unknown action {action}")


if __name__ == "__main__":
    main()
