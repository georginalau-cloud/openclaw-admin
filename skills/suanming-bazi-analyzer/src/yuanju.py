#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[04] src/yuanju.py - 原局排盘模块
调用层级：被 src/bazi_chart.py 调用
依赖：src/jieqi.py [02]、lib/ganzhi_calculator.py [03]

职责：
- 接收真太阳时校准后的出生信息
- 推导四柱干支（年/月/日/时）
- 计算每柱的：藏干、十神、五行、纳音、阴阳
- 输出完整的原局结构化数据

依赖：
  vendor/lunar_python  ← 四柱干支、农历信息
  src/jieqi.py         ← 正确的月支（基于12节）

调用方式：
  python3 src/yuanju.py --year 1995 --month 9 --day 4 --hour 21 --minute 44 --gender male --city 江阴
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List

# vendor 路径
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_SKILL_DIR, 'vendor'))

try:
    from lunar_python import Solar, Lunar
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False

# 同目录的 jieqi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jieqi import get_jieqi_info


# ─────────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────────

GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 12时辰范围（真太阳时）
SHICHEN = [
    (23, 1,  '子'), (1,  3,  '丑'), (3,  5,  '寅'), (5,  7,  '卯'),
    (7,  9,  '辰'), (9,  11, '巳'), (11, 13, '午'), (13, 15, '未'),
    (15, 17, '申'), (17, 19, '酉'), (19, 21, '戌'), (21, 23, '亥'),
]

# 五鼠遁：日干 → 子时天干起点
WUSHU_DUN = {
    '甲': '甲', '己': '甲',
    '乙': '丙', '庚': '丙',
    '丙': '戊', '辛': '戊',
    '丁': '庚', '壬': '庚',
    '戊': '壬', '癸': '壬',
}

# 地支藏干（主气在前）
ZHI_CANGYGAN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲'],
}

# 十神（简称）：以日干为基准
TEN_GODS = {
    '甲': {'甲':'比','乙':'劫','丙':'食','丁':'伤','戊':'才','己':'财','庚':'杀','辛':'官','壬':'枭','癸':'印'},
    '乙': {'甲':'劫','乙':'比','丙':'伤','丁':'食','戊':'财','己':'才','庚':'官','辛':'杀','壬':'印','癸':'枭'},
    '丙': {'甲':'枭','乙':'印','丙':'比','丁':'劫','戊':'食','己':'伤','庚':'才','辛':'财','壬':'杀','癸':'官'},
    '丁': {'甲':'印','乙':'枭','丙':'劫','丁':'比','戊':'伤','己':'食','庚':'财','辛':'才','壬':'官','癸':'杀'},
    '戊': {'甲':'杀','乙':'官','丙':'枭','丁':'印','戊':'比','己':'劫','庚':'食','辛':'伤','壬':'才','癸':'财'},
    '己': {'甲':'官','乙':'杀','丙':'印','丁':'枭','戊':'劫','己':'比','庚':'伤','辛':'食','壬':'财','癸':'才'},
    '庚': {'甲':'才','乙':'财','丙':'杀','丁':'官','戊':'枭','己':'印','庚':'比','辛':'劫','壬':'食','癸':'伤'},
    '辛': {'甲':'财','乙':'才','丙':'官','丁':'杀','戊':'印','己':'枭','庚':'劫','辛':'比','壬':'伤','癸':'食'},
    '壬': {'甲':'食','乙':'伤','丙':'才','丁':'财','戊':'杀','己':'官','庚':'枭','辛':'印','壬':'比','癸':'劫'},
    '癸': {'甲':'伤','乙':'食','丙':'财','丁':'才','戊':'官','己':'杀','庚':'印','辛':'枭','壬':'劫','癸':'比'},
}

GAN_WUXING = {
    '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
    '己':'土','庚':'金','辛':'金','壬':'水','癸':'水',
}
ZHI_WUXING = {
    '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
    '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水',
}

NAYIN = {
    '甲子':'海中金','乙丑':'海中金','丙寅':'炉中火','丁卯':'炉中火',
    '戊辰':'大林木','己巳':'大林木','庚午':'路旁土','辛未':'路旁土',
    '壬申':'剑锋金','癸酉':'剑锋金','甲戌':'山头火','乙亥':'山头火',
    '丙子':'涧下水','丁丑':'涧下水','戊寅':'城头土','己卯':'城头土',
    '庚辰':'白腊金','辛巳':'白腊金','壬午':'杨柳木','癸未':'杨柳木',
    '甲申':'泉中水','乙酉':'泉中水','丙戌':'屋上土','丁亥':'屋上土',
    '戊子':'霹雳火','己丑':'霹雳火','庚寅':'松柏木','辛卯':'松柏木',
    '壬辰':'长流水','癸巳':'长流水','甲午':'砂石金','乙未':'砂石金',
    '丙申':'山下火','丁酉':'山下火','戊戌':'平地木','己亥':'平地木',
    '庚子':'壁上土','辛丑':'壁上土','壬寅':'金箔金','癸卯':'金箔金',
    '甲辰':'覆灯火','乙巳':'覆灯火','丙午':'天河水','丁未':'天河水',
    '戊申':'大驿土','己酉':'大驿土','庚戌':'钗钏金','辛亥':'钗钏金',
    '壬子':'桑柘木','癸丑':'桑柘木','甲寅':'大溪水','乙卯':'大溪水',
    '丙辰':'沙中土','丁巳':'沙中土','戊午':'天上火','己未':'天上火',
    '庚申':'石榴木','辛酉':'石榴木','壬戌':'大海水','癸亥':'大海水',
}


# ─────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────

def get_shichen_zhi(hour: int, minute: int) -> str:
    """根据真太阳时小时/分钟返回时支。"""
    for start, end, zhi in SHICHEN:
        if start == 23:                          # 子时跨午夜
            if hour >= 23 or hour < 1:
                return zhi
        else:
            if start <= hour < end:
                return zhi
    return '子'


def get_time_gan(day_gan: str, time_zhi: str) -> str:
    """五鼠遁口诀：由日干和时支推算时干。"""
    start = WUSHU_DUN.get(day_gan, '甲')
    start_idx = GAN.index(start)
    zhi_idx   = ZHI.index(time_zhi)
    return GAN[(start_idx + zhi_idx) % 10]


def get_ten_god(day_gan: str, gan: str) -> str:
    """返回某天干相对日干的十神（简称）。"""
    return TEN_GODS.get(day_gan, {}).get(gan, '')


def build_pillar(idx: int, name: str, gan: str, zhi: str, day_gan: str) -> dict:
    """构建单柱的完整信息字典。"""
    cangygan = ZHI_CANGYGAN.get(zhi, [])
    return {
        'index':    idx,
        'name':     name,
        'gan':      gan,
        'zhi':      zhi,
        'ganzhi':   gan + zhi,
        'gan_wuxing':  GAN_WUXING.get(gan, ''),
        'zhi_wuxing':  ZHI_WUXING.get(zhi, ''),
        'gan_shishen': get_ten_god(day_gan, gan) if idx != 2 else '日主',
        'zhi_shishen': get_ten_god(day_gan, cangygan[0]) if cangygan else '',
        'cangygan':    cangygan,
        'cangygan_details': [
            {'gan': g, 'wuxing': GAN_WUXING.get(g, ''), 'shishen': get_ten_god(day_gan, g)}
            for g in cangygan
        ],
        'nayin':    NAYIN.get(gan + zhi, ''),
        'yinyang':  '阳' if GAN.index(gan) % 2 == 0 else '阴',
    }


# ─────────────────────────────────────────────────────────────────
# 核心排盘
# ─────────────────────────────────────────────────────────────────

def calculate_yuanju(birth_info: dict) -> dict:
    """
    计算原局排盘。

    birth_info 必须包含真太阳时校准后的时间：
      year, month, day, hour, minute, gender, city
    """
    if not HAS_LUNAR:
        return {'success': False, 'error': 'vendor/lunar_python 未找到'}

    try:
        year   = birth_info['year']
        month  = birth_info['month']
        day    = birth_info['day']
        hour   = birth_info['hour']
        minute = birth_info['minute']
        gender = birth_info.get('gender', 'male')
        city   = birth_info.get('city', '')

        # ── 1. 通过 lunar_python 获取四柱基础干支 ──────────────────
        solar     = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar     = solar.getLunar()
        eight_char = lunar.getEightChar()

        year_gz  = eight_char.getYear()   # 如 '乙亥'
        month_gz = eight_char.getMonth()  # 月干正确，月支可能错
        day_gz   = eight_char.getDay()
        # 时柱不用 lunar_python 的，自己算（更准确）

        year_gan,  year_zhi  = year_gz[0],  year_gz[1]
        month_gan, _         = month_gz[0], month_gz[1]
        day_gan,   day_zhi   = day_gz[0],   day_gz[1]

        # ── 2. 修正月支（用 jieqi.py 的12节逻辑）──────────────────
        jieqi_info       = get_jieqi_info(year, month, day)
        correct_month_zhi = jieqi_info['month_zhi']
        correct_month_gz  = month_gan + correct_month_zhi

        # ── 3. 计算时柱（五鼠遁 + 真太阳时时辰）──────────────────
        hour_zhi = get_shichen_zhi(hour, minute)
        hour_gan = get_time_gan(day_gan, hour_zhi)
        hour_gz  = hour_gan + hour_zhi

        # ── 4. 构建四柱 ────────────────────────────────────────────
        pillars = [
            build_pillar(0, '年柱', year_gan,  year_zhi,          day_gan),
            build_pillar(1, '月柱', month_gan, correct_month_zhi, day_gan),
            build_pillar(2, '日柱', day_gan,   day_zhi,           day_gan),
            build_pillar(3, '时柱', hour_gan,  hour_zhi,          day_gan),
        ]

        return {
            'success': True,
            'birth': {
                'solar_date':  f'{year}-{month:02d}-{day:02d}',
                'solar_time':  f'{hour:02d}:{minute:02d}',
                'lunar_date':  f'{lunar.getYear()}年{abs(lunar.getMonth())}月{lunar.getDay()}日',
                'gender':      gender,
                'city':        city,
                'solar_time_applied': birth_info.get('solar_time_applied', False),
            },
            'ganzhi': {
                'year':  year_gz,
                'month': correct_month_gz,
                'day':   day_gz,
                'hour':  hour_gz,
            },
            'pillars':    pillars,
            'day_gan':    day_gan,
            'jieqi_info': jieqi_info,
            'generated_at': datetime.now().isoformat(),
        }

    except Exception as e:
        return {'success': False, 'error': f'排盘失败: {e}'}


# ─────────────────────────────────────────────────────────────────
# 命令行入口
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='八字原局排盘')
    parser.add_argument('--year',   type=int, required=True)
    parser.add_argument('--month',  type=int, required=True)
    parser.add_argument('--day',    type=int, required=True)
    parser.add_argument('--hour',   type=int, required=True)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--gender', type=str, default='male')
    parser.add_argument('--city',   type=str, default='')
    parser.add_argument('--solar-time-applied', action='store_true')
    args = parser.parse_args()

    result = calculate_yuanju({
        'year': args.year, 'month': args.month, 'day': args.day,
        'hour': args.hour, 'minute': args.minute,
        'gender': args.gender, 'city': args.city,
        'solar_time_applied': args.solar_time_applied,
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
