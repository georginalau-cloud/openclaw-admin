#!/usr/bin/env python3
"""
fortune_analyzer.py - 五运分析器

对大运或流年进行五个维度的深度分析：
  - intimate:  感情运
  - wealth:    财运
  - children:  子运（后代运）
  - official:  禄运（事业运）
  - longevity: 寿运（健康运）

用法：
    python3 fortune_analyzer.py <bazi_json> <full_report> <dimension> <cycle_json>

其中 cycle_json 格式：
    {
      "age": 44,
      "ganzhi": "壬申",
      "wangshuai": "建",
      "nayin": "剑锋金",
      "relations": {
        "chong": [],
        "xing": [],
        "hai": [],
        "he": ["丁"],
        "po": []
      }
    }

输出（JSON）：
    {"name": "财运", "status": "平", "insights": [...]}
"""

import json
import sys
import os

_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SKILL_DIR)

from lib.ganzhi_calculator import (
    STEM_ELEMENTS, BRANCH_ELEMENTS, HIDDEN_STEMS,
)
from lib.ten_gods_analyzer import get_ten_god


# ── 纳音五行映射 ──────────────────────────────────────────────────

NAYIN_ELEMENT = {
    '海中金': '金', '炉中火': '火', '大林木': '木', '路旁土': '土', '剑锋金': '金',
    '山头火': '火', '涧下水': '水', '城头土': '土', '白蜡金': '金', '杨柳木': '木',
    '泉中水': '水', '屋上土': '土', '霹雳火': '火', '松柏木': '木', '长流水': '水',
    '砂中金': '金', '山下火': '火', '平地木': '木', '壁上土': '土', '金箔金': '金',
    '覆灯火': '火', '天河水': '水', '大驿土': '土', '钗钏金': '金', '桑柘木': '木',
    '大溪水': '水', '沙中土': '土', '天上火': '火', '石榴木': '木', '大海水': '水',
}

# ── 旺衰：强度（1-10）及别名规范化 ────────────────────────────────

WANGSHUAI_STRENGTH = {
    '长生': 7, '沐浴': 5, '冠带': 7,
    '临官': 9, '建禄': 9, '建': 9,
    '帝旺': 10, '旺': 10,
    '衰': 4, '病': 3, '死': 2,
    '绝': 1, '胎': 2, '养': 3,
    '墓': 3, '库': 3,
}

# 短别名 → 完整名称（用于逻辑判断）
WANGSHUAI_ALIAS = {
    '建': '建禄',
    '旺': '帝旺',
    '库': '墓',
}

# ── 维度中文名映射 ─────────────────────────────────────────────────

DIMENSION_NAMES = {
    'intimate':  '感情运',
    'wealth':    '财运',
    'children':  '子运',
    'official':  '禄运',
    'longevity': '寿运',
}


class BaziFortuneAnalyzer:
    """
    五运分析器：对大运或流年进行五个维度的深度分析。

    支持的维度：
        intimate  - 感情运（财星/妻星、旺衰活力、纳音特质、刑冲合）
        wealth    - 财运（财星透干、食伤辅助、旺衰等级、纳音流向、干支关系）
        children  - 子运（食伤星、旺衰质量、刑冲威胁）
        official  - 禄运（官杀透干、建禄帝旺、纳音特质、职场人脉）
        longevity - 寿运（旺衰身体、墓库健康、纳音保养、刑冲害风险）
    """

    def __init__(self, bazi, full_report=''):
        """
        参数：
            bazi:        四柱干支字典，键为 year/month/day/hour，值如 "己巳"
            full_report: 完整八字精批报告文字（供参考上下文，可留空）
        """
        self.bazi = bazi
        self.full_report = full_report

        day_gz = bazi.get('day', '')
        self.day_stem = day_gz[0] if len(day_gz) >= 1 else ''
        self.day_element = STEM_ELEMENTS.get(self.day_stem, '')

    # ─────────────────────────────────────────────────────────────
    # 公共入口
    # ─────────────────────────────────────────────────────────────

    def analyze(self, dimension, cycle):
        """
        分析指定五运维度。

        参数：
            dimension: 'intimate' | 'wealth' | 'children' | 'official' | 'longevity'
            cycle: {
                "age": int,
                "ganzhi": "壬申",
                "wangshuai": "建",
                "nayin": "剑锋金",
                "relations": {"chong":[], "xing":[], "hai":[], "he":["丁"], "po":[]}
            }

        返回：
            {"name": str, "status": "吉"|"平"|"凶", "insights": [str, ...]}
        """
        ganzhi = cycle.get('ganzhi', '')
        cycle_stem = ganzhi[0] if len(ganzhi) >= 1 else ''
        cycle_branch = ganzhi[1] if len(ganzhi) >= 2 else ''

        # 旺衰
        ws_raw = cycle.get('wangshuai', '')
        ws_full = WANGSHUAI_ALIAS.get(ws_raw, ws_raw)
        ws_strength = WANGSHUAI_STRENGTH.get(ws_raw,
                      WANGSHUAI_STRENGTH.get(ws_full, 5))

        # 纳音
        nayin = cycle.get('nayin', '')
        nayin_element = NAYIN_ELEMENT.get(nayin, '')
        if not nayin_element:
            # 尝试从名称中提取五行字
            for elem in ('金', '木', '水', '火', '土'):
                if elem in nayin:
                    nayin_element = elem
                    break

        relations = cycle.get('relations', {})

        # 大运天干十神（相对日主）
        cycle_ten_god = ''
        if cycle_stem and self.day_stem:
            cycle_ten_god = get_ten_god(self.day_stem, cycle_stem)

        # 大运地支藏干十神
        hidden_ten_gods = []
        if cycle_branch in HIDDEN_STEMS:
            for h_stem in HIDDEN_STEMS[cycle_branch]:
                if h_stem:
                    tg = get_ten_god(self.day_stem, h_stem)
                    hidden_ten_gods.append({'stem': h_stem, 'ten_god': tg})

        ctx = {
            'ws_raw':          ws_raw,
            'ws_full':         ws_full,
            'ws_strength':     ws_strength,
            'cycle_ten_god':   cycle_ten_god,
            'hidden_ten_gods': hidden_ten_gods,
            'nayin':           nayin,
            'nayin_element':   nayin_element,
            'relations':       relations,
        }

        dispatch = {
            'intimate':  self._analyze_intimate,
            'wealth':    self._analyze_wealth,
            'children':  self._analyze_children,
            'official':  self._analyze_official,
            'longevity': self._analyze_longevity,
        }
        fn = dispatch.get(dimension)
        if fn:
            return fn(ctx)

        return {
            'name':     dimension,
            'status':   '平',
            'insights': [f'不支持的分析维度：{dimension}'],
        }

    # ─────────────────────────────────────────────────────────────
    # 感情运
    # ─────────────────────────────────────────────────────────────

    def _analyze_intimate(self, ctx):
        ws_raw      = ctx['ws_raw']
        ws_full     = ctx['ws_full']
        ws_strength = ctx['ws_strength']
        nayin       = ctx['nayin']
        nayin_el    = ctx['nayin_element']
        relations   = ctx['relations']
        all_tg      = [ctx['cycle_ten_god']] + [h['ten_god'] for h in ctx['hidden_ten_gods']]

        score    = 5
        insights = []

        # 1. 旺衰 → 感情活力
        if ws_strength >= 9:
            score += 1
            insights.append(f'大运{ws_raw}，禄旺身强，是积累和发展的好时期')
        elif ws_strength >= 7:
            insights.append(f'大运{ws_raw}，精力旺盛，感情活跃有动力')
        elif ws_strength in (4, 5):
            score -= 1
            insights.append(f'大运{ws_raw}，气势稍减，感情需耐心经营')
        elif ws_full in ('墓', '绝', '死'):
            score -= 2
            insights.append(f'大运{ws_raw}，感情低潮，宜静心等待，勿强求')
        else:
            insights.append(f'大运{ws_raw}，感情气息一般，随缘而行')

        # 2. 关系星透干（财星为妻星，官杀为夫星）
        if '正财' in all_tg or '正官' in all_tg:
            score += 2
            star = '正财' if '正财' in all_tg else '正官'
            insights.append(f'{star}现于大运，正缘来临，适合稳定感情')
        elif '偏财' in all_tg or '七杀' in all_tg:
            score += 1
            star = '偏财' if '偏财' in all_tg else '七杀'
            insights.append(f'{star}透运，异性缘旺，宜辨别正缘与过客')

        # 3. 纳音五行 → 感情特质
        nayin_msg = {
            '木': '木纳音主生发，感情缘分勃发，易邂逅新缘',
            '火': '火纳音主热情，感情炽烈，表达主动，易成缘',
            '水': '水纳音主情深，感情细腻绵长，重情重义',
            '金': '金纳音主收敛，感情内敛含蓄，需主动表达',
            '土': '土纳音主稳重，感情踏实可靠，重视承诺',
        }
        if nayin_el in nayin_msg:
            msg = nayin_msg[nayin_el]
            label = nayin if nayin else nayin_el
            if nayin_el in ('金',):
                score -= 1
            insights.append(f'{label}纳音，{msg.split("，", 1)[1]}')

        # 4. 干支关系 → 实际影响
        he_list   = relations.get('he', [])
        chong_list = relations.get('chong', [])
        xing_list  = relations.get('xing', [])
        hai_list   = relations.get('hai', [])

        if he_list:
            score += 2
            insights.append('大运相合，感情融洽，有利于婚配或巩固关系')
        if chong_list:
            score -= 2
            targets = '、'.join(chong_list[:2])
            insights.append(f'大运冲{targets}，感情易生波折，宜包容化解')
        if xing_list:
            score -= 1
            insights.append('大运带刑，感情关系紧张，沟通方式需调整')
        if hai_list:
            score -= 1
            insights.append('大运带害，感情暗流涌动，防小人破坏')

        return {
            'name':     DIMENSION_NAMES['intimate'],
            'status':   self._status_from_score(score),
            'insights': insights,
        }

    # ─────────────────────────────────────────────────────────────
    # 财运
    # ─────────────────────────────────────────────────────────────

    def _analyze_wealth(self, ctx):
        ws_raw      = ctx['ws_raw']
        ws_full     = ctx['ws_full']
        ws_strength = ctx['ws_strength']
        nayin       = ctx['nayin']
        nayin_el    = ctx['nayin_element']
        relations   = ctx['relations']
        cycle_tg    = ctx['cycle_ten_god']
        all_tg      = [cycle_tg] + [h['ten_god'] for h in ctx['hidden_ten_gods']]

        score    = 5
        insights = []

        # 1. 旺衰 → 投资风险与时机
        if ws_strength >= 9:
            score += 1
            insights.append(f'大运处于{ws_raw}，身强气盛，适合主动投资理财')
        elif ws_strength >= 7:
            insights.append(f'大运{ws_raw}，气势充足，财运稳步向好')
        elif ws_strength in (4, 5):
            score -= 1
            insights.append(f'大运{ws_raw}，精力有限，财运需稳健规划')
        elif ws_full in ('墓', '绝', '死'):
            score -= 2
            insights.append(f'大运{ws_raw}，财气萎靡，宜守成为主，避免冒险')
        else:
            insights.append(f'大运{ws_raw}，财运平淡，宜积累根基')

        # 2. 财星透干（正财/偏财直接透干才显示）
        if cycle_tg in ('正财', '偏财'):
            score += 2
            desc = '正财稳健，适合稳定收入理财' if cycle_tg == '正财' else '偏财旺盛，适合投资经营'
            insights.append(f'{cycle_tg}透于大运天干，{desc}')
        elif cycle_tg in ('正官', '七杀'):
            score += 1
            insights.append('官杀透干，晋升机遇带动收入提升')

        # 3. 纳音五行 → 财运流向
        nayin_msg = {
            '金': '金纳音主收敛，财运紧凑，需谨慎理财',
            '木': '木纳音主生长，财运扩展，适合开拓新业',
            '水': '水纳音主流通，财运灵活，资金流转顺畅',
            '火': '火纳音主显达，名利双收，财运因名气而旺',
            '土': '土纳音主积累，财运稳健，适合不动产投资',
        }
        if nayin_el in nayin_msg:
            label = nayin if nayin else nayin_el
            msg = nayin_msg[nayin_el]
            if nayin_el == '金':
                score -= 1
            elif nayin_el in ('木', '水', '火'):
                score += 1
            insights.append(msg)

        # 4. 干支关系 → 人脉与财路
        he_list    = relations.get('he', [])
        chong_list = relations.get('chong', [])
        xing_list  = relations.get('xing', [])

        if he_list:
            score += 1
            insights.append('大运相合，事业顺畅，人脉助力财运')
        if chong_list:
            score -= 2
            targets = '、'.join(chong_list[:2])
            insights.append(f'大运冲{targets}，财运波动，谨慎大额投资')
        if xing_list:
            score -= 1
            insights.append('大运带刑，财务纠纷风险上升，合同需谨慎')

        return {
            'name':     DIMENSION_NAMES['wealth'],
            'status':   self._status_from_score(score),
            'insights': insights,
        }

    # ─────────────────────────────────────────────────────────────
    # 子运
    # ─────────────────────────────────────────────────────────────

    def _analyze_children(self, ctx):
        ws_raw      = ctx['ws_raw']
        ws_full     = ctx['ws_full']
        ws_strength = ctx['ws_strength']
        nayin       = ctx['nayin']
        nayin_el    = ctx['nayin_element']
        relations   = ctx['relations']
        cycle_tg    = ctx['cycle_ten_god']
        all_tg      = [cycle_tg] + [h['ten_god'] for h in ctx['hidden_ten_gods']]

        score    = 5
        insights = []

        # 1. 旺衰 → 亲子关系质量
        if ws_strength >= 9:
            score += 1
            insights.append(f'大运{ws_raw}，精力充沛，亲子互动质量高')
        elif ws_strength >= 7:
            insights.append(f'大运{ws_raw}，气势稳固，有利亲子关系建立')
        elif ws_full in ('墓', '绝', '死', '病'):
            score -= 2
            insights.append(f'大运{ws_raw}，子女缘分偏薄，或亲子关系疏离')
        else:
            insights.append(f'大运{ws_raw}，子女关系平稳，随缘即可')

        # 2. 食伤星（子星）透干
        if cycle_tg == '食神':
            score += 2
            insights.append('食神透于大运，子女缘佳，亲子感情融洽')
        elif cycle_tg == '伤官':
            score += 1
            insights.append('伤官透运，子女聪慧有个性，需给予充分空间')
        elif cycle_tg in ('比肩', '劫财'):
            score -= 1
            insights.append('比劫透运，精力分散，亲子相处需主动投入')

        # 3. 纳音五行 → 子嗣特质
        nayin_msg = {
            '木': '木纳音主生育，子嗣运旺，利于孕育',
            '水': '水纳音主智慧，子女聪慧，学习能力强',
            '火': '火纳音主活力，子女活泼好动，精力旺盛',
            '金': '金纳音主严肃，亲子关系偏严，需加强沟通',
            '土': '土纳音主稳重，亲子关系踏实，家庭和睦',
        }
        if nayin_el in nayin_msg:
            label = nayin if nayin else nayin_el
            msg = nayin_msg[nayin_el]
            if nayin_el == '金':
                score -= 1
            elif nayin_el in ('木', '水'):
                score += 1
            insights.append(f'{label}纳音，{msg.split("，", 1)[1]}')

        # 4. 刑冲 → 子女威胁
        xing_list  = relations.get('xing', [])
        chong_list = relations.get('chong', [])
        he_list    = relations.get('he', [])

        if xing_list:
            score -= 2
            insights.append('大运带刑，子女关系紧张，需防亲子摩擦')
        if chong_list:
            score -= 1
            insights.append('大运逢冲，子女或有动荡，宜多沟通关注')
        if he_list:
            score += 1
            insights.append('大运相合，家庭和谐，有利亲子缘分')

        return {
            'name':     DIMENSION_NAMES['children'],
            'status':   self._status_from_score(score),
            'insights': insights,
        }

    # ─────────────────────────────────────────────────────────────
    # 禄运（事业运）
    # ─────────────────────────────────────────────────────────────

    def _analyze_official(self, ctx):
        ws_raw      = ctx['ws_raw']
        ws_full     = ctx['ws_full']
        ws_strength = ctx['ws_strength']
        nayin       = ctx['nayin']
        nayin_el    = ctx['nayin_element']
        relations   = ctx['relations']
        cycle_tg    = ctx['cycle_ten_god']
        all_tg      = [cycle_tg] + [h['ten_god'] for h in ctx['hidden_ten_gods']]

        score    = 5
        insights = []

        # 1. 旺衰 → 事业时机（建禄/帝旺是巅峰）
        if ws_full in ('建禄', '帝旺'):
            score += 3
            insights.append(f'大运{ws_raw}，事业巅峰期，晋升发展绝佳时机')
        elif ws_strength >= 7:
            score += 1
            insights.append(f'大运{ws_raw}，气势旺盛，事业推进顺畅')
        elif ws_strength in (4, 5):
            score -= 1
            insights.append(f'大运{ws_raw}，事业稳中有降，宜积蓄实力')
        elif ws_full in ('墓', '绝', '死'):
            score -= 2
            insights.append(f'大运{ws_raw}，事业低潮，宜蓄势待发，避免冒进')
        else:
            insights.append(f'大运{ws_raw}，事业平稳，量力而行')

        # 2. 官杀透干 → 升职机遇
        if cycle_tg == '正官':
            score += 2
            insights.append('正官透于大运，上司赏识，晋升机遇清晰')
        elif cycle_tg == '七杀':
            score += 1
            insights.append('七杀透运，竞争激烈，奋力拼搏可出头')
        elif cycle_tg in ('食神', '伤官'):
            score += 1
            insights.append(f'{cycle_tg}透运，展现专业才华，技能立业')
        elif cycle_tg in ('正印', '偏印'):
            insights.append('印星透运，贵人相助，适合学习提升资质')

        # 3. 纳音五行 → 事业发展特质
        nayin_msg = {
            '火': '火纳音主显达，事业能见度高，利名利双收',
            '木': '木纳音主成长，事业开拓，适合创业或拓展',
            '金': '金纳音主纪律，事业踏实，适合技术或管理',
            '水': '水纳音主谋略，事业需智谋布局，后劲十足',
            '土': '土纳音主沉稳，事业稳健，不适合冒进',
        }
        if nayin_el in nayin_msg:
            label = nayin if nayin else nayin_el
            msg = nayin_msg[nayin_el]
            if nayin_el in ('火', '木'):
                score += 1
            insights.append(f'{label}纳音，{msg.split("，", 1)[1]}')

        # 4. 干支关系 → 职场人脉
        he_list    = relations.get('he', [])
        chong_list = relations.get('chong', [])
        xing_list  = relations.get('xing', [])

        if he_list:
            score += 2
            insights.append('大运相合，职场人脉顺畅，贵人助力可期')
        if chong_list:
            score -= 2
            insights.append('大运逢冲，职场变动较大，宜主动适应调整')
        if xing_list:
            score -= 1
            insights.append('大运带刑，职场关系紧张，需注意同事摩擦')

        return {
            'name':     DIMENSION_NAMES['official'],
            'status':   self._status_from_score(score),
            'insights': insights,
        }

    # ─────────────────────────────────────────────────────────────
    # 寿运（健康运）
    # ─────────────────────────────────────────────────────────────

    def _analyze_longevity(self, ctx):
        ws_raw      = ctx['ws_raw']
        ws_full     = ctx['ws_full']
        ws_strength = ctx['ws_strength']
        nayin       = ctx['nayin']
        nayin_el    = ctx['nayin_element']
        relations   = ctx['relations']

        score    = 5
        insights = []

        # 1. 旺衰 → 直接影响身体状态
        if ws_strength >= 9:
            score += 2
            insights.append(f'大运{ws_raw}，身体精力旺盛，健康状态良好')
        elif ws_strength >= 7:
            score += 1
            insights.append(f'大运{ws_raw}，体力充足，注意劳逸结合')
        elif ws_strength in (4, 5):
            score -= 1
            insights.append(f'大运{ws_raw}，精力有所耗损，注意调养休息')
        elif ws_full in ('墓', '库'):
            score -= 2
            insights.append(f'大运{ws_raw}，墓库之期宜特别关注健康，定期体检')
        elif ws_full in ('病', '死', '绝'):
            score -= 3
            insights.append(f'大运{ws_raw}，体质偏弱，需注意慢性病防治')
        else:
            insights.append(f'大运{ws_raw}，健康需适度关注，保持良好作息')

        # 2. 纳音五行 → 季节保养重点
        nayin_health = {
            '金': ('对应肺与呼吸系统', '秋季注意保养呼吸道'),
            '木': ('对应肝与眼目', '春季注意养肝护目'),
            '水': ('对应肾与泌尿', '冬季注意补肾保暖'),
            '火': ('对应心与血压', '夏季注意防暑护心'),
            '土': ('对应脾胃消化', '季节交替注意脾胃调理'),
        }
        if nayin_el in nayin_health:
            label = nayin if nayin else nayin_el
            organ_hint, season_hint = nayin_health[nayin_el]
            insights.append(f'{label}纳音{organ_hint}，{season_hint}')

        # 3. 刑冲害 → 潜在健康风险
        xing_list  = relations.get('xing', [])
        chong_list = relations.get('chong', [])
        hai_list   = relations.get('hai', [])
        he_list    = relations.get('he', [])

        if xing_list:
            score -= 2
            insights.append('大运带刑，需防意外伤害与手术风险')
        if chong_list:
            score -= 1
            targets = '、'.join(chong_list[:2])
            insights.append(f'大运冲{targets}，健康有波动，注意压力管理')
        if hai_list:
            score -= 1
            insights.append('大运带害，注意慢性隐患，定期检查')
        if he_list:
            score += 1
            insights.append('大运相合，气血调和，适合积极保健')

        return {
            'name':     DIMENSION_NAMES['longevity'],
            'status':   self._status_from_score(score),
            'insights': insights,
        }

    # ─────────────────────────────────────────────────────────────
    # 工具方法
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _status_from_score(score):
        """综合分转换为状态：吉 / 平 / 凶"""
        if score >= 8:
            return '吉'
        elif score >= 5:
            return '平'
        else:
            return '凶'


# ── CLI 入口 ──────────────────────────────────────────────────────

def main():
    """
    命令行用法：
        python3 fortune_analyzer.py <bazi_json> <full_report> <dimension> <cycle_json>

    示例：
        python3 fortune_analyzer.py \\
          '{"year": "己巳", "month": "丁丑", "day": "庚辰", "hour": "庚辰"}' \\
          "$(cat report.json | jq -r '.full_report')" \\
          "wealth" \\
          '{"age": 44, "ganzhi": "壬申", "wangshuai": "建", "nayin": "剑锋金",
            "relations": {"chong": [], "xing": [], "hai": [], "he": ["丁"], "po": []}}'
    """
    if len(sys.argv) < 5:
        print(
            '用法: python3 fortune_analyzer.py <bazi_json> <full_report> <dimension> <cycle_json>',
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        bazi = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f'[fortune_analyzer] bazi_json 解析失败: {e}', file=sys.stderr)
        sys.exit(1)

    full_report = sys.argv[2]
    dimension   = sys.argv[3]

    try:
        cycle = json.loads(sys.argv[4])
    except json.JSONDecodeError as e:
        print(f'[fortune_analyzer] cycle_json 解析失败: {e}', file=sys.stderr)
        sys.exit(1)

    try:
        analyzer = BaziFortuneAnalyzer(bazi, full_report)
        result   = analyzer.analyze(dimension, cycle)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
