#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[22] lib/daily_fortune.py - 日运分析模块
调用层级：被 bin/bazi（daily 模式）调用
依赖：vendor/lunar_python

功能：
  1. 计算当日干支（年/月/日/时）
  2. 获取黄历宜忌、建除十二值星、吉神方位
  3. 分析当日干支与命局（原局 + 大运 + 流年 + 流月）的关系
  4. 生成日运 prompt 供 MiniMax 润色

层级：原局 → 大运 → 流年 → 流月 → 流日（完整五层）
"""

import os
import sys
from datetime import date
from typing import Dict

_LIB_DIR   = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_LIB_DIR)
sys.path.insert(0, os.path.join(_SKILL_DIR, 'vendor'))
sys.path.insert(0, os.path.join(_SKILL_DIR, 'src'))

try:
    from lunar_python import Solar
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False

# ─────────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────────

ZHI_CANGYGAN = {
    '子':['癸'],'丑':['己','癸','辛'],'寅':['甲','丙','戊'],
    '卯':['乙'],'辰':['戊','乙','癸'],'巳':['丙','戊','庚'],
    '午':['丁','己'],'未':['己','丁','乙'],'申':['庚','壬','戊'],
    '酉':['辛'],'戌':['戊','辛','丁'],'亥':['壬','甲'],
}
CHONG = {
    '子':'午','午':'子','丑':'未','未':'丑',
    '寅':'申','申':'寅','卯':'酉','酉':'卯',
    '辰':'戌','戌':'辰','巳':'亥','亥':'巳',
}
HE6 = {
    '子':'丑','丑':'子','寅':'亥','亥':'寅',
    '卯':'戌','戌':'卯','辰':'酉','酉':'辰',
    '巳':'申','申':'巳','午':'未','未':'午',
}
XING = {
    '子':'卯','卯':'子',
    '寅':'巳','巳':'申','申':'寅',
    '丑':'戌','戌':'未','未':'丑',
}
SANHE = [
    ({'申','子','辰'}, '水局'),
    ({'寅','午','戌'}, '火局'),
    ({'巳','酉','丑'}, '金局'),
    ({'亥','卯','未'}, '木局'),
]
DIRECTION_CN = {
    '艮':'东北','震':'正东','巽':'东南','离':'正南',
    '坤':'西南','兑':'正西','乾':'西北','坎':'正北','中':'中央',
}
LUCKY_COLORS = {
    '木':['绿色','青色'],'火':['红色','橙色','紫色'],
    '土':['黄色','棕色','米色'],'金':['白色','金色','银色'],
    '水':['黑色','深蓝色','灰色'],
}
SHISHEN_FULL = {
    '比':'比肩','劫':'劫财','食':'食神','伤':'伤官',
    '才':'偏财','财':'正财','杀':'七杀','官':'正官',
    '枭':'偏印','印':'正印','日主':'日主',
}


# ─────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────

def _get_interactions(zhi_a, zhi_set):
    notes = []
    for zhi_b in zhi_set:
        if zhi_b == zhi_a:
            continue
        if CHONG.get(zhi_a) == zhi_b:
            notes.append({'type':'冲','desc':f'{zhi_a}冲{zhi_b}','effect':'动荡变化，需防意外'})
        if HE6.get(zhi_a) == zhi_b:
            notes.append({'type':'合','desc':f'{zhi_a}合{zhi_b}','effect':'有助力，贵人相助'})
        if XING.get(zhi_a) == zhi_b:
            notes.append({'type':'刑','desc':f'{zhi_a}刑{zhi_b}','effect':'摩擦压力，需谨慎'})
    for members, ju_name in SANHE:
        if zhi_a in members and members.issubset(zhi_set | {zhi_a}):
            notes.append({'type':'三合','desc':f'三合{ju_name}','effect':'力量聚合，大有助益'})
            break
    return notes


def _score_day(day_gz, day_gan, all_zhis):
    from .ten_gods_analyzer import get_ten_god
    if not day_gz or len(day_gz) < 2:
        return {}
    gan, zhi = day_gz[0], day_gz[1]
    shishen_gan  = get_ten_god(day_gan, gan)
    cangygan     = ZHI_CANGYGAN.get(zhi, [])
    shishen_zhi  = get_ten_god(day_gan, cangygan[0]) if cangygan else ''
    interactions = _get_interactions(zhi, all_zhis)

    score = 0
    notes = []
    GOOD = {'印','枭','官','财','才','食'}
    BAD  = {'杀','劫','伤'}
    if shishen_gan in GOOD:
        score += 1
        notes.append(f'日干{gan}（{SHISHEN_FULL.get(shishen_gan,shishen_gan)}）对命局有利')
    elif shishen_gan in BAD:
        score -= 1
        notes.append(f'日干{gan}（{SHISHEN_FULL.get(shishen_gan,shishen_gan)}）需注意压力')

    for inter in interactions:
        if inter['type'] == '冲':
            score -= 2
            notes.append(f"{inter['desc']}，{inter['effect']}")
        elif inter['type'] == '合':
            score += 1
            notes.append(f"{inter['desc']}，{inter['effect']}")
        elif inter['type'] == '刑':
            score -= 1
            notes.append(f"{inter['desc']}，{inter['effect']}")
        elif inter['type'] == '三合':
            score += 2
            notes.append(f"{inter['desc']}，{inter['effect']}")

    rating = '吉' if score >= 2 else ('需防' if score < 0 else '平')
    return {
        'score': score, 'rating': rating,
        'shishen_gan': shishen_gan, 'shishen_zhi': shishen_zhi,
        'interactions': interactions, 'notes': notes,
    }


# ─────────────────────────────────────────────────────────────────
# 主分析器
# ─────────────────────────────────────────────────────────────────

class DailyFortune:
    """日运分析器，接收 bazi_chart 完整输出。"""

    def __init__(self, chart):
        self.chart   = chart
        self.day_gan = chart.get('day_gan', '')
        gender_raw   = chart.get('meta', {}).get('gender', 'male')
        self.gender  = 'male' if gender_raw.lower() in ('male','m','男') else 'female'
        pillars      = chart.get('pillars', [])
        self.yuanju_zhis = {p['zhi'] for p in pillars if 'zhi' in p}
        current          = chart.get('current', {})
        self.dayun_gz    = current.get('dayun', {}).get('ganzhi', '') if current else ''
        liuyear          = current.get('liuyear', {}) if current else {}
        self.year_gz     = liuyear.get('ganzhi', '') if liuyear else ''
        self.liu_yue     = liuyear.get('liu_yue', []) if liuyear else []

    def _get_day_data(self, target_date, hour=8):
        if not HAS_LUNAR:
            return {'error': 'vendor/lunar_python 未找到'}
        try:
            y, m, d = [int(x) for x in target_date.split('-')]
            solar   = Solar.fromYmdHms(y, m, d, hour, 0, 0)
            lunar   = solar.getLunar()
            pos     = {
                'xi':  f"{lunar.getDayPositionXi()}（{DIRECTION_CN.get(lunar.getDayPositionXi(),'')}）",
                'cai': f"{lunar.getDayPositionCai()}（{DIRECTION_CN.get(lunar.getDayPositionCai(),'')}）",
                'fu':  f"{lunar.getDayPositionFu()}（{DIRECTION_CN.get(lunar.getDayPositionFu(),'')}）",
            }
            return {
                'date':       target_date,
                'lunar_date': f"{lunar.getYearInChinese()}年{lunar.getMonthInChinese()}月{lunar.getDayInChinese()}",
                'ganzhi': {
                    'year':  lunar.getYearInGanZhi(),
                    'month': lunar.getMonthInGanZhi(),
                    'day':   lunar.getDayInGanZhi(),
                    'hour':  lunar.getTime().getGanZhi(),
                },
                'huangli': {
                    'yi':       lunar.getDayYi(),
                    'ji':       lunar.getDayJi(),
                    'zhi_xing': lunar.getZhiXing(),
                    'chong':    lunar.getDayChong(),
                    'sha':      lunar.getDaySha(),
                    'nayin':    lunar.getDayNaYin(),
                },
                'positions': pos,
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_month_gz(self, target_date):
        if not self.liu_yue:
            return ''
        try:
            month = int(target_date.split('-')[1])
            idx   = (month - 2) % 12
            if idx < len(self.liu_yue):
                return self.liu_yue[idx].get('ganzhi', '')
        except Exception:
            pass
        return ''

    def analyze(self, target_date=None, hour=8):
        """
        分析指定日期的日运。

        参数：
          target_date: 'YYYY-MM-DD'，默认今天
          hour: 时辰（0-23），默认早8点
        """
        if not target_date:
            target_date = date.today().strftime('%Y-%m-%d')

        day_data = self._get_day_data(target_date, hour)
        if 'error' in day_data:
            return {'success': False, 'error': day_data['error']}

        day_gz   = day_data['ganzhi']['day']
        month_gz = self._get_month_gz(target_date)

        # 所有层级地支集合
        all_zhis = set(self.yuanju_zhis)
        for gz in [self.dayun_gz, self.year_gz, month_gz]:
            if gz and len(gz) >= 2:
                all_zhis.add(gz[1])

        day_analysis  = _score_day(day_gz, self.day_gan, all_zhis)
        yong_shen     = (
            self.chart.get('yong_shen', {}).get('yong_shen', '')
            or self.chart.get('analysis', {}).get('format_analysis', {}).get('yong_shen', '')
        )
        ji_shen       = (
            self.chart.get('yong_shen', {}).get('ji_shen', [])
            or self.chart.get('analysis', {}).get('format_analysis', {}).get('ji_shen', [])
        )
        lucky_colors  = LUCKY_COLORS.get(yong_shen, [])
        lucky_dir     = day_data['positions'].get('xi', '')

        layers = []
        if self.dayun_gz: layers.append(f"{self.dayun_gz}大运")
        if self.year_gz:  layers.append(f"{self.year_gz}流年")
        if month_gz:      layers.append(f"{month_gz}流月")
        layers.append(f"{day_gz}流日")

        return {
            'success':      True,
            'date':         target_date,
            'day_data':     day_data,
            'month_gz':     month_gz,
            'day_analysis': day_analysis,
            'lucky': {
                'colors':    lucky_colors,
                'direction': lucky_dir,
                'cai_pos':   day_data['positions'].get('cai', ''),
                'fu_pos':    day_data['positions'].get('fu', ''),
            },
            'layer_desc':   ' → '.join(layers),
            'prompt_for_llm': self._build_prompt(
                target_date, day_data, day_analysis, month_gz, lucky_colors, lucky_dir
            ),
        }

    def _build_prompt(self, target_date, day_data, day_analysis, month_gz, lucky_colors, lucky_dir):
        meta    = self.chart.get('meta', {})
        gz      = self.chart.get('ganzhi', {})
        fmt     = self.chart.get('yong_shen', {})
        yong    = fmt.get('yong_shen', '') or self.chart.get('analysis', {}).get('format_analysis', {}).get('yong_shen', '')
        ji      = fmt.get('ji_shen', []) or self.chart.get('analysis', {}).get('format_analysis', {}).get('ji_shen', [])
        huangli = day_data.get('huangli', {})
        pos     = day_data.get('positions', {})
        gender_cn = '男' if meta.get('gender','').lower() in ('male','m','男') else '女'
        day_gz    = day_data['ganzhi']['day']
        rating    = day_analysis.get('rating', '平')
        notes     = day_analysis.get('notes', [])
        yi_str    = '、'.join(huangli.get('yi', [])[:5])
        ji_str    = '、'.join(huangli.get('ji', [])[:4])

        return f"""你是一位精通子平八字的命理师，请为以下用户写一份简洁有温度的日运分析。

## 用户命盘
- 四柱：年{gz.get('year','')} 月{gz.get('month','')} 日{gz.get('day','')} 时{gz.get('hour','')}（{gender_cn}命）
- 日主：{self.day_gan}  用神：{yong}  忌神：{'、'.join(ji)}
- 当前：{self.dayun_gz}大运 × {self.year_gz}流年{f' × {month_gz}流月' if month_gz else ''}

## 今日信息（{target_date}）
- 农历：{day_data.get('lunar_date','')}
- 今日干支：{day_gz}  建除：{huangli.get('zhi_xing','')}日  纳音：{huangli.get('nayin','')}
- 冲：{huangli.get('chong','')}  煞：{huangli.get('sha','')}方
- 黄历宜：{yi_str}
- 黄历忌：{ji_str}
- 喜神方位：{pos.get('xi','')}  财神方位：{pos.get('cai','')}  福神方位：{pos.get('fu','')}

## 命盘与今日干支的关系
今日综合评级：【{rating}】
{chr(10).join(f'- {n}' for n in notes) if notes else '- 今日干支与命局无明显刑冲，运势平稳'}

## 写作要求
请写一份300-500字的日运分析，包含：

1. **今日整体运势**：结合命盘和今日干支，说明今天的整体气场（2句话）

2. **重点提示**：今日最值得关注的一个命盘互动，用通俗语言解释对今天的影响

3. **黄历建议**：结合宜忌，给出1-2条今天适合/不适合做的事

4. **幸运提示**：幸运色 {('、'.join(lucky_colors)) if lucky_colors else ''}，幸运方位 {lucky_dir}

语气轻松亲切，像朋友发早安消息，结尾加一句鼓励的话。
"""