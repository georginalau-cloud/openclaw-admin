#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[12] lib/yongshen_analyzer.py - 用神取用引擎（三法合一）
调用层级：被 lib/format_analyzer.py [13] 调用
依赖：lib/ganzhi_calculator.py [03]

取用优先级：
  1. 调候用神（穷通宝鉴，日干×月支，解决寒暖燥湿）
  2. 病药用神（格局分析，有病找药）
  3. 通关用神（两方对峙，找通关五行）

参考文献：
  《穷通宝鉴》（余春台）- 调候用神
  《子平真诠》（沈孝瞻）- 格局用神
  《滴天髓》（刘基）- 病药通关
"""

import os
import sys
from typing import Dict, List, Optional, Tuple

_LIB_DIR   = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_LIB_DIR)
sys.path.insert(0, _SKILL_DIR)

# ─────────────────────────────────────────────────────────────────
# 基础常量
# ─────────────────────────────────────────────────────────────────

STEM_ELEMENTS = {
    '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
    '己':'土','庚':'金','辛':'金','壬':'水','癸':'水',
}
BRANCH_ELEMENTS = {
    '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
    '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水',
}
GENERATES = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
CONTROLS  = {'木':'土','火':'金','土':'水','金':'木','水':'火'}

# 月支对应月份（节气月）
BRANCH_MONTH = {
    '寅':1,'卯':2,'辰':3,'巳':4,'午':5,'未':6,
    '申':7,'酉':8,'戌':9,'亥':10,'子':11,'丑':12,
}

# ─────────────────────────────────────────────────────────────────
# 穷通宝鉴调候用神表
# 格式：(日干, 月支) -> {
#   'yong': [主用神五行, ...],      # 第一位最重要
#   'ji':   [忌神五行, ...],
#   'note': '简要说明',
# }
# 数据来源：《穷通宝鉴》逐条整理，取主用神（不含全文）
# ─────────────────────────────────────────────────────────────────

TIAOHOU_TABLE: Dict[Tuple[str,str], Dict] = {

    # ══════════════════════════════════════════════════════════════
    # 甲木
    # ══════════════════════════════════════════════════════════════
    ('甲','寅'): {'yong':['火','水'], 'ji':['金'], 'note':'初春余寒，丙火温暖为先，癸水次之'},
    ('甲','卯'): {'yong':['金','水'], 'ji':['水'], 'note':'二月阳刃，庚金驾杀，财资之'},
    ('甲','辰'): {'yong':['金','水'], 'ji':['火'], 'note':'三月木气竭，先庚后壬'},
    ('甲','巳'): {'yong':['水','火'], 'ji':['土'], 'note':'四月退气，先癸后丁，庚金佐之'},
    ('甲','午'): {'yong':['水','火'], 'ji':['土'], 'note':'五月木虚焦，癸水为先，丁庚次之'},
    ('甲','未'): {'yong':['水','火'], 'ji':['土'], 'note':'六月同五月，先癸后丁'},
    ('甲','申'): {'yong':['火','水'], 'ji':['金'], 'note':'七月先丁后庚，丙火次之'},
    ('甲','酉'): {'yong':['火','金'], 'ji':['水'], 'note':'八月丁火为先，庚金次之'},
    ('甲','戌'): {'yong':['火','水'], 'ji':['土'], 'note':'九月先丁癸，庚金再次'},
    ('甲','亥'): {'yong':['火','土'], 'ji':['水'], 'note':'十月庚丁为要，丙火次之，忌壬泛'},
    ('甲','子'): {'yong':['火','金'], 'ji':['水'], 'note':'十一月寒枝，丁先庚后，丙火佐之'},
    ('甲','丑'): {'yong':['火','金'], 'ji':['水'], 'note':'十二月极寒，庚劈甲引丁，丁不可少'},

    # ══════════════════════════════════════════════════════════════
    # 乙木
    # ══════════════════════════════════════════════════════════════
    ('乙','寅'): {'yong':['火','水'], 'ji':['土'], 'note':'正月余寒，丙火为先，癸水次之'},
    ('乙','卯'): {'yong':['火','水'], 'ji':['金'], 'note':'二月阳气升，丙为君，癸为臣'},
    ('乙','辰'): {'yong':['水','火'], 'ji':['金'], 'note':'三月先癸后丙'},
    ('乙','巳'): {'yong':['水','金'], 'ji':['土'], 'note':'四月专用癸水，辛金佐之'},
    ('乙','午'): {'yong':['水','火'], 'ji':['土'], 'note':'五月上半月癸水，下半月丙癸齐用'},
    ('乙','未'): {'yong':['水','火'], 'ji':['土'], 'note':'六月木性且寒，癸水为先，丙火次之'},
    ('乙','申'): {'yong':['火','土'], 'ji':['金'], 'note':'七月喜己土，丙癸酌用'},
    ('乙','酉'): {'yong':['水','火'], 'ji':['金'], 'note':'八月白露前癸水，秋分后丙火'},
    ('乙','戌'): {'yong':['水','金'], 'ji':['土'], 'note':'九月根枯，癸水滋养，辛金发源'},
    ('乙','亥'): {'yong':['火','土'], 'ji':['水'], 'note':'十月丙火为用，戊土次之'},
    ('乙','子'): {'yong':['火'],      'ji':['水'], 'note':'十一月专用丙火解冻，忌癸冻木'},
    ('乙','丑'): {'yong':['火'],      'ji':['水'], 'note':'十二月寒谷回春，丙火为先'},

    # ══════════════════════════════════════════════════════════════
    # 丙火
    # ══════════════════════════════════════════════════════════════
    ('丙','寅'): {'yong':['水','金'], 'ji':['土'], 'note':'正月壬水为尊，庚金佐之'},
    ('丙','卯'): {'yong':['水','土'], 'ji':['金'], 'note':'二月专用壬水，戊土制水'},
    ('丙','辰'): {'yong':['水','木'], 'ji':['土'], 'note':'三月壬水为用，甲木辅之'},
    ('丙','巳'): {'yong':['水','金'], 'ji':['土'], 'note':'四月建禄，专用壬水，庚金发源'},
    ('丙','午'): {'yong':['水','金'], 'ji':['土'], 'note':'五月壬庚高透为上命'},
    ('丙','未'): {'yong':['水','金'], 'ji':['土'], 'note':'六月退气，壬水为用，庚辅佐'},
    ('丙','申'): {'yong':['水','土'], 'ji':['金'], 'note':'七月仍用壬水，戊土制之'},
    ('丙','酉'): {'yong':['水','土'], 'ji':['金'], 'note':'八月余光，壬水辅映'},
    ('丙','戌'): {'yong':['木','水'], 'ji':['土'], 'note':'九月先甲后壬，忌土晦光'},
    ('丙','亥'): {'yong':['木','土','金'], 'ji':['水'], 'note':'十月甲戊庚出干，木旺宜庚，水旺宜戊'},
    ('丙','子'): {'yong':['水','土'], 'ji':['金'], 'note':'十一月壬水为最，戊土佐之'},
    ('丙','丑'): {'yong':['水','木'], 'ji':['土'], 'note':'十二月壬甲两透，己土司令须甲疏'},

    # ══════════════════════════════════════════════════════════════
    # 丁火
    # ══════════════════════════════════════════════════════════════
    ('丁','寅'): {'yong':['金','木'], 'ji':['水'], 'note':'正月庚金劈甲引丁，甲木为引'},
    ('丁','卯'): {'yong':['金','木'], 'ji':['水'], 'note':'二月先庚后甲，非庚不能去乙'},
    ('丁','辰'): {'yong':['木','金'], 'ji':['水'], 'note':'三月先甲后庚，甲疏戊土'},
    ('丁','巳'): {'yong':['木','金'], 'ji':['水'], 'note':'四月甲引丁，庚劈甲，忌癸'},
    ('丁','午'): {'yong':['水','木'], 'ji':['土'], 'note':'五月建禄，壬水为贵，甲木佐之'},
    ('丁','未'): {'yong':['木','水'], 'ji':['土'], 'note':'六月退气，专取甲木，壬水次之'},
    ('丁','申'): {'yong':['木','火'], 'ji':['水'], 'note':'七月退气，甲木为先，丙暖金晒甲'},
    ('丁','酉'): {'yong':['木','水'], 'ji':['金'], 'note':'八月甲木引丁，壬水次之'},
    ('丁','戌'): {'yong':['木','金'], 'ji':['土'], 'note':'九月甲木为先，庚金次之'},
    ('丁','亥'): {'yong':['木','金'], 'ji':['水'], 'note':'三冬丁火，专用庚甲，甲乃庚之良友'},
    ('丁','子'): {'yong':['木','金'], 'ji':['水'], 'note':'十一月同亥月，庚甲为要，丙火佐之'},
    ('丁','丑'): {'yong':['木','金'], 'ji':['水'], 'note':'十二月庚甲为要，丙火佐之'},

    # ══════════════════════════════════════════════════════════════
    # 戊土
    # ══════════════════════════════════════════════════════════════
    ('戊','寅'): {'yong':['火','水','木'], 'ji':['金'], 'note':'正二月先丙后甲癸，无丙不暖'},
    ('戊','卯'): {'yong':['火','水','木'], 'ji':['金'], 'note':'二月同寅月，丙甲癸三者'},
    ('戊','辰'): {'yong':['水','火','木'], 'ji':['金'], 'note':'三月先癸后丙，甲疏土'},
    ('戊','巳'): {'yong':['木','火','水'], 'ji':['土'], 'note':'四月先甲疏劈，次丙癸为佐'},
    ('戊','午'): {'yong':['水','木'], 'ji':['火'], 'note':'五月仲夏火炎，先壬后甲，丙酌用'},
    ('戊','未'): {'yong':['水','火','木'], 'ji':['土'], 'note':'六月乾枯，先癸后丙甲'},
    ('戊','申'): {'yong':['火','水','木'], 'ji':['金'], 'note':'七月先丙后癸，甲木次之'},
    ('戊','酉'): {'yong':['火','水'], 'ji':['金'], 'note':'八月金泄身寒，先丙后癸'},
    ('戊','戌'): {'yong':['木','水','火'], 'ji':['土'], 'note':'九月先甲后癸，忌化合'},
    ('戊','亥'): {'yong':['木','火'], 'ji':['水'], 'note':'十月先甲后丙，非甲土不灵'},
    ('戊','子'): {'yong':['火','木'], 'ji':['水'], 'note':'十一二月严寒，丙火为尊，甲木为佐'},
    ('戊','丑'): {'yong':['火','木'], 'ji':['水'], 'note':'十二月同子月，丙甲两透'},

    # ══════════════════════════════════════════════════════════════
    # 己土
    # ══════════════════════════════════════════════════════════════
    ('己','寅'): {'yong':['火','水'], 'ji':['水'], 'note':'正月田园犹冻，丙为尊，忌壬泛'},
    ('己','卯'): {'yong':['木','水','火'], 'ji':['金'], 'note':'二月先甲疏土，次癸水润之'},
    ('己','辰'): {'yong':['火','水','木'], 'ji':['金'], 'note':'三月先丙后癸，随用甲疏'},
    ('己','巳'): {'yong':['水','火'], 'ji':['土'], 'note':'四月杂气才官，取癸为要，次丙火'},
    ('己','午'): {'yong':['水','火'], 'ji':['土'], 'note':'五月同巳月，癸丙齐用'},
    ('己','未'): {'yong':['水','火'], 'ji':['土'], 'note':'六月同巳月，癸丙为用'},
    ('己','申'): {'yong':['火','水'], 'ji':['金'], 'note':'七月三秋，癸先丙后，辛辅癸'},
    ('己','酉'): {'yong':['火','水'], 'ji':['金'], 'note':'八月同申月，癸先丙后'},
    ('己','戌'): {'yong':['火','水'], 'ji':['金'], 'note':'九月同申月，九月土盛宜甲疏'},
    ('己','亥'): {'yong':['火','木'], 'ji':['水'], 'note':'十月三冬，丙火为尊，甲木参酌'},
    ('己','子'): {'yong':['火','木'], 'ji':['水'], 'note':'十一月同亥月，丙火为尊'},
    ('己','丑'): {'yong':['火','木'], 'ji':['水'], 'note':'十二月同亥月，丙火为尊'},

    # ══════════════════════════════════════════════════════════════
    # 庚金
    # ══════════════════════════════════════════════════════════════
    ('庚','寅'): {'yong':['火','木'], 'ji':['水'], 'note':'正月先丙暖庚，甲疏土，丁火次之'},
    ('庚','卯'): {'yong':['火','木'], 'ji':['水'], 'note':'二月专用丁火，甲引丁，庚劈甲'},
    ('庚','辰'): {'yong':['木','火'], 'ji':['水'], 'note':'三月先甲后丁，土旺金顽'},
    ('庚','巳'): {'yong':['水','土','火'], 'ji':['木'], 'note':'四月长生，先壬后戊，丙火佐之'},
    ('庚','午'): {'yong':['水','水'], 'ji':['火'], 'note':'五月败地，专用壬水，癸次之'},
    ('庚','未'): {'yong':['火','木'], 'ji':['水'], 'note':'六月三伏生寒，先丁后甲'},
    ('庚','申'): {'yong':['火','木'], 'ji':['水'], 'note':'七月刚锐，专用丁火，甲引丁'},
    ('庚','酉'): {'yong':['火','木'], 'ji':['水'], 'note':'八月刚锐退，丁甲丙并用'},
    ('庚','戌'): {'yong':['木','水'], 'ji':['土'], 'note':'九月先甲疏土，后壬洗金'},
    ('庚','亥'): {'yong':['火','木'], 'ji':['水'], 'note':'十月水冷性寒，非丁莫造，非丙不暖'},
    ('庚','子'): {'yong':['火','木'], 'ji':['水'], 'note':'十一月仍取丁甲，丙火照暖'},
    ('庚','丑'): {'yong':['火','火','木'], 'ji':['水'], 'note':'十二月寒气太重，先丙后丁，甲不可少'},

    # ══════════════════════════════════════════════════════════════
    # 辛金
    # ══════════════════════════════════════════════════════════════
    ('辛','寅'): {'yong':['土','水'], 'ji':['木'], 'note':'正月先己土，次壬水，庚金佐之'},
    ('辛','卯'): {'yong':['水','木'], 'ji':['土'], 'note':'二月壬水为尊，甲制戊，忌戊己'},
    ('辛','辰'): {'yong':['水','木'], 'ji':['火'], 'note':'三月先壬后甲，忌丙贪合'},
    ('辛','巳'): {'yong':['水','金'], 'ji':['火'], 'note':'四月忌丙燥烈，喜壬水洗淘'},
    ('辛','午'): {'yong':['土','水'], 'ji':['火'], 'note':'五月失令，己壬兼用，无壬癸亦可'},
    ('辛','未'): {'yong':['水','金'], 'ji':['土'], 'note':'六月先壬后庚，忌戊出'},
    ('辛','申'): {'yong':['水','土','木'], 'ji':['火'], 'note':'七月壬水为尊，甲戊酌用'},
    ('辛','酉'): {'yong':['水','木'], 'ji':['土'], 'note':'八月当令，专用壬水淘洗，甲制土'},
    ('辛','戌'): {'yong':['水','木'], 'ji':['火'], 'note':'九月先壬后甲，火土为病，水木为药'},
    ('辛','亥'): {'yong':['水','火'], 'ji':['土'], 'note':'十月先壬后丙，金白水清'},
    ('辛','子'): {'yong':['火','水'], 'ji':['水'], 'note':'十一月癸水冻金，壬丙两透，忌癸出'},
    ('辛','丑'): {'yong':['火','水'], 'ji':['土'], 'note':'十二月寒冻，先丙后壬，戊己次之'},

    # ══════════════════════════════════════════════════════════════
    # 壬水
    # ══════════════════════════════════════════════════════════════
    ('壬','寅'): {'yong':['金','火','土'], 'ji':['木'], 'note':'正月先庚发源，次丙除寒，戊止流'},
    ('壬','卯'): {'yong':['土','金'], 'ji':['木'], 'note':'二月专取戊土为堤，辛发其源'},
    ('壬','辰'): {'yong':['木','金'], 'ji':['土'], 'note':'三月先甲疏土，次庚金'},
    ('壬','巳'): {'yong':['水','金'], 'ji':['火'], 'note':'四月水弱，取壬比肩，辛金发源'},
    ('壬','午'): {'yong':['水','金'], 'ji':['火'], 'note':'五月丁旺壬弱，取癸为用，庚为佐'},
    ('壬','未'): {'yong':['金','水','木'], 'ji':['土'], 'note':'六月先辛后甲，次取癸水'},
    ('壬','申'): {'yong':['土','火'], 'ji':['木'], 'note':'七月长生，专用戊土，丁火佐戊'},
    ('壬','酉'): {'yong':['木','金'], 'ji':['土'], 'note':'八月金白水清，专用甲木制戊'},
    ('壬','戌'): {'yong':['木','火'], 'ji':['土'], 'note':'九月进气，先甲后丙，戊出干用丙'},
    ('壬','亥'): {'yong':['土','火'], 'ji':['木'], 'note':'十月至旺，取戊为用，丙火次之'},
    ('壬','子'): {'yong':['土','火'], 'ji':['木'], 'note':'十一月阳刃，先戊后丙，丙戊两透'},
    ('壬','丑'): {'yong':['火','木'], 'ji':['水'], 'note':'十二月旺极复衰，专用丙火，甲木佐之'},

    # ══════════════════════════════════════════════════════════════
    # 癸水
    # ══════════════════════════════════════════════════════════════
    ('癸','寅'): {'yong':['金','火'], 'ji':['土'], 'note':'正月先辛金发源，次丙火照暖'},
    ('癸','卯'): {'yong':['金'], 'ji':['火'], 'note':'二月专用庚金，辛金次之'},
    ('癸','辰'): {'yong':['火','金','木'], 'ji':['土'], 'note':'三月清明前丙火，谷雨后辛甲佐之'},
    ('癸','巳'): {'yong':['金','水'], 'ji':['火'], 'note':'四月喜辛金为用，无辛用庚'},
    ('癸','午'): {'yong':['金','水'], 'ji':['火'], 'note':'五月至弱，庚辛壬参酌并用'},
    ('癸','未'): {'yong':['金','水'], 'ji':['火'], 'note':'六月专用庚辛，忌丁透'},
    ('癸','申'): {'yong':['火','木'], 'ji':['金'], 'note':'七月死处逢生，取丁火为用，甲引丁'},
    ('癸','酉'): {'yong':['金','火'], 'ji':['土'], 'note':'八月金白水清，辛金为用，丙火佐之'},
    ('癸','戌'): {'yong':['金','木'], 'ji':['土'], 'note':'九月失令，辛甲并用，比肩滋甲制戊'},
    ('癸','亥'): {'yong':['金'], 'ji':['木'], 'note':'十月旺中有弱，庚辛为妙'},
    ('癸','子'): {'yong':['火','金'], 'ji':['水'], 'note':'十一月冰冻，专用丙火解冻，辛金滋扶'},
    ('癸','丑'): {'yong':['火','水'], 'ji':['土'], 'note':'十二月寒极成冰，丙火解冻，壬水辅之'},
}


# ─────────────────────────────────────────────────────────────────
# 寒暖燥湿评分（用于辅助判断调候紧迫程度）
# 正值=暖燥，负值=寒湿，区间[-12, 12]
# ─────────────────────────────────────────────────────────────────

BRANCH_TEMP = {
    '寅': 2, '卯': 3, '辰': 1,
    '巳': 5, '午': 6, '未': 4,
    '申': -1,'酉': -2,'戌': -1,
    '亥': -4,'子': -6,'丑': -5,
}
STEM_TEMP = {
    '甲': 1, '乙': 1, '丙': 4, '丁': 3, '戊': 1,
    '己': 0, '庚': -2,'辛': -2,'壬': -3,'癸': -4,
}
ELEMENT_TEMP = {'木': 1, '火': 4, '土': 0, '金': -2, '水': -3}


def calc_temp_score(pillars_list: list) -> int:
    """
    计算命局寒暖燥湿总分。正=暖燥，负=寒湿。
    注意：三合/三会局会改变地支的五行属性，影响寒暖计算。
    例如：巳酉丑三合金局后，巳的火性被金局吸收，暖度大幅降低。
    """
    # 先检测三合/三会局
    all_zhis = [p.get('zhi', '') for p in pillars_list]
    branch_set = set(all_zhis)

    # 记录被三合/三会吸收的地支（其原始五行属性被改变）
    absorbed_zhis = {}  # zhi -> 合化后的五行

    for members, element in SANHUI:
        if members.issubset(branch_set):
            for zhi in members:
                absorbed_zhis[zhi] = element

    for members, element in SANHE:
        if members.issubset(branch_set):
            for zhi in members:
                if zhi not in absorbed_zhis:  # 三会优先
                    absorbed_zhis[zhi] = element

    score = 0
    for p in pillars_list:
        score += STEM_TEMP.get(p.get('gan', ''), 0)
        zhi = p.get('zhi', '')
        if zhi in absorbed_zhis:
            # 地支被合化，用合化后五行的温度，但原始温度保留30%
            original_temp = BRANCH_TEMP.get(zhi, 0)
            merged_element = absorbed_zhis[zhi]
            merged_temp = ELEMENT_TEMP.get(merged_element, 0)
            # 合化后：30%原始 + 70%合化五行温度
            effective_temp = int(original_temp * 0.3 + merged_temp * 0.7)
            score += effective_temp
        else:
            score += BRANCH_TEMP.get(zhi, 0)

    return score


# ─────────────────────────────────────────────────────────────────
# 日主强弱判断（改进版，考虑三合/三会）
# ─────────────────────────────────────────────────────────────────

HIDDEN_STEMS = {
    '子':['癸'],'丑':['己','癸','辛'],'寅':['甲','丙','戊'],
    '卯':['乙'],'辰':['戊','乙','癸'],'巳':['丙','戊','庚'],
    '午':['丁','己'],'未':['己','丁','乙'],'申':['庚','壬','戊'],
    '酉':['辛'],'戌':['戊','辛','丁'],'亥':['壬','甲'],
}

SANHE = [
    ({'申','子','辰'}, '水'), ({'寅','午','戌'}, '火'),
    ({'巳','酉','丑'}, '金'), ({'亥','卯','未'}, '木'),
]
SANHUI = [
    ({'亥','子','丑'}, '水'), ({'寅','卯','辰'}, '木'),
    ({'巳','午','未'}, '火'), ({'申','酉','戌'}, '金'),
]

# 月令旺衰分值
MONTH_STRENGTH = {
    # (日主五行, 月支) -> 分值  正=得令/旺，负=失令/弱
    ('木','寅'):3,('木','卯'):3,('木','亥'):1,('木','子'):1,('木','辰'):1,
    ('木','巳'):-1,('木','午'):-2,('木','未'):-1,('木','申'):-2,('木','酉'):-3,('木','戌'):-1,('木','丑'):-1,
    ('火','巳'):3,('火','午'):3,('火','寅'):1,('火','卯'):1,('火','未'):1,
    ('火','申'):-1,('火','酉'):-2,('火','戌'):-1,('火','亥'):-2,('火','子'):-3,('火','丑'):-2,('火','辰'):-1,
    ('土','辰'):2,('土','戌'):2,('土','丑'):2,('土','未'):2,('土','巳'):1,('土','午'):1,
    ('土','申'):-1,('土','酉'):-1,('土','亥'):-2,('土','子'):-2,('土','寅'):-1,('土','卯'):-1,
    ('金','申'):3,('金','酉'):3,('金','辰'):1,('金','丑'):1,('金','戌'):1,
    ('金','亥'):-1,('金','子'):-1,('金','寅'):-2,('金','卯'):-3,('金','巳'):-1,('金','午'):-2,('金','未'):-1,
    ('水','亥'):3,('水','子'):3,('水','申'):1,('水','酉'):1,('水','丑'):-1,
    ('水','寅'):-1,('水','卯'):-1,('水','辰'):-1,('水','巳'):-2,('水','午'):-3,('水','未'):-2,('水','戌'):-1,
}


def get_daymaster_strength_v2(pillars_list: list, day_gan: str) -> Tuple[str, int]:
    """
    改进版日主强弱判断。
    返回 (强弱标签, 数值分)
    标签: '极旺'/'旺'/'中'/'弱'/'极弱'
    """
    day_element = STEM_ELEMENTS.get(day_gan, '')
    if not day_element:
        return '中', 0

    # 月支
    month_zhi = ''
    for p in pillars_list:
        if p.get('index') == 1:
            month_zhi = p.get('zhi', '')
            break

    score = MONTH_STRENGTH.get((day_element, month_zhi), 0) * 3  # 月令权重最大

    # 收集所有地支
    all_zhis = [p.get('zhi', '') for p in pillars_list]
    branch_set = set(all_zhis)

    # 三合/三会加成（完整三合力量强于单支，给予更高权重）
    for members, element in SANHE:
        if members.issubset(branch_set):
            if element == day_element:
                score += 5   # 三合同五行，帮身极强
            elif GENERATES.get(element) == day_element:
                score += 3   # 三合印局，生身有力（原来+2，提升为+3）
            elif CONTROLS.get(day_element) == element:
                score -= 3   # 三合财局，耗身较重

    for members, element in SANHUI:
        if members.issubset(branch_set):
            if element == day_element:
                score += 6   # 三会同五行，帮身最强
            elif GENERATES.get(element) == day_element:
                score += 4   # 三会印局，生身极强
            elif CONTROLS.get(day_element) == element:
                score -= 4   # 三会财局，耗身极重

    # 天干帮扶/克泄
    for p in pillars_list:
        if p.get('index') == 2:
            continue  # 跳过日干本身
        gan = p.get('gan', '')
        gan_elem = STEM_ELEMENTS.get(gan, '')
        if gan_elem == day_element:
            score += 2  # 比劫帮身
        elif GENERATES.get(gan_elem) == day_element:
            score += 1  # 印星生身
        elif CONTROLS.get(day_element) == gan_elem:
            score -= 1  # 财星耗身
        elif CONTROLS.get(gan_elem) == day_element:
            score -= 2  # 官杀克身

    # 地支藏干帮扶
    for zhi in all_zhis:
        for hidden in HIDDEN_STEMS.get(zhi, []):
            h_elem = STEM_ELEMENTS.get(hidden, '')
            if h_elem == day_element:
                score += 1
            elif GENERATES.get(h_elem) == day_element:
                score += 0.5

    if score >= 8:
        return '极旺', score
    elif score >= 3:
        return '旺', score
    elif score >= -2:
        return '中', score
    elif score >= -6:
        return '弱', score
    else:
        return '极弱', score



# ─────────────────────────────────────────────────────────────────
# 从格判断（改进版，已在 format_analyzer 修过，这里独立实现）
# ─────────────────────────────────────────────────────────────────

def check_cong_ge(pillars_list: list, day_gan: str, ten_gods_map: dict) -> Optional[dict]:
    """
    判断是否为从格。
    返回 None 表示非从格，否则返回从格信息字典。
    """
    strength_label, score = get_daymaster_strength_v2(pillars_list, day_gan)
    if strength_label not in ('弱', '极弱'):
        return None

    day_element = STEM_ELEMENTS.get(day_gan, '')
    input_element = ''
    for k, v in GENERATES.items():
        if v == day_element:
            input_element = k
            break

    all_zhis = [p.get('zhi', '') for p in pillars_list]
    branch_set = set(all_zhis)

    # 三合/三会生扶日主 → 不能从
    for members, element in SANHE + SANHUI:
        if len(members & branch_set) >= (3 if element in [e for _,e in SANHE] else 3):
            if GENERATES.get(element) == day_element or element == day_element:
                return None
        elif len(members & branch_set) >= 2:
            if members.issubset(branch_set) and (GENERATES.get(element) == day_element or element == day_element):
                return None

    # 天干有印比透出 → 不能从
    for p in pillars_list:
        if p.get('index') == 2:
            continue
        gan_elem = STEM_ELEMENTS.get(p.get('gan', ''), '')
        if gan_elem == day_element or gan_elem == input_element:
            return None

    # 地支有印星或比劫的强根（主气/中气）→ 不能真从
    # 余气（藏干第三位）力量太弱，不算有根
    for p in pillars_list:
        zhi = p.get('zhi', '')
        hidden = HIDDEN_STEMS.get(zhi, [])
        # 只看主气（index 0）和中气（index 1），余气不算
        for idx, h in enumerate(hidden[:2]):
            if h is None:
                continue
            h_elem = STEM_ELEMENTS.get(h, '')
            if h_elem == day_element or h_elem == input_element:
                # 主气有根：绝对不能从
                # 中气有根：力量较弱，但仍构成"有根"，不能真从
                return None

    # 统计十神分布
    counts = {}
    for pillar_key, data in ten_gods_map.items():
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg and stem_tg != '日主':
            counts[stem_tg] = counts.get(stem_tg, 0) + 2
        for hd in data.get('branch_hidden', []):
            tg = hd.get('ten_god', '')
            if tg:
                counts[tg] = counts.get(tg, 0) + 1

    CONG_GE_MAP = {
        '食神':'从儿格','伤官':'从儿格',
        '正财':'从财格','偏财':'从财格',
        '七杀':'从杀格','正官':'从官格',
    }
    for tg, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        if cnt >= 6 and tg in CONG_GE_MAP:
            dominant_elem = STEM_ELEMENTS.get(
                next((g for g,t in {
                    '甲':'食','乙':'食','丙':'才','丁':'财',
                    '戊':'官','己':'杀','庚':'印','辛':'枭','壬':'劫','癸':'比',
                }.items() if t == tg), ''), ''
            )
            return {
                'name': CONG_GE_MAP[tg],
                'dominant_god': tg,
                'note': f'从格命局，顺从{tg}之气',
            }
    return None


# ─────────────────────────────────────────────────────────────────
# 核心取用神函数
# ─────────────────────────────────────────────────────────────────

def get_yongshen(
    pillars_list: list,
    day_gan: str,
    month_zhi: str,
    ten_gods_map: dict,
) -> dict:
    """
    三法合一取用神。

    参数：
      pillars_list: bazi_chart 的 pillars 列表
      day_gan:      日干（如 '癸'）
      month_zhi:    月支（如 '丑'）
      ten_gods_map: lib 格式的 pillars 字典（含 stem_ten_god/branch_hidden）

    返回：
      {
        'yong_shen':   主用神五行（字符串）
        'yong_list':   用神五行列表（按优先级）
        'ji_shen':     忌神五行列表
        'strength':    日主强弱标签
        'strength_score': 数值分
        'method':      取用方法（'调候'/'病药'/'通关'/'从格'）
        'tiaohou':     调候用神信息（dict or None）
        'cong_ge':     从格信息（dict or None）
        'note':        取用说明
        'temp_score':  寒暖燥湿分值
      }
    """
    day_element = STEM_ELEMENTS.get(day_gan, '')
    strength_label, strength_score = get_daymaster_strength_v2(pillars_list, day_gan)
    temp_score = calc_temp_score(pillars_list)

    # ── 1. 从格判断（优先级最高，从格用神与普通命局完全不同）──
    cong_ge = check_cong_ge(pillars_list, day_gan, ten_gods_map)
    if cong_ge:
        dominant_god = cong_ge['dominant_god']
        yong, ji = _cong_ge_yongshen(day_element, dominant_god)
        xi, xiang = _calc_xi_shen(yong[0] if yong else '', day_element, '弱（从格）')
        return {
            'yong_shen':      yong[0] if yong else '',
            'yong_list':      yong,
            'ji_shen':        ji,
            'xi_shen':        xi,
            'xiang_shen':     xiang,
            'strength':       '弱（从格）',
            'strength_score': strength_score,
            'method':         '从格',
            'tiaohou':        None,
            'cong_ge':        cong_ge,
            'note':           f"{cong_ge['name']}，顺从{dominant_god}之气，用神为{yong}",
            'temp_score':     temp_score,
        }

    # ── 2. 调候用神（月支极寒/极热时优先，或总分极端时优先）──────
    tiaohou = TIAOHOU_TABLE.get((day_gan, month_zhi))

    # 月支寒暖单独判断（月令是命局核心，不能被其他柱抵消）
    month_temp = BRANCH_TEMP.get(month_zhi, 0)
    month_urgent = abs(month_temp) >= 4  # 月支寒暖明显（亥子丑/巳午未）
    total_urgent = abs(temp_score) >= 6  # 全局极端
    tiaohou_urgent = month_urgent or total_urgent

    # ── 调候优先的限制条件（梁湘润观点）──────────────────────────
    # 当调候用神与格局用神方向相反时，调候降为辅助，格局为主：
    # 条件1：调候用神生助日主（日主已旺/极旺，调候反而加重病症）
    #   例：己土极旺，调候用火，火生土更旺，反为害
    # 条件2：调候用神与日主同五行（等同于比劫帮身，日主旺时不需要）
    tiaohou_primary = tiaohou['yong'][0] if tiaohou and tiaohou.get('yong') else ''
    tiaohou_helps_daymaster = (
        tiaohou_primary and (
            GENERATES.get(tiaohou_primary) == day_element  # 调候用神生日主
            or tiaohou_primary == day_element               # 调候用神与日主同五行
        )
    )
    # 日主旺/极旺时，若调候用神生助日主，调候不能优先
    if tiaohou_helps_daymaster and strength_label in ('旺', '极旺'):
        tiaohou_urgent = False  # 降级：调候不优先，改为辅助

    if tiaohou and tiaohou_urgent:
        yong_list = tiaohou['yong']
        ji_list   = tiaohou.get('ji', [])
        # 调候用神与病药用神合并（调候为主，病药为辅）
        bingya_yong, bingya_ji = _bingya_yongshen(day_element, strength_label, pillars_list)
        # 合并忌神：排除调候用神（调候用神不能同时是忌神）
        tiaohou_yong_set = set(yong_list)
        merged_ji = list(dict.fromkeys(
            j for j in (ji_list + [j for j in bingya_ji if j not in ji_list])
            if j not in tiaohou_yong_set  # 调候用神不列为忌神
        ))
        # 如果病药忌神与调候用神冲突，加注说明
        conflict_note = ''
        for j in bingya_ji:
            if j in tiaohou_yong_set:
                conflict_note = f'（注：{j}为调候用神，虽病药法视为忌，但调候优先，以暖局为要）'
                break
        xi, xiang = _calc_xi_shen(yong_list[0], day_element, strength_label)
        return {
            'yong_shen':      yong_list[0],
            'yong_list':      yong_list,
            'ji_shen':        merged_ji,
            'xi_shen':        xi,
            'xiang_shen':     xiang,
            'strength':       strength_label,
            'strength_score': strength_score,
            'method':         '调候',
            'tiaohou':        tiaohou,
            'cong_ge':        None,
            'note':           f"月支{month_zhi}寒暖明显（月支{month_temp:+d}分，总分{temp_score:+d}），调候优先。{tiaohou['note']}{conflict_note}",
            'temp_score':     temp_score,
        }

    # ── 3. 病药用神（格局分析）────────────────────────────────
    bingya_yong, bingya_ji = _bingya_yongshen(day_element, strength_label, pillars_list)

    # 调候用神作为辅助参考（非极端时，或调候被降级时）
    if tiaohou:
        tiaohou_primary = tiaohou['yong'][0] if tiaohou['yong'] else ''
        if tiaohou_primary:
            # 只有当调候用神不生助日主时，才插入辅用神列表
            # 若调候用神生助日主（火生土、木生火等），且日主已旺/极旺，则不插入
            tiaohou_helps_daymaster_check = (
                GENERATES.get(tiaohou_primary) == day_element
                or tiaohou_primary == day_element
            )
            if not (tiaohou_helps_daymaster_check and strength_label in ('旺', '极旺')):
                if tiaohou_primary not in bingya_yong:
                    bingya_yong = [bingya_yong[0], tiaohou_primary] + bingya_yong[1:]
            # 调候忌神补充：但要排除病药用神（不能把病药用神列为忌神）
            bingya_yong_set = set(bingya_yong)
            for j in tiaohou.get('ji', []):
                if j not in bingya_ji and j not in bingya_yong_set:
                    bingya_ji.append(j)

    # ── 4. 通关用神（两方对峙时）──────────────────────────────
    tongguan = _check_tongguan(pillars_list, day_element)
    if tongguan and not bingya_yong:
        xi, xiang = _calc_xi_shen(tongguan['yong'], day_element, strength_label)
        return {
            'yong_shen':      tongguan['yong'],
            'yong_list':      [tongguan['yong']],
            'ji_shen':        bingya_ji,
            'xi_shen':        xi,
            'xiang_shen':     xiang,
            'strength':       strength_label,
            'strength_score': strength_score,
            'method':         '通关',
            'tiaohou':        tiaohou,
            'cong_ge':        None,
            'note':           tongguan['note'],
            'temp_score':     temp_score,
        }

    xi, xiang = _calc_xi_shen(bingya_yong[0] if bingya_yong else day_element, day_element, strength_label)
    return {
        'yong_shen':      bingya_yong[0] if bingya_yong else day_element,
        'yong_list':      bingya_yong,
        'ji_shen':        bingya_ji,
        'xi_shen':        xi,
        'xiang_shen':     xiang,
        'strength':       strength_label,
        'strength_score': strength_score,
        'method':         '病药' if not tiaohou_urgent else '调候+病药',
        'tiaohou':        tiaohou,
        'cong_ge':        None,
        'note':           _build_note(day_element, strength_label, bingya_yong, tiaohou, temp_score),
        'temp_score':     temp_score,
    }


def _calc_xi_shen(yong_shen: str, day_element: str, strength: str) -> list:
    """
    计算喜神列表。
    喜神 = 生助用神的五行，间接有利于命局。

    层次：
      用神：直接解决命局核心问题
      喜神：生助用神，间接有利
      相神：生助日主（日主弱时）或泄耗日主（日主旺时）
      忌神：克泄用神，或加重命局病症
      仇神：生助忌神

    对于调候用神（火）+ 日主弱的命局：
      用神：火（暖局）
      喜神：木（木生火，生助用神）
      相神：金（金生水，印星帮身）、水（比劫帮身）
      忌神：土（土克水，土晦火）
    """
    xi_shen = []

    if not yong_shen:
        return xi_shen

    # 喜神 = 生助用神的五行
    # 但需排除两种情况：
    # 1. 喜神与日主同五行（比劫，日主旺时是忌神）
    # 2. 喜神克日主（官杀，日主弱时是忌神）
    for elem, generates in GENERATES.items():
        if generates == yong_shen:
            # 排除与日主同五行
            if elem == day_element:
                break
            # 排除克日主的五行（官杀）
            if CONTROLS.get(elem) == day_element:
                break
            xi_shen.append(elem)
            break

    # 相神：帮助日主的五行（日主弱时额外有用）
    xiang_shen = []
    if strength in ('弱', '极弱'):
        # 印星（生身）
        for elem, generates in GENERATES.items():
            if generates == day_element and elem not in xi_shen and elem != yong_shen:
                xiang_shen.append(elem)
                break
        # 比劫（帮身）
        if day_element not in xi_shen and day_element != yong_shen:
            xiang_shen.append(day_element)

    return xi_shen, xiang_shen
    """从格用神取法。"""
    output_elem = GENERATES.get(day_element, '')
    input_elem  = next((k for k,v in GENERATES.items() if v == day_element), '')
    controlled  = CONTROLS.get(day_element, '')

    if dominant_god in ('食神', '伤官'):  # 从儿格
        return [output_elem, GENERATES.get(output_elem,'')], [day_element, input_elem]
    elif dominant_god in ('正财', '偏财'):  # 从财格
        return [controlled, output_elem], [day_element, input_elem]
    elif dominant_god in ('七杀', '正官'):  # 从杀/从官格
        killer = next((k for k,v in CONTROLS.items() if v == day_element), '')
        return [killer, controlled], [day_element]
    return [output_elem], [day_element]


def _bingya_yongshen(day_element: str, strength: str, pillars_list: list) -> Tuple[List, List]:
    """
    病药法取用神。

    日主旺/极旺时的用神优先级（《子平真诠》）：
      1. 食伤泄秀（顺势而为，最优雅）
      2. 财星耗身（食伤生财，连贯）
      3. 官杀克制（最后手段，有压力）
    忌神：印星（生身更旺）、比劫（帮身更旺）

    日主弱/极弱时的用神优先级：
      1. 印星生身
      2. 比劫帮身
    忌神：官杀（克身）、财星（耗身）、食伤（泄身）
    """
    output_elem = GENERATES.get(day_element, '')   # 食伤（我生）
    input_elem  = next((k for k,v in GENERATES.items() if v == day_element), '')  # 印星（生我）
    controlled  = CONTROLS.get(day_element, '')    # 财星（我克）
    killer_elem = next((k for k,v in CONTROLS.items() if v == day_element), '')   # 官杀（克我）

    if strength in ('极旺', '旺'):
        # 日主旺：食伤泄秀 > 财星耗身 > 官杀克制
        # 忌：印星（生身更旺）、比劫（帮身更旺）
        return [output_elem, controlled, killer_elem], [input_elem, day_element]
    elif strength in ('弱', '极弱'):
        # 日主弱：印星生身 > 比劫帮身
        # 忌：官杀（克身）、财星（耗身）
        return [input_elem, day_element], [killer_elem, controlled]
    else:
        # 中和：以月令为基础，调候为辅
        return [input_elem, day_element], [killer_elem]


def _check_tongguan(pillars_list: list, day_element: str) -> Optional[dict]:
    """通关用神判断。"""
    elem_scores = {'木':0,'火':0,'土':0,'金':0,'水':0}
    for p in pillars_list:
        gan_e = STEM_ELEMENTS.get(p.get('gan',''), '')
        zhi_e = BRANCH_ELEMENTS.get(p.get('zhi',''), '')
        if gan_e: elem_scores[gan_e] += 2
        if zhi_e: elem_scores[zhi_e] += 1

    # 找两个势均力敌且相克的五行
    for e1, e2 in [(k,v) for k,v in CONTROLS.items()]:
        s1, s2 = elem_scores[e1], elem_scores[e2]
        if s1 >= 4 and s2 >= 4 and abs(s1-s2) <= 3:
            # 找通关五行（e1生X，X生e2 或 e2生X，X生e1）
            tongguan_elem = GENERATES.get(e1, '')
            if tongguan_elem and GENERATES.get(tongguan_elem) == e2:
                return {'yong': tongguan_elem, 'note': f'{e1}与{e2}对峙，{tongguan_elem}通关'}
    return None


def _build_note(day_element, strength, yong_list, tiaohou, temp_score) -> str:
    parts = [f'日主{day_element}（{strength}）']
    if tiaohou:
        tiaohou_primary = tiaohou['yong'][0] if tiaohou.get('yong') else ''
        tiaohou_helps = (
            GENERATES.get(tiaohou_primary) == day_element
            or tiaohou_primary == day_element
        )
        if tiaohou_helps and strength in ('旺', '极旺'):
            parts.append(
                f'调候参考：{tiaohou["note"]}'
                f'（调候用神{tiaohou_primary}生助日主，日主已{strength}，调候降为参考，不作主用神）'
            )
        else:
            parts.append(f'调候参考：{tiaohou["note"]}')
    if yong_list:
        parts.append(f'用神：{"/ ".join(yong_list[:2])}')
    if temp_score:
        parts.append(f'寒暖分值：{temp_score:+d}')
    return '，'.join(parts)

