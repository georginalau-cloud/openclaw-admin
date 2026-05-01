#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[08] src/bazi_chart_month.py - 标准盘 + 流年 + 流月叠加
调用层级：被 bin/bazi 调用（monthly/daily 模式）
依赖：src/bazi_chart_year.py [07]

职责：
  接收 bazi_chart_year 的输出（流年盘），叠加指定流月干支，
  计算流月与原局/大运/流年的刑冲合关系，输出完整的"流月盘"。

  月运分析直接调用本文件的输出，lib/daily_fortune 按月粒度分析时也用这个。

输出结构：
  {
    "success": true,
    "base_chart":   原始标准盘
    "liuyear":      流年信息（含流月列表）
    "liuyue":       本月干支详情 + 与原局/大运/流年的刑冲合
    "context":      运势层级摘要（大运 + 流年 + 流月）
    "interactions": 流月与各层的刑冲合汇总
  }

调用方式（命令行）：
  python3 src/bazi_chart_month.py --year 1995 --month 9 --day 4 \
    --hour 21 --minute 44 --gender male --city 江阴 \
    --liuyear 2026 --liuyue-month 4

调用方式（Python）：
  from bazi_chart_month import build_month_chart
  month_chart = build_month_chart(year_chart, liuyue_month=4)
  # 或直接传 ganzhi：
  month_chart = build_month_chart(year_chart, liuyue_gz='丙辰')
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional

_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_SKILL_DIR, 'vendor'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bazi_chart import build_bazi_chart
from bazi_chart_year import (
    build_year_chart,
    _ganzhi_detail, _ten_god, _calc_zhi_interactions, _calc_gan_interactions,
    _summarize_interactions, _year_to_ganzhi,
    GAN_WUXING, ZHI_WUXING, ZHI_CANGYGAN, TEN_GODS,
    CHONG, HE6, XING, SANHE, GAN_HE, GAN_CHONG,
)

# 流月月支顺序（寅月=农历正月=1月起运）
_MONTH_ZHI_ORDER = ['寅','卯','辰','巳','午','未','申','酉','戌','亥','子','丑']

# 五虎遁：年干 → 寅月天干起点
_WUHU_DUN = {
    '甲': '丙', '己': '丙',
    '乙': '戊', '庚': '戊',
    '丙': '庚', '辛': '庚',
    '丁': '壬', '壬': '壬',
    '戊': '甲', '癸': '甲',
}
_GAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
_ZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']


def _month_index_to_gz(liuyear_gz: str, month_index: int) -> str:
    """
    根据流年天干和月序（1=寅月/农历正月 … 12=丑月）推算流月干支。
    month_index: 1-12，对应寅卯辰巳午未申酉戌亥子丑
    """
    year_gan = liuyear_gz[0] if liuyear_gz else '甲'
    start_gan = _WUHU_DUN.get(year_gan, '丙')
    start_idx = _GAN.index(start_gan)
    # 月序从1开始，寅月=index 0
    gan_idx = (start_idx + (month_index - 1)) % 10
    zhi = _MONTH_ZHI_ORDER[month_index - 1]
    return _GAN[gan_idx] + zhi


def _solar_month_to_month_index(solar_month: int) -> int:
    """
    将公历月份粗略转换为农历月序（寅月=1）。
    注意：这是近似值，精确月支需用 jieqi.py。
    公历2月≈寅月(1), 3月≈卯月(2), ..., 1月≈丑月(12)
    """
    # 公历月 2→1, 3→2, ..., 12→11, 1→12
    return ((solar_month - 2) % 12) + 1


# ─────────────────────────────────────────────────────────────────
# 核心函数
# ─────────────────────────────────────────────────────────────────

def build_month_chart(year_chart: dict, liuyue_month: int = None, liuyue_gz: str = None) -> dict:
    """
    在流年盘基础上叠加流月，生成流月盘。

    参数：
      year_chart:   bazi_chart_year.build_year_chart() 的完整输出
      liuyue_month: 农历月序（1=寅月, 2=卯月, ..., 12=丑月）
                    与 liuyue_gz 二选一，优先用 liuyue_gz
      liuyue_gz:    直接指定流月干支（如 '丙辰'），优先级高于 liuyue_month

    返回：
      包含原盘 + 流年 + 流月叠加信息的完整流月盘
    """
    if not year_chart.get('success'):
        return {'success': False, 'error': '流年盘无效'}

    base_chart  = year_chart.get('base_chart', {})
    liuyear_info = year_chart.get('liuyear', {})
    liuyear_gz  = liuyear_info.get('ganzhi', '')
    liuyear     = liuyear_info.get('year', datetime.now().year)
    day_gan     = base_chart.get('day_gan', '')
    pillars     = base_chart.get('pillars', [])
    dayun_gz    = year_chart.get('dayun', {}).get('ganzhi', '')

    # ── 1. 确定流月干支 ────────────────────────────────────────────
    if liuyue_gz and len(liuyue_gz) >= 2:
        # 直接使用传入的干支
        month_gz = liuyue_gz
        # 反推月序
        zhi = liuyue_gz[1]
        month_index = (_MONTH_ZHI_ORDER.index(zhi) + 1) if zhi in _MONTH_ZHI_ORDER else 1
    elif liuyue_month:
        month_index = liuyue_month
        # 先尝试从 year_chart 的 liu_yue 列表中找
        liu_yue = liuyear_info.get('liu_yue', [])
        month_gz = ''
        for ly in liu_yue:
            if ly.get('month_index') == month_index:
                month_gz = ly.get('ganzhi', '')
                break
        # 找不到则用五虎遁推算
        if not month_gz:
            month_gz = _month_index_to_gz(liuyear_gz, month_index)
    else:
        # 默认当前月
        month_index = _solar_month_to_month_index(datetime.now().month)
        liu_yue = liuyear_info.get('liu_yue', [])
        month_gz = ''
        for ly in liu_yue:
            if ly.get('month_index') == month_index:
                month_gz = ly.get('ganzhi', '')
                break
        if not month_gz:
            month_gz = _month_index_to_gz(liuyear_gz, month_index)

    month_gan = month_gz[0] if len(month_gz) >= 2 else ''
    month_zhi = month_gz[1] if len(month_gz) >= 2 else ''

    # 从 liu_yue 列表中找到完整信息（含空亡）
    liu_yue = liuyear_info.get('liu_yue', [])
    month_detail_from_chart = None
    for ly in liu_yue:
        if ly.get('ganzhi') == month_gz or ly.get('month_index') == month_index:
            month_detail_from_chart = ly
            break

    xun_kong = month_detail_from_chart.get('xun_kong', '') if month_detail_from_chart else ''

    # ── 2. 收集所有地支（原局 + 大运 + 流年）用于刑冲合计算 ────────
    yuanju_zhis = {p['zhi'] for p in pillars if 'zhi' in p}
    yuanju_gans = {p['gan'] for p in pillars if 'gan' in p}

    dayun_zhi = dayun_gz[1] if len(dayun_gz) >= 2 else ''
    dayun_gan = dayun_gz[0] if len(dayun_gz) >= 2 else ''
    liuyear_zhi = liuyear_gz[1] if len(liuyear_gz) >= 2 else ''
    liuyear_gan = liuyear_gz[0] if len(liuyear_gz) >= 2 else ''

    base_zhis = yuanju_zhis | ({dayun_zhi} if dayun_zhi else set()) | ({liuyear_zhi} if liuyear_zhi else set())
    base_gans = yuanju_gans | ({dayun_gan} if dayun_gan else set()) | ({liuyear_gan} if liuyear_gan else set())

    # ── 3. 计算流月与各层的刑冲合 ─────────────────────────────────
    zhi_interactions = _calc_zhi_interactions(month_zhi, base_zhis)
    gan_interactions = _calc_gan_interactions(month_gan, base_gans)

    # 标注来源
    pillar_names = {p['zhi']: p['name'] for p in pillars}
    pillar_names[dayun_zhi]   = '大运'
    pillar_names[liuyear_zhi] = '流年'
    interaction_detail = []
    for item in zhi_interactions:
        source = pillar_names.get(item.get('zhi_b', ''), '未知')
        interaction_detail.append({**item, 'source': source})

    # ── 4. 月份标注（中文月名）────────────────────────────────────
    month_cn_map = {1:'正月',2:'二月',3:'三月',4:'四月',5:'五月',6:'六月',
                    7:'七月',8:'八月',9:'九月',10:'十月',11:'十一月',12:'十二月'}

    # ── 5. 组装流月盘 ──────────────────────────────────────────────
    month_chart = {
        'success': True,
        'chart_type': 'month',

        # 原始标准盘
        'base_chart': base_chart,

        # 流年信息（不含 liu_yue 以减少冗余，保留关键字段）
        'liuyear': {
            'year':        liuyear,
            'ganzhi':      liuyear_gz,
            'gan_shishen': _ten_god(day_gan, liuyear_gz[0]) if liuyear_gz else '',
            'zhi_shishen': _ten_god(day_gan, ZHI_CANGYGAN.get(liuyear_gz[1] if len(liuyear_gz)>1 else '', [''])[0]),
        },

        # 当前大运摘要
        'dayun': year_chart.get('dayun', {}),

        # 流月信息
        'liuyue': {
            'month_index': month_index,
            'month_cn':    month_cn_map.get(month_index, ''),
            'ganzhi':      month_gz,
            'gan':         month_gan,
            'zhi':         month_zhi,
            'gan_wuxing':  GAN_WUXING.get(month_gan, ''),
            'zhi_wuxing':  ZHI_WUXING.get(month_zhi, ''),
            'gan_shishen': _ten_god(day_gan, month_gan),
            'zhi_shishen': _ten_god(day_gan, ZHI_CANGYGAN.get(month_zhi, [''])[0]),
            'cangygan':    ZHI_CANGYGAN.get(month_zhi, []),
            'cangygan_shishen': [
                {'gan': g, 'wuxing': GAN_WUXING.get(g,''), 'shishen': _ten_god(day_gan, g)}
                for g in ZHI_CANGYGAN.get(month_zhi, [])
            ],
            'xun_kong':    xun_kong,
        },

        # 运势层级上下文
        'context': {
            'layer_desc': f'{dayun_gz}大运 × {liuyear_gz}流年 × {month_gz}流月（{liuyear}年{month_cn_map.get(month_index,"")}）',
            'dayun_gz':   dayun_gz,
            'liuyear_gz': liuyear_gz,
            'liuyue_gz':  month_gz,
            'liuyear':    liuyear,
            'month_index': month_index,
        },

        # 刑冲合汇总
        'interactions': {
            'zhi': interaction_detail,
            'gan': gan_interactions,
            'summary': _summarize_interactions(zhi_interactions + gan_interactions),
        },

        'generated_at': datetime.now().isoformat(),
    }

    return month_chart


# ─────────────────────────────────────────────────────────────────
# 命令行入口
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='八字流月盘')
    parser.add_argument('--year',         type=int, required=True)
    parser.add_argument('--month',        type=int, required=True)
    parser.add_argument('--day',          type=int, required=True)
    parser.add_argument('--hour',         type=int, required=True)
    parser.add_argument('--minute',       type=int, default=0)
    parser.add_argument('--gender',       type=str, default='male')
    parser.add_argument('--city',         type=str, default='')
    parser.add_argument('--liuyear',      type=int, default=None, help='流年（公历年份），默认今年')
    parser.add_argument('--liuyue-month', type=int, default=None, help='流月月序（1=寅月…12=丑月）')
    parser.add_argument('--liuyue-gz',    type=str, default=None, help='流月干支（如 丙辰），优先级高于 --liuyue-month')
    args = parser.parse_args()

    liuyear = args.liuyear or datetime.now().year

    base_chart = build_bazi_chart(
        year=args.year, month=args.month, day=args.day,
        hour=args.hour, minute=args.minute,
        gender=args.gender, city=args.city,
        current_year=liuyear,
    )
    year_chart = build_year_chart(base_chart, liuyear=liuyear)
    result = build_month_chart(
        year_chart,
        liuyue_month=args.liuyue_month,
        liuyue_gz=args.liuyue_gz,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
