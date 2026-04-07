#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国主要城市经度数据表
格式: {城市名: 经度(度)}
"""

CITIES = {
    # 北京地区
    '北京': 120.15,
    '天津': 117.2,
    
    # 上海地区
    '上海': 121.47,
    '浙江': 120.15,
    '杭州': 120.15,
    
    # 广州地区
    '广州': 113.26,
    '深圳': 114.07,
    '珠海': 113.53,
    
    # 成都地区
    '成都': 104.07,
    '重庆': 106.55,
    
    # 西安地区
    '西安': 108.95,
    
    # 南京地区
    '南京': 118.8,
    
    # 武汉地区
    '武汉': 114.31,
    
    # 沈阳地区
    '沈阳': 123.43,
    '哈尔滨': 126.53,
    
    # 南昌地区
    '南昌': 115.86,
    
    # 福州地区
    '福州': 119.3,
    '厦门': 118.09,
    
    # 苏州地区
    '苏州': 120.59,
    
    # 其他
    '长沙': 112.94,
    '郑州': 113.65,
    '青岛': 120.33,
    '大连': 121.62,
    '昆明': 102.87,
    '南宁': 108.33,
    '海口': 110.35,
    '石家庄': 114.57,
    '太原': 112.55,
    '兰州': 103.83,
    '西宁': 101.77,
    '银川': 106.27,
    '乌鲁木齐': 87.68,
}

def get_longitude(city_name):
    """
    获取城市经度
    返回: 经度(浮点数) 或 None
    """
    # 精确匹配
    if city_name in CITIES:
        return CITIES[city_name]
    
    # 模糊匹配 (取前缀)
    for key in CITIES.keys():
        if city_name.startswith(key) or key.startswith(city_name):
            return CITIES[key]
    
    return None

def calculate_solar_time(hour, minute, second, longitude, timezone_offset=8):
    """
    计算真太阳时
    
    参数:
        hour: 时(0-23)
        minute: 分(0-59)
        second: 秒(0-59)
        longitude: 经度(度)
        timezone_offset: 时区偏差 (默认中国 UTC+8)
    
    返回:
        (修正后的小时, 修正后的分钟)
    
    公式:
        真太阳时 = 本地时 + (120° - 经度) × 4分钟/度
        
    说明:
        - 中国统一使用 UTC+8 (东八区，标准经线120°)
        - 如果经度 < 120°，需要加时间（地区在标准线西边）
        - 如果经度 > 120°，需要减时间（地区在标准线东边）
    """
    # 转换为总分钟数
    total_minutes = hour * 60 + minute
    
    # 计算时差 (分钟)
    # 标准线是 120°，每1°差4分钟
    # 注意：这里直接计算分钟，不要除以60再乘以60
    time_diff_minutes = (120 - longitude) * 4
    
    # 应用修正
    adjusted_minutes = total_minutes + time_diff_minutes
    
    # 处理跨天情况
    if adjusted_minutes < 0:
        adjusted_minutes += 24 * 60
    elif adjusted_minutes >= 24 * 60:
        adjusted_minutes -= 24 * 60
    
    # 转换回小时和分钟
    new_hour = int(adjusted_minutes // 60)
    new_minute = int(adjusted_minutes % 60)
    
    return new_hour, new_minute

if __name__ == '__main__':
    # 测试
    print("测试真太阳时计算:")
    print("北京 (120.15°E):", calculate_solar_time(8, 0, 0, 120.15))
    print("西安 (108.95°E):", calculate_solar_time(8, 0, 0, 108.95))
    print("上海 (121.47°E):", calculate_solar_time(8, 0, 0, 121.47))
