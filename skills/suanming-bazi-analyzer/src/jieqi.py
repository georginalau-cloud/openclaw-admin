#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[02] src/jieqi.py - 节气查询模块
调用层级：被 src/yuanju.py 和 src/dayun.py 调用
依赖：vendor/lunar_python

职责：
- 根据公历日期查询前后节气（12节，不是24节气）
- 根据节气确定农历月支
关键：
  12节（决定月支）：立春、惊蛰、清明、立夏、芒种、小暑、立秋、白露、寒露、立冬、大雪、冬至
  12气（不决定月支）：雨水、春分、谷雨、小满、夏至、大暑、处暑、秋分、霜降、小雪、冬至、大寒

  getPrevJie/getNextJie  ← 只返回12节（正确）
  getPrevJieQi/getNextJieQi ← 返回24节气（错误，会混入气）
"""

import os
import sys

# 从 vendor 导入 lunar_python
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_SKILL_DIR, 'vendor'))

try:
    from lunar_python import Solar, Lunar
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False


# 12节对应的月支
JIEQI_TO_MONTH_ZHI = {
    '立春': '寅',   # 正月
    '惊蛰': '卯',   # 二月
    '清明': '辰',   # 三月
    '立夏': '巳',   # 四月
    '芒种': '午',   # 五月
    '小暑': '未',   # 六月
    '立秋': '申',   # 七月
    '白露': '酉',   # 八月
    '寒露': '戌',   # 九月
    '立冬': '亥',   # 十月
    '大雪': '子',   # 十一月
    '小寒': '丑',   # 十二月
}


def get_month_zhi_by_solar_date(year: int, month: int, day: int) -> str:
    """
    根据公历日期获取农历月支。

    原理：
      找到当前日期之前最近的一个节（12节之一），
      该节对应的月支就是当前的月支。

    例：1995-09-04
      → 前一个节：立秋（8月8日）→ 月支为申
      → 下一个节：白露（9月8日）
      → 当前在立秋之后、白露之前 → 月支 = 申
    """
    if not HAS_LUNAR:
        return '卯'

    try:
        solar = Solar.fromYmdHms(year, month, day, 12, 0, 0)
        lunar = solar.getLunar()

        # 获取前一个节（12节之一）
        prev_jie = lunar.getPrevJie()
        if prev_jie:
            jie_name = prev_jie.getName()
            if jie_name in JIEQI_TO_MONTH_ZHI:
                return JIEQI_TO_MONTH_ZHI[jie_name]

        # fallback：根据农历月份推导
        lunar_month = abs(lunar.getMonth())
        zhi_list = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        month_zhi_idx = (lunar_month - 1 + 2) % 12  # 农历正月 → 寅
        return zhi_list[month_zhi_idx]

    except Exception as e:
        print(f"节气查询失败: {e}", file=sys.stderr)
        return '卯'


def get_jieqi_info(year: int, month: int, day: int) -> dict:
    """
    获取当前日期的节气信息（前后各一个节）。

    返回：
      {
        'prev_jie': {'name': '立秋', 'date': '1995-08-08', 'time': '07:46:00'},
        'next_jie': {'name': '白露', 'date': '1995-09-08', 'time': '10:24:00'},
        'month_zhi': '申'
      }
    """
    if not HAS_LUNAR:
        return {'prev_jie': None, 'next_jie': None, 'month_zhi': '卯'}

    try:
        solar = Solar.fromYmdHms(year, month, day, 12, 0, 0)
        lunar = solar.getLunar()

        prev_jie_obj = lunar.getPrevJie()
        next_jie_obj = lunar.getNextJie()

        prev_jie = None
        next_jie = None

        if prev_jie_obj:
            s = prev_jie_obj.getSolar()
            prev_jie = {
                'name': prev_jie_obj.getName(),
                'date': f'{s.getYear()}-{s.getMonth():02d}-{s.getDay():02d}',
                'time': f'{s.getHour():02d}:{s.getMinute():02d}:{s.getSecond():02d}'
            }

        if next_jie_obj:
            s = next_jie_obj.getSolar()
            next_jie = {
                'name': next_jie_obj.getName(),
                'date': f'{s.getYear()}-{s.getMonth():02d}-{s.getDay():02d}',
                'time': f'{s.getHour():02d}:{s.getMinute():02d}:{s.getSecond():02d}'
            }

        month_zhi = get_month_zhi_by_solar_date(year, month, day)

        return {
            'prev_jie': prev_jie,
            'next_jie': next_jie,
            'month_zhi': month_zhi
        }

    except Exception as e:
        print(f"节气信息获取失败: {e}", file=sys.stderr)
        return {'prev_jie': None, 'next_jie': None, 'month_zhi': '卯'}


# ─────────────────────────────────────────────────────────────────
# 测试
# ─────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    print("【测试】1995年09月04日的节气和月支")
    info = get_jieqi_info(1995, 9, 4)
    print(f"  前一个节: {info['prev_jie']}")
    print(f"  下一个节: {info['next_jie']}")
    print(f"  月支: {info['month_zhi']}")
    print(f"  期望: 前节=立秋, 下节=白露, 月支=申")
