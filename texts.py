import collections


prec_level_s = [
    (-0.01, '数据异常'),
    (0.001, '无'),
    (0.031, '毛毛雨'),
    (0.25, '小雨'),
    (0.35, '中雨'),
    (0.48, '大雨'),
    (1.001, '暴雨'),
]

skycon_s = {
    'CLEAR_DAY': '晴',
    'CLEAR_NIGHT': '晴',
    'PARTLY_CLOUDY_DAY': '多云',
    'PARTLY_CLOUDY_NIGHT': '多云',
    'CLOUDY': '阴',
    'LIGHT_HAZE': '轻度雾霾',
    'MODERATE_HAZE': '中度雾霾',
    'HEAVY_HAZE': '重度雾霾',
    'LIGHT_RAIN': '小雨',
    'MODERATE_RAIN': '中雨',
    'HEAVY_RAIN': '大雨',
    'STORM_RAIN': '暴雨',
    'FOG': '雾',
    'SNOW': '雪',
    'LIGHT_SNOW': '小雪',
    'MODERATE_SNOW': '中雪',
    'HEAVY_SNOW': '大雪',
    'STORM_SNOW': '暴雪',
    'DUST': '浮尘',
    'SAND': '沙尘',
    'WIND': '大风',
    'THUNDER_SHOWER': '雷阵雨',
    'HAIL': '冰雹',
    'SLEET': '雨夹雪',
}


def skycon(key):
    return skycon_s.get(key, "未知")

def weekday(key):
    return "星期一 星期二 星期三 星期四 星期五 星期六 星期日".split()[key % 7]

def prec_level(val):
    for upper, s in prec_level_s:
        if val <= upper:
            return s
    return "未知"
