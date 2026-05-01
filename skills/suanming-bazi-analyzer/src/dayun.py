#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[05] src/dayun.py - 大运/流年/流月展开模块
调用层级：被 src/bazi_chart.py 调用
依赖：src/jieqi.py [02]

职责：
- 计算起运时间（精确到天，基于节气精确时刻）
- 生成 8 个大运序列
- 展开当前大运下的 10 个流年
- 展开当前流年下的 12 个流月
- 如追问则继续展开流日

核心算法（由 vendor/lunar_python 的 Yun 类实现）：
  顺逆排：阳年男/阴年女 → 顺排；阴年男/阳年女 → 逆排
  起运天数：出生到下一节（顺）或上一节（逆）的精确时间差
  换算：3天=1岁，1天=4个月，1时辰=10天

调用方式：
  python3 src/dayun.py --year 1995 --month 9 --day 4 --hour 21 --minute 44 --gender male
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
    from lunar_python import Solar
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False

# 同目录的 jieqi（用于流年月支判断）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jieqi import get_jieqi_info

# ─────────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────────

GAN_WUXING = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
}
ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水',
}
ZHI_CANGYGAN = {
    '子': ['癸'], '丑': ['己', '癸', '辛'], '寅': ['甲', '丙', '戊'],
    '卯': ['乙'], '辰': ['戊', '乙', '癸'], '巳': ['丙', '戊', '庚'],
    '午': ['丁', '己'], '未': ['己', '丁', '乙'], '申': ['庚', '壬', '戊'],
    '酉': ['辛'], '戌': ['戊', '辛', '丁'], '亥': ['壬', '甲'],
}
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


# ─────────────────────────────────────────────────────────────────
# 辅助
# ─────────────────────────────────────────────────────────────────

def _ten_god(day_gan: str, gan: str) -> str:
    return TEN_GODS.get(day_gan, {}).get(gan, '')


def _ganzhi_detail(gz: str, day_gan: str) -> dict:
    """给一个干支字符串生成完整的五行/十神/藏干信息。"""
    if not gz or len(gz) < 2:
        return {}
    gan, zhi = gz[0], gz[1]
    cangygan = ZHI_CANGYGAN.get(zhi, [])
    return {
        'ganzhi':      gz,
        'gan':         gan,
        'zhi':         zhi,
        'gan_wuxing':  GAN_WUXING.get(gan, ''),
        'zhi_wuxing':  ZHI_WUXING.get(zhi, ''),
        'gan_shishen': _ten_god(day_gan, gan),
        'zhi_shishen': _ten_god(day_gan, cangygan[0]) if cangygan else '',
        'cangygan':    cangygan,
        'cangygan_shishen': [
            {'gan': g, 'wuxing': GAN_WUXING.get(g, ''), 'shishen': _ten_god(day_gan, g)}
            for g in cangygan
        ],
        'xun_kong': '',  # 空亡，由调用方填入
    }


# ─────────────────────────────────────────────────────────────────
# 核心计算
# ─────────────────────────────────────────────────────────────────

def calculate_dayun(birth_info: dict, current_year: int = None) -> dict:
    """
    计算完整的大运/流年/流月信息。

    birth_info 必须包含真太阳时校准后的时间：
      year, month, day, hour, minute, gender ('male'/'female')
    还需要 day_gan（日干，从 yuanju 输出中取）。

    current_year: 用于标记当前大运和流年，默认取今年。
    """
    if not HAS_LUNAR:
        return {'success': False, 'error': 'vendor/lunar_python 未找到'}

    try:
        year   = birth_info['year']
        month  = birth_info['month']
        day    = birth_info['day']
        hour   = birth_info['hour']
        minute = birth_info['minute']
        gender_str = birth_info.get('gender', 'male')
        day_gan    = birth_info.get('day_gan', '')

        gender = 1 if gender_str.lower() in ('male', 'm', '男') else 0
        cur_year = current_year or datetime.now().year

        # ── 1. 构建 lunar 对象，获取 Yun ──────────────────────────
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        lunar = solar.getLunar()
        ec    = lunar.getEightChar()
        yun   = ec.getYun(gender)

        # ── 2. 起运信息 ────────────────────────────────────────────
        start_solar = yun.getStartSolar()
        qiyun = {
            'is_forward':    yun.isForward(),
            'direction':     '顺排' if yun.isForward() else '逆排',
            'start_year':    yun.getStartYear(),
            'start_month':   yun.getStartMonth(),
            'start_day':     yun.getStartDay(),
            'start_date':    start_solar.toYmd(),
            'description':   f"出生后 {yun.getStartYear()}年{yun.getStartMonth()}月{yun.getStartDay()}天 起运",
        }

        # ── 3. 大运列表（index 0 是命宫前，1-8 是真正的大运）──────
        all_dayuns = yun.getDaYun(9)   # 取 9 个，index 0 跳过
        dayun_list = []

        for da in all_dayuns[1:]:      # 跳过 index 0
            gz = da.getGanZhi()
            detail = _ganzhi_detail(gz, day_gan)
            detail['xun_kong'] = da.getXunKong()

            is_current = da.getStartYear() <= cur_year <= da.getEndYear()

            entry = {
                'index':      da.getIndex(),
                'ganzhi':     gz,
                'start_year': da.getStartYear(),
                'end_year':   da.getEndYear(),
                'start_age':  da.getStartAge(),
                'end_age':    da.getEndAge(),
                'is_current': is_current,
                **detail,
            }

            # ── 4. 当前大运展开流年 ────────────────────────────────
            if is_current:
                liu_nian_list = []
                for ln in da.getLiuNian(10):
                    ln_gz     = ln.getGanZhi()
                    ln_detail = _ganzhi_detail(ln_gz, day_gan)
                    ln_detail['xun_kong'] = ln.getXunKong()
                    is_cur_year = (ln.getYear() == cur_year)

                    ln_entry = {
                        'year':       ln.getYear(),
                        'age':        ln.getAge(),
                        'ganzhi':     ln_gz,
                        'is_current': is_cur_year,
                        **ln_detail,
                    }

                    # ── 5. 当前流年展开流月 ────────────────────────
                    if is_cur_year:
                        liu_yue_list = []
                        for ly in ln.getLiuYue():
                            ly_gz     = ly.getGanZhi()
                            ly_detail = _ganzhi_detail(ly_gz, day_gan)
                            ly_detail['xun_kong'] = ly.getXunKong()
                            liu_yue_list.append({
                                'month_index': ly.getIndex() + 1,
                                'month_cn':    ly.getMonthInChinese(),
                                'ganzhi':      ly_gz,
                                **ly_detail,
                            })
                        ln_entry['liu_yue'] = liu_yue_list

                    liu_nian_list.append(ln_entry)

                entry['liu_nian'] = liu_nian_list

            dayun_list.append(entry)

        # ── 6. 找出当前大运和流年的摘要 ───────────────────────────
        current_dayun  = next((d for d in dayun_list if d['is_current']), None)
        current_liuyear = None
        if current_dayun and 'liu_nian' in current_dayun:
            current_liuyear = next(
                (ln for ln in current_dayun['liu_nian'] if ln['is_current']), None
            )

        return {
            'success':         True,
            'qiyun':           qiyun,
            'dayun_list':      dayun_list,
            'current_dayun':   current_dayun,
            'current_liuyear': current_liuyear,
            'current_year':    cur_year,
            'generated_at':    datetime.now().isoformat(),
        }

    except Exception as e:
        import traceback
        return {'success': False, 'error': str(e), 'traceback': traceback.format_exc()}


# ─────────────────────────────────────────────────────────────────
# 命令行入口
# ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='八字大运排盘')
    parser.add_argument('--year',    type=int, required=True)
    parser.add_argument('--month',   type=int, required=True)
    parser.add_argument('--day',     type=int, required=True)
    parser.add_argument('--hour',    type=int, required=True)
    parser.add_argument('--minute',  type=int, default=0)
    parser.add_argument('--gender',  type=str, default='male')
    parser.add_argument('--day-gan', type=str, default='')
    parser.add_argument('--current-year', type=int, default=None)
    args = parser.parse_args()

    result = calculate_dayun({
        'year': args.year, 'month': args.month, 'day': args.day,
        'hour': args.hour, 'minute': args.minute,
        'gender': args.gender, 'day_gan': args.day_gan,
    }, current_year=args.current_year)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
