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

alert_type_s = {
    '01': '台风',
    '02': '暴雨',
    '03': '暴雪',
    '04': '寒潮',
    '05': '大风',
    '06': '沙尘暴',
    '07': '高温',
    '08': '干旱',
    '09': '雷电',
    '10': '冰雹',
    '11': '霜冻',
    '12': '大雾',
    '13': '霾',
    '14': '道路结冰',
    '15': '森林火灾',
    '16': '雷雨大风',
    '17': '春季沙尘天气趋势预警',
    '18': '沙尘',
}

alert_level_s = {
    '00': '白色预警',
    '01': '蓝色预警',
    '02': '黄色预警',
    '03': '橙色预警',
    '04': '红色预警'
}

def skycon(key):
    return skycon_s.get(key, "未知")

def weekday(key):
    return "星期一 星期二 星期三 星期四 星期五 星期六 星期日".split()[key % 7]

def prec_level(val):
    for upper, s in prec_level_s:
        if val <= upper:
            return s
    return f"未知（{val}）"

def alert(code):
    try:
        return alert_type_s[code[:2]] + alert_level_s[code[-2:]]
    except KeyError:
        return f"未知（{code}）"
