#!/usr/bin/python3

import datetime
import json
import os
import requests
import sys
import telegram

import texts


DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE = os.path.join(DIR, "config.json")


class CaiYun:
    def __init__(self, config):
        self.config = dict(config)

    def fetch_api(self):
        url = 'https://api.caiyunapp.com/v2.5/{}/{},{}/weather.json?lang=zh_CN&alert=true'.format(
            self.config['token'], self.config['longitude'], self.config['latitude'])
        for _ in range(self.config['retry']):
            try:
                res = requests.get(url)
                res.raise_for_status()
                data = res.json()
                if data['status'] == 'ok':
                    return data
            except Exception:
                exc_type, exc_val, exc_tb = sys.exc_info()
                print(f"{exc_type.__name__}: {exc_val}", file=sys.stderr)
        return None


def extract_daily(daily_data):
    daily = {}
    for key in daily_data:
        if isinstance(daily_data[key], list):
            daily[key] = daily_data[key][0]
        elif isinstance(daily_data[key], dict):
            daily[key] = extract_daily(daily_data[key])
        else:
            daily[key] = daily_data[key]
    return daily


def send_forecast():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    bot = telegram.Bot(token=config['telegram']['token'])
    caiyun = CaiYun(config['caiyun'])
    api_data = caiyun.fetch_api()
    if not api_data:
        return

    daily_data = api_data['result']['daily']
    if daily_data['status'] != "ok":
        return
    daily = extract_daily(daily_data)

    date = datetime.datetime.fromisoformat(daily['skycon']['date'])
    date_s = date.strftime("%Y 年 %m 月 %d 日")
    skycon_day = daily['skycon_08h_20h']['value']
    skycon_night = daily['skycon_20h_32h']['value']
    temp_high = daily['temperature']['max']
    temp_low = daily['temperature']['min']
    hum_high = daily['humidity']['max']
    hum_low = daily['humidity']['min']
    hum_avg = daily['humidity']['avg']

    text = f"" \
           f"\n温度：{temp_low:.1f}°C - {temp_high:.1f}°C" \
           f"\n湿度：{hum_avg:.0%}" \
           f"\n白天天气：{texts.skycon(skycon_day)}" \
           f"\n夜间天气：{texts.skycon(skycon_night)}" \
           ""
    text = f"*{date_s}*" + telegram.utils.helpers.escape_markdown(text, 2)
    bot.send_message(chat_id=config['telegram']['target'], text=text, parse_mode="MarkdownV2",
                     disable_web_page_preview=True)


def main():
    send_forecast()


if __name__ == "__main__":
    main()
