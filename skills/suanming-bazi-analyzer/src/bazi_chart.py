#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[06] src/bazi_chart.py - 标准盘整合输出
调用层级：被 bin/bazi 调用，是排盘层的最终出口
依赖：src/cities_longitude.py [01]、src/yuanju.py [04]、src/dayun.py [05]

职责：
  接收 yuanju + dayun 的输出，整合成一份完整的标准盘 JSON。
  这是排盘阶段的最终产物，供 lib/ 分析层和 bin/bazi 入口使用。

输出结构：
  {
    "success": true,
    "meta":        出生基本信息（含真太阳时校准说明）
    "pillars":     四柱详情（年月日时，含十神/藏干/纳音/五行）
    "wuxing":      五行统计（各五行力量分布）
    "qiyun":       起运信息
    "dayun_list":  8个大运
    "current":     当前大运 + 流年 + 流月摘要
  }

调用方式：
  python3 src/bazi_chart.py --year 1995 --month 9 --day 4 \\
    --hour 21 --minute 44 --gender male --city 江阴
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict

# vendor 路径
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_SKILL_DIR, 'vendor'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cities_longitude import calculate_solar_time, get_longitude
from yuanju import calculate_yuanju
from dayun import calculate_dayun


# ─────────────────────────────────────────────────────────────────
# 五行统计
# ─────────────────────────────────────────────────────────────────

# 各位置的权重（天干 vs 地支 vs 藏干主气/中气/余气）
_WEIGHTS = {
    'gan':        5,   # 天干
    'zhi_main':   4,   # 地支主气（藏干第一位）
    'zhi_mid':    2,   # 地支中气（藏干第二位）
    'zhi_minor':  1,   # 地支余气（藏干第三位）
}

GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}


def _calc_wuxing(pillars: list) -> dict:
    """
    计算命局五行力量分布。
    天干权重5，地支藏干主气4、中气2、余气1。
    月支额外加倍（月令得令）。
    """
    scores = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}

    for p in pillars:
        is_month = (p['index'] == 1)
        multiplier = 2 if is_month else 1

        # 天干
        wx = GAN_WUXING.get(p['gan'], '')
        if wx:
            scores[wx] += _WEIGHTS['gan'] * multiplier

        # 地支藏干
        cangygan = p.get('cangygan', [])
        weight_keys = ['zhi_main', 'zhi_mid', 'zhi_minor']
        for i, g in enumerate(cangygan):
            wx = GAN_WUXING.get(g, '')
            if wx and i < len(weight_keys):
                scores[wx] += _WEIGHTS[weight_keys[i]] * multiplier

    total = sum(scores.values()) or 1
    percentages = {k: round(v / total * 100, 1) for k, v in scores.items()}

    # 排序（从强到弱）
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return {
        'scores':      scores,
        'percentages': percentages,
        'ranked':      [{'wuxing': k, 'score': v, 'pct': percentages[k]} for k, v in ranked],
        'strongest':   ranked[0][0],
        'weakest':     ranked[-1][0],
    }


# ─────────────────────────────────────────────────────────────────
# 核心整合
# ─────────────────────────────────────────────────────────────────

def build_bazi_chart(
    year: int, month: int, day: int,
    hour: int, minute: int,
    gender: str,
    city: str = '',
    current_year: int = None,
) -> dict:
    """
    完整排盘入口。

    流程：
      1. 真太阳时校准（cities_longitude）
      2. 原局排盘（yuanju）
      3. 大运展开（dayun）
      4. 整合成标准盘

    参数均为用户输入的原始北京时间。
    """
    cur_year = current_year or datetime.now().year

    # ── 1. 真太阳时校准 ────────────────────────────────────────────
    solar_correction = None
    corrected_hour, corrected_minute = hour, minute

    if city:
        longitude = get_longitude(city)
        if longitude is not None:
            try:
                corrected_hour, corrected_minute = calculate_solar_time(
                    hour=hour,
                    minute=minute,
                    second=0,
                    longitude=longitude,
                    month=month,
                    day=day,
                )
                offset_min = (corrected_hour * 60 + corrected_minute) - (hour * 60 + minute)
                solar_correction = {
                    'city':       city,
                    'longitude':  longitude,
                    'original':   f'{hour:02d}:{minute:02d}',
                    'corrected':  f'{corrected_hour:02d}:{corrected_minute:02d}',
                    'offset_min': offset_min,
                    'applied':    True,
                }
            except Exception as e:
                solar_correction = {
                    'city':    city,
                    'applied': False,
                    'reason':  f'真太阳时计算失败：{e}，使用原始时间',
                }
        else:
            solar_correction = {
                'city':    city,
                'applied': False,
                'reason':  f'城市 "{city}" 未在经度库中找到，使用原始时间',
            }

    # ── 2. 原局排盘 ────────────────────────────────────────────────
    yuanju_result = calculate_yuanju({
        'year': year, 'month': month, 'day': day,
        'hour': corrected_hour, 'minute': corrected_minute,
        'gender': gender, 'city': city,
        'solar_time_applied': solar_correction is not None and solar_correction.get('applied', False),
    })

    if not yuanju_result.get('success'):
        return {'success': False, 'error': yuanju_result.get('error', '原局排盘失败')}

    day_gan = yuanju_result['day_gan']
    pillars = yuanju_result['pillars']

    # ── 3. 大运展开 ────────────────────────────────────────────────
    dayun_result = calculate_dayun({
        'year': year, 'month': month, 'day': day,
        'hour': corrected_hour, 'minute': corrected_minute,
        'gender': gender, 'day_gan': day_gan,
    }, current_year=cur_year)

    if not dayun_result.get('success'):
        return {'success': False, 'error': dayun_result.get('error', '大运计算失败')}

    # ── 4. 五行统计 ────────────────────────────────────────────────
    wuxing = _calc_wuxing(pillars)

    # ── 5. 当前摘要 ────────────────────────────────────────────────
    current_dayun   = dayun_result.get('current_dayun')
    current_liuyear = dayun_result.get('current_liuyear')

    current_summary = None
    if current_dayun:
        current_summary = {
            'dayun': {
                'ganzhi':     current_dayun['ganzhi'],
                'start_year': current_dayun['start_year'],
                'end_year':   current_dayun['end_year'],
                'start_age':  current_dayun['start_age'],
                'end_age':    current_dayun['end_age'],
                'gan_shishen': current_dayun.get('gan_shishen', ''),
                'zhi_shishen': current_dayun.get('zhi_shishen', ''),
                'xun_kong':   current_dayun.get('xun_kong', ''),
            },
        }
        if current_liuyear:
            current_summary['liuyear'] = {
                'year':        current_liuyear['year'],
                'age':         current_liuyear['age'],
                'ganzhi':      current_liuyear['ganzhi'],
                'gan_shishen': current_liuyear.get('gan_shishen', ''),
                'zhi_shishen': current_liuyear.get('zhi_shishen', ''),
                'xun_kong':    current_liuyear.get('xun_kong', ''),
                'liu_yue':     current_liuyear.get('liu_yue', []),
            }

    # ── 6. 组装标准盘 ──────────────────────────────────────────────
    chart = {
        'success': True,

        # 基本信息
        'meta': {
            'solar_date':       f'{year}-{month:02d}-{day:02d}',
            'solar_time_input': f'{hour:02d}:{minute:02d}',
            'solar_time_used':  f'{corrected_hour:02d}:{corrected_minute:02d}',
            'lunar_date':       yuanju_result['birth']['lunar_date'],
            'gender':           gender,
            'city':             city,
            'solar_correction': solar_correction,
            'current_year':     cur_year,
        },

        # 四柱
        'ganzhi':  yuanju_result['ganzhi'],
        'pillars': pillars,
        'day_gan': day_gan,

        # 节气
        'jieqi': yuanju_result.get('jieqi_info', {}),

        # 五行
        'wuxing': wuxing,

        # 大运
        'qiyun':      dayun_result['qiyun'],
        'dayun_list': dayun_result['dayun_list'],

        # 当前运势摘要
        'current': current_summary,

        'generated_at': datetime.now().isoformat(),
    }

    return chart


# ─────────────────────────────────────────────────────────────────
# 命令行入口
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='八字标准盘整合输出')
    parser.add_argument('--year',         type=int, required=True)
    parser.add_argument('--month',        type=int, required=True)
    parser.add_argument('--day',          type=int, required=True)
    parser.add_argument('--hour',         type=int, required=True)
    parser.add_argument('--minute',       type=int, default=0)
    parser.add_argument('--gender',       type=str, default='male')
    parser.add_argument('--city',         type=str, default='')
    parser.add_argument('--current-year', type=int, default=None)
    args = parser.parse_args()

    chart = build_bazi_chart(
        year=args.year, month=args.month, day=args.day,
        hour=args.hour, minute=args.minute,
        gender=args.gender, city=args.city,
        current_year=args.current_year,
    )
    print(json.dumps(chart, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
