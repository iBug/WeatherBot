import json
import logging
import os
import random
import requests
import sys
import time


DIR = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger()


class CaiYun:
    def __init__(self, config):
        self.config = dict(config)
        self.tokens = config.get("tokens", [config.get("token")])
        self.cache_file = os.path.join(DIR, config['cache_file'])
        self.cache_ttl = config['cache_ttl']
        self.timeout = config['timeout']

    def get_cache(self):
        if not os.path.exists(self.cache_file):
            return False
        try:
            with open(self.cache_file, "r") as f:
                now = time.time()
                data = json.load(f)
        except Exception:
            exc_type, exc_val, exc_tb = sys.exc_info()
            print(f"{exc_type.__name__}: {exc_val}", file=sys.stderr)
            return None  # invalid cache
        if now < data['server_time'] + self.cache_ttl:
            return data
        return None  # cache expired

    def fetch_api(self):
        cache = self.get_cache()
        if cache:
            return cache

        for _ in range(self.config['retry']):
            try:
                token = random.choice(self.tokens)
                url = 'https://api.caiyunapp.com/v2.6/{}/{},{}/weather.json?lang=zh_CN&alert=true'
                url = url.format(token, self.config['longitude'], self.config['latitude'])

                res = requests.get(url, timeout=self.timeout)
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

        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(data, f, separators=(',', ':'))
        return data


class SaveData():
    base_dir = None

    def __init__(self, filename):
        self.filename = os.path.join(self.base_dir, filename + ".json")
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                self.data = json.load(f)

    def save(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, separators=(',', ':'))

    @classmethod
    def set_base_dir(cls, base):
        cls.base_dir = base
