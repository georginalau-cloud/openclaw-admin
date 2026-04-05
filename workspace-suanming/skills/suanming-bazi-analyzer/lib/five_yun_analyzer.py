"""
five_yun_analyzer.py - 五运分析库模块

封装五运（感情、财、子、禄、寿）的分析逻辑。
从完整分析结果中提取大运流年数据，对每个维度进行结构化深度分析。

支持与 bazi_analyzer.py 集成，也可单独使用。
"""

import datetime

from .ganzhi_calculator import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENTS, BRANCH_ELEMENTS,
    HIDDEN_STEMS, STEM_POLARITY, GENERATES, CONTROLS
)
from .ten_gods_analyzer import get_ten_god


# ─── 长生十二宫（旺衰状态） ────────────────────────────────────────────────────
# 每个天干在各地支上的旺衰状态（长生、沐浴、冠带、临官/建禄、帝旺、衰、病、死、墓、绝、胎、养）
WANGSHUAI_MAP = {
    '甲': ['亥', '子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌'],
    '乙': ['午', '巳', '辰', '卯', '寅', '丑', '子', '亥', '戌', '酉', '申', '未'],
    '丙': ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'],
    '丁': ['酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑', '子', '亥', '戌'],
    '戊': ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'],
    '己': ['酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑', '子', '亥', '戌'],
    '庚': ['巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑', '寅', '卯', '辰'],
    '辛': ['子', '亥', '戌', '酉', '申', '未', '午', '巳', '辰', '卯', '寅', '丑'],
    '壬': ['申', '酉', '戌', '亥', '子', '丑', '寅', '卯', '辰', '巳', '午', '未'],
    '癸': ['卯', '寅', '丑', '子', '亥', '戌', '酉', '申', '未', '午', '巳', '辰'],
}

WANGSHUAI_NAMES = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']

# 旺衰强弱评级
WANGSHUAI_STRENGTH = {
    '长生': '旺', '沐浴': '平', '冠带': '旺', '临官': '强',
    '帝旺': '强', '衰': '弱', '病': '弱', '死': '弱',
    '墓': '平', '绝': '弱', '胎': '平', '养': '平',
}

# 纳音五行（六十甲子纳音，简化版，仅取旺衰判断用）
NAYIN_MAP = {
    '甲子': '海中金', '乙丑': '海中金', '丙寅': '炉中火', '丁卯': '炉中火',
    '戊辰': '大林木', '己巳': '大林木', '庚午': '路旁土', '辛未': '路旁土',
    '壬申': '剑锋金', '癸酉': '剑锋金', '甲戌': '山头火', '乙亥': '山头火',
    '丙子': '涧下水', '丁丑': '涧下水', '戊寅': '城头土', '己卯': '城头土',
    '庚辰': '白蜡金', '辛巳': '白蜡金', '壬午': '杨柳木', '癸未': '杨柳木',
    '甲申': '泉中水', '乙酉': '泉中水', '丙戌': '屋上土', '丁亥': '屋上土',
    '戊子': '霹雳火', '己丑': '霹雳火', '庚寅': '松柏木', '辛卯': '松柏木',
    '壬辰': '长流水', '癸巳': '长流水', '甲午': '沙中金', '乙未': '沙中金',
    '丙申': '山下火', '丁酉': '山下火', '戊戌': '平地木', '己亥': '平地木',
    '庚子': '壁上土', '辛丑': '壁上土', '壬寅': '金箔金', '癸卯': '金箔金',
    '甲辰': '覆灯火', '乙巳': '覆灯火', '丙午': '天河水', '丁未': '天河水',
    '戊申': '大驿土', '己酉': '大驿土', '庚戌': '钗钏金', '辛亥': '钗钏金',
    '壬子': '桑柘木', '癸丑': '桑柘木', '甲寅': '大溪水', '乙卯': '大溪水',
    '丙辰': '沙中土', '丁巳': '沙中土', '戊午': '天上火', '己未': '天上火',
    '庚申': '石榴木', '辛酉': '石榴木', '壬戌': '大海水', '癸亥': '大海水',
}

# 六冲表
CHONG_MAP = {
    '子': '午', '午': '子', '丑': '未', '未': '丑',
    '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
    '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳',
}

# 六合表
HE_MAP = {
    '子': '丑', '丑': '子', '寅': '亥', '亥': '寅',
    '卯': '戌', '戌': '卯', '辰': '酉', '酉': '辰',
    '巳': '申', '申': '巳', '午': '未', '未': '午',
}

# 三合表
SANHE_MAP = {
    '寅': ['午', '戌'], '午': ['寅', '戌'], '戌': ['寅', '午'],
    '亥': ['卯', '未'], '卯': ['亥', '未'], '未': ['亥', '卯'],
    '申': ['子', '辰'], '子': ['申', '辰'], '辰': ['申', '子'],
    '巳': ['酉', '丑'], '酉': ['巳', '丑'], '丑': ['巳', '酉'],
}

# 天干合表（五合）
STEM_HE_MAP = {
    '甲': '己', '己': '甲', '乙': '庚', '庚': '乙',
    '丙': '辛', '辛': '丙', '丁': '壬', '壬': '丁',
    '戊': '癸', '癸': '戊',
}


def get_wangshuai(stem, branch):
    """计算天干在地支上的旺衰状态"""
    order = WANGSHUAI_MAP.get(stem, [])
    if branch in order:
        idx = order.index(branch)
        return WANGSHUAI_NAMES[idx]
    return '平'


def get_nayin(gz):
    """获取干支纳音"""
    return NAYIN_MAP.get(gz, '未知')


def _get_relations(branch, all_branches):
    """计算地支与命局各地支的关系（冲、合、三合）"""
    relations = {'chong': [], 'he': [], 'sanhe': []}
    chong = CHONG_MAP.get(branch)
    he = HE_MAP.get(branch)
    sanhe = SANHE_MAP.get(branch, [])

    for b in all_branches:
        if b == branch:
            continue
        if chong and b == chong:
            relations['chong'].append(b)
        if he and b == he:
            relations['he'].append(b)
        if b in sanhe:
            relations['sanhe'].append(b)

    return relations


def _stem_relation(stem, day_stem):
    """计算天干与日主的十神关系"""
    if not stem or not day_stem:
        return ''
    return get_ten_god(day_stem, stem)


class FiveYunAnalyzer:
    """
    五运分析器 - 封装五运（感情、财、子、禄、寿）分析逻辑

    参数:
        luck_info: bazi_analyzer.py 中 analyze() 生成的 luck_info 字典，包含
                   'cycles'（大运数据）和 'yearly_predictions'（流年预测）
        pillars:   四柱数据（来自 calculate_four_pillars）
        gender:    性别 'male' | 'female' | 'unknown'
    """

    def __init__(self, luck_info, pillars, gender='unknown'):
        self.luck_info = luck_info
        self.pillars = pillars
        self.gender = gender
        self.day_stem = pillars['day_master']
        self.day_element = STEM_ELEMENTS[self.day_stem]

        # 命局地支列表（供关系计算）
        self.natal_branches = [
            pillars['year_pillar']['branch'],
            pillars['month_pillar']['branch'],
            pillars['day_pillar']['branch'],
            pillars['hour_pillar']['branch'],
        ]
        self.natal_stems = [
            pillars['year_pillar']['stem'],
            pillars['month_pillar']['stem'],
            pillars['day_pillar']['stem'],
            pillars['hour_pillar']['stem'],
        ]

    def get_recent_dayun(self, count=3):
        """
        获取近N个大运（以当前年份为基准，包含当前大运及后续）

        返回: 大运数据列表，每条包含 index, gz, stem, branch, age_start, age_end,
              year_start, year_end, wangshuai, nayin, ten_god, relations
        """
        current_year = datetime.date.today().year
        cycles = self.luck_info.get('cycles', {}).get('cycles', [])

        # 找到当前或即将到来的大运
        relevant = []
        for c in cycles:
            if c['year_end'] >= current_year - 5:
                relevant.append(c)
            if len(relevant) >= count:
                break

        enriched = []
        for c in relevant:
            enriched.append(self._enrich_dayun(c))
        return enriched

    def get_next_liunya(self, count=3):
        """
        获取接下来N年流年

        返回: 流年预测列表，每条包含 year, gz, fortune_score, fortune_desc, aspects
        """
        yearly = self.luck_info.get('yearly_predictions', [])
        current_year = datetime.date.today().year
        upcoming = [p for p in yearly if p['year'] >= current_year]
        return upcoming[:count]

    def _enrich_dayun(self, cycle):
        """丰富大运数据：补充旺衰、纳音、十神、干支关系"""
        stem = cycle['stem']
        branch = cycle['branch']
        gz = cycle['gz']

        wangshuai = get_wangshuai(stem, branch)
        nayin = get_nayin(gz)
        ten_god = _stem_relation(stem, self.day_stem)
        branch_ten_god = ''
        hidden = [s for s in HIDDEN_STEMS.get(branch, []) if s]
        if hidden:
            branch_ten_god = _stem_relation(hidden[0], self.day_stem)

        relations = _get_relations(branch, self.natal_branches)
        stem_rel = []
        if stem in STEM_HE_MAP and STEM_HE_MAP[stem] in self.natal_stems:
            stem_rel.append(f"天干{stem}合{STEM_HE_MAP[stem]}")

        enriched = dict(cycle)
        enriched.update({
            'wangshuai': wangshuai,
            'wangshuai_strength': WANGSHUAI_STRENGTH.get(wangshuai, '平'),
            'nayin': nayin,
            'ten_god': ten_god,
            'branch_ten_god': branch_ten_god,
            'branch_hidden': hidden,
            'relations': relations,
            'stem_relations': stem_rel,
        })
        return enriched

    def analyze_all_dimensions(self, dayun):
        """
        对单个大运进行五维度并行分析

        参数:
            dayun: 大运数据字典（来自 get_recent_dayun 的单条）
        返回:
            包含五个维度分析结果的字典
        """
        return {
            'intimate': self.analyze_intimate(dayun),
            'wealth': self.analyze_wealth(dayun),
            'children': self.analyze_children(dayun),
            'official': self.analyze_official(dayun),
            'longevity': self.analyze_longevity(dayun),
        }

    def analyze_intimate(self, dayun):
        """
        感情运分析 - 妻星/夫星在大运的表现

        男命：财星（正财/偏财）代表妻、情缘
        女命：官杀（正官/七杀）代表夫、情缘
        """
        stem = dayun.get('stem', '')
        branch = dayun.get('branch', '')
        gz = dayun.get('gz', '')
        ten_god = dayun.get('ten_god', '')
        relations = dayun.get('relations', {})
        wangshuai = dayun.get('wangshuai', '')
        nayin = dayun.get('nayin', '')

        # 确定感情星
        if self.gender == 'female':
            romance_gods = ['正官', '七杀']
            romance_label = '夫星'
        else:
            romance_gods = ['正财', '偏财']
            romance_label = '妻星'

        # 大运天干是否为感情星
        is_romance_stem = ten_god in romance_gods
        # 大运地支藏干是否含感情星
        hidden = dayun.get('branch_hidden', [])
        hidden_romance = [s for s in hidden if _stem_relation(s, self.day_stem) in romance_gods]

        score, desc, advice = self._score_intimate(
            ten_god, is_romance_stem, hidden_romance, relations, wangshuai
        )

        points = []
        if is_romance_stem:
            points.append(f"大运天干{stem}为{ten_god}，{romance_label}透出，感情机遇明显")
        if hidden_romance:
            points.append(f"地支{branch}藏{'/'.join(hidden_romance)}，{romance_label}暗藏，桃花深藏")
        if relations.get('he'):
            points.append(f"大运{branch}与命局{'/'.join(relations['he'])}相合，有情缘汇合之象")
        if relations.get('chong'):
            points.append(f"大运{branch}冲{'/'.join(relations['chong'])}，感情易有波折或分离")
        if relations.get('sanhe'):
            points.append(f"大运{branch}与{'/'.join(relations['sanhe'])}三合，人际桃花旺")
        if wangshuai in ['长生', '冠带', '临官', '帝旺']:
            points.append(f"大运处{wangshuai}，运势正旺，感情主动积极")
        elif wangshuai in ['衰', '病', '死', '绝']:
            points.append(f"大运处{wangshuai}，运势收敛，感情宜守不宜过于主动")

        return {
            'dimension': 'intimate',
            'label': '感情运',
            'dayun_gz': gz,
            'score': score,
            'overall': desc,
            'romance_label': romance_label,
            'is_romance_star_present': is_romance_stem or bool(hidden_romance),
            'key_points': points,
            'advice': advice,
            'wangshuai': wangshuai,
            'nayin': nayin,
        }

    def analyze_wealth(self, dayun):
        """
        财运分析 - 财星在大运的表现

        财星（正财/偏财）代表有形财富
        食神/伤官生财，为财之源头
        """
        stem = dayun.get('stem', '')
        branch = dayun.get('branch', '')
        gz = dayun.get('gz', '')
        ten_god = dayun.get('ten_god', '')
        relations = dayun.get('relations', {})
        wangshuai = dayun.get('wangshuai', '')
        nayin = dayun.get('nayin', '')
        stem_rels = dayun.get('stem_relations', [])

        wealth_gods = ['正财', '偏财']
        source_gods = ['食神', '伤官']
        drain_gods = ['比肩', '劫财']

        is_wealth = ten_god in wealth_gods
        is_source = ten_god in source_gods
        is_drain = ten_god in drain_gods

        hidden = dayun.get('branch_hidden', [])
        hidden_wealth = [s for s in hidden if _stem_relation(s, self.day_stem) in wealth_gods]
        hidden_source = [s for s in hidden if _stem_relation(s, self.day_stem) in source_gods]

        score, desc, advice = self._score_wealth(
            ten_god, is_wealth, is_source, is_drain, hidden_wealth, relations, wangshuai
        )

        points = []
        if is_wealth:
            points.append(f"大运天干{stem}为{ten_god}，财星透干，财运显露，收入有望增加")
        if is_source:
            points.append(f"大运天干{stem}为{ten_god}，食伤生财，靠才能变现，财运自然进账")
        if is_drain:
            points.append(f"大运天干{stem}为{ten_god}，比劫争财，财运受竞争影响，谨慎共财")
        if hidden_wealth:
            points.append(f"地支{branch}藏财星，偏财暗动，投资或副业有机遇")
        if hidden_source:
            points.append(f"地支{branch}藏食伤，财源从地支生发，偏财机遇有")
        if relations.get('he'):
            points.append(f"大运{branch}合{'/'.join(relations['he'])}，人脉助力财运")
        if relations.get('chong'):
            points.append(f"大运{branch}冲{'/'.join(relations['chong'])}，财运有动荡，需防破财")
        if wangshuai in ['长生', '冠带', '临官', '帝旺']:
            points.append(f"大运处{wangshuai}，运旺气盛，适合主动投资理财")
        if stem_rels:
            points.append(f"天干{stem_rels[0]}，有合化之机，财运或有转机")

        return {
            'dimension': 'wealth',
            'label': '财运',
            'dayun_gz': gz,
            'score': score,
            'overall': desc,
            'is_wealth_star_present': is_wealth or bool(hidden_wealth),
            'key_points': points,
            'advice': advice,
            'wangshuai': wangshuai,
            'nayin': nayin,
        }

    def analyze_children(self, dayun):
        """
        子运分析 - 子女星在大运的表现

        男命：食神/伤官代表子女（泄身之星）
        女命：官杀代表子女（克身之星，另说食神）
        """
        stem = dayun.get('stem', '')
        branch = dayun.get('branch', '')
        gz = dayun.get('gz', '')
        ten_god = dayun.get('ten_god', '')
        relations = dayun.get('relations', {})
        wangshuai = dayun.get('wangshuai', '')
        nayin = dayun.get('nayin', '')

        if self.gender == 'female':
            children_gods = ['正官', '七杀', '食神', '伤官']
            children_label = '子女星（官杀/食伤）'
        else:
            children_gods = ['食神', '伤官']
            children_label = '子女星（食伤）'

        is_children = ten_god in children_gods
        hidden = dayun.get('branch_hidden', [])
        hidden_children = [s for s in hidden if _stem_relation(s, self.day_stem) in children_gods]

        score, desc, advice = self._score_children(
            ten_god, is_children, hidden_children, relations, wangshuai
        )

        points = []
        if is_children:
            points.append(f"大运天干{stem}为{ten_god}，{children_label}透出，子女缘分深或子女有成就")
        if hidden_children:
            points.append(f"地支{branch}藏子女星，子女缘分潜藏，宜多关注子女教育")
        if relations.get('he'):
            points.append(f"大运{branch}合{'/'.join(relations['he'])}，子女关系融洽，有喜事机遇")
        if relations.get('chong'):
            points.append(f"大运{branch}冲{'/'.join(relations['chong'])}，与子女关系有变动，宜多沟通")
        if wangshuai in ['长生', '冠带', '临官', '帝旺']:
            points.append(f"大运处{wangshuai}，子女运旺，子女有贵人助力")
        elif wangshuai in ['衰', '病', '死', '绝']:
            points.append(f"大运处{wangshuai}，子女缘分需耐心经营，宜重视亲子互动")

        return {
            'dimension': 'children',
            'label': '子运',
            'dayun_gz': gz,
            'score': score,
            'overall': desc,
            'is_children_star_present': is_children or bool(hidden_children),
            'key_points': points,
            'advice': advice,
            'wangshuai': wangshuai,
            'nayin': nayin,
        }

    def analyze_official(self, dayun):
        """
        禄运分析 - 官禄、事业运在大运的表现

        正官/七杀代表官禄、事业
        食神/伤官发展才能，可转化为事业成就
        """
        stem = dayun.get('stem', '')
        branch = dayun.get('branch', '')
        gz = dayun.get('gz', '')
        ten_god = dayun.get('ten_god', '')
        relations = dayun.get('relations', {})
        wangshuai = dayun.get('wangshuai', '')
        nayin = dayun.get('nayin', '')
        stem_rels = dayun.get('stem_relations', [])

        official_gods = ['正官', '七杀']
        talent_gods = ['食神', '伤官']

        is_official = ten_god in official_gods
        is_talent = ten_god in talent_gods
        hidden = dayun.get('branch_hidden', [])
        hidden_official = [s for s in hidden if _stem_relation(s, self.day_stem) in official_gods]
        hidden_talent = [s for s in hidden if _stem_relation(s, self.day_stem) in talent_gods]

        score, desc, advice = self._score_official(
            ten_god, is_official, is_talent, hidden_official, relations, wangshuai
        )

        points = []
        if is_official:
            points.append(f"大运天干{stem}为{ten_god}，官星透出，职位晋升机会，上司赏识")
        if is_talent:
            points.append(f"大运天干{stem}为{ten_god}，食伤透出，发挥才华，创业或技艺有成")
        if hidden_official:
            points.append(f"地支{branch}藏官星，官禄暗动，职场有隐形升机")
        if hidden_talent:
            points.append(f"地支{branch}藏食伤，才能发挥机遇在地支")
        if relations.get('he'):
            points.append(f"大运{branch}合{'/'.join(relations['he'])}，有贵人相助，事业有助力")
        if relations.get('chong'):
            points.append(f"大运{branch}冲{'/'.join(relations['chong'])}，工作环境有变动，需主动应对")
        if wangshuai in ['临官', '帝旺']:
            points.append(f"大运处{wangshuai}，建禄/帝旺，事业正当其时，宜主动出击")
        if stem_rels:
            points.append(f"天干{stem_rels[0]}，上下有合，贵人助力或与领导关系融洽")

        return {
            'dimension': 'official',
            'label': '禄运',
            'dayun_gz': gz,
            'score': score,
            'overall': desc,
            'is_official_star_present': is_official or bool(hidden_official),
            'key_points': points,
            'advice': advice,
            'wangshuai': wangshuai,
            'nayin': nayin,
        }

    def analyze_longevity(self, dayun):
        """
        寿运分析 - 健康与寿元在大运的表现

        日主旺衰与大运的配合
        忌神大运损伤元气，用神大运扶持寿元
        五行偏枯影响对应脏腑
        """
        stem = dayun.get('stem', '')
        branch = dayun.get('branch', '')
        gz = dayun.get('gz', '')
        ten_god = dayun.get('ten_god', '')
        wangshuai = dayun.get('wangshuai', '')
        nayin = dayun.get('nayin', '')
        relations = dayun.get('relations', {})

        # 大运五行
        stem_element = STEM_ELEMENTS.get(stem, '')
        branch_element = BRANCH_ELEMENTS.get(branch, '')

        # 对日主的影响（印星生身为扶，财官泄耗）
        help_gods = ['正印', '偏印', '比肩', '劫财']
        drain_gods = ['正财', '偏财', '正官', '七杀', '食神', '伤官']

        is_help = ten_god in help_gods
        is_drain = ten_god in drain_gods

        score, desc, advice = self._score_longevity(
            ten_god, is_help, is_drain, wangshuai, stem_element, branch_element
        )

        # 脏腑对应（五行与健康）
        organ_map = {
            '木': '肝胆', '火': '心脏/小肠', '土': '脾胃',
            '金': '肺/大肠', '水': '肾/膀胱'
        }

        points = []
        if is_help:
            points.append(f"大运{ten_god}助身，元气得补，健康状态良好，寿元稳固")
        if is_drain:
            points.append(f"大运{ten_god}耗身，体能消耗较大，注意休息和养生")
        if wangshuai in ['长生', '冠带', '临官', '帝旺']:
            points.append(f"大运处{wangshuai}，生命力旺盛，抵抗力强")
        elif wangshuai in ['病', '死', '绝']:
            points.append(f"大运处{wangshuai}，体质相对薄弱，需注重保健预防")
        if stem_element in organ_map:
            points.append(f"大运天干五行为{stem_element}，宜关注{organ_map[stem_element]}健康")
        if relations.get('chong'):
            points.append(f"大运{branch}冲{'/'.join(relations['chong'])}，身体可能有应激反应，注意突发健康问题")

        return {
            'dimension': 'longevity',
            'label': '寿运',
            'dayun_gz': gz,
            'score': score,
            'overall': desc,
            'health_element': stem_element,
            'key_points': points,
            'advice': advice,
            'wangshuai': wangshuai,
            'nayin': nayin,
        }

    # ─── 内部评分函数 ──────────────────────────────────────────────────────────

    def _score_intimate(self, ten_god, is_romance, hidden_romance, relations, wangshuai):
        score = 50
        if self.gender == 'female':
            romance_gods = ['正官', '七杀']
        else:
            romance_gods = ['正财', '偏财']

        if is_romance:
            score += 25
            desc = '感情运旺盛，有缘分出现或关系深化'
        elif ten_god in ['食神', '伤官']:
            score += 10
            desc = '感情上主动表达，有桃花机遇'
        elif ten_god in ['比肩', '劫财']:
            score -= 10
            desc = '感情上有竞争压力，注意第三者'
        elif ten_god in ['七杀'] and self.gender != 'female':
            score -= 15
            desc = '感情易有波折，需更多耐心沟通'
        else:
            desc = '感情运平稳，维系既有关系为主'

        if hidden_romance:
            score += 10
        if relations.get('he'):
            score += 15
            desc += '，合局有情缘助力'
        if relations.get('chong'):
            score -= 15
        if wangshuai in ['长生', '冠带', '临官', '帝旺']:
            score += 5
        elif wangshuai in ['死', '绝']:
            score -= 10

        score = max(10, min(100, score))
        if score >= 75:
            overall = '✅ 感情运顺遂'
            advice = '感情机遇良好，把握缘分，积极互动，适合深化关系'
        elif score >= 55:
            overall = '☑️ 感情运稳定'
            advice = '感情整体稳定，注意细节经营，避免因小失大'
        elif score >= 40:
            overall = '⚠️ 感情运一般'
            advice = '感情需要耐心，避免冲动决策，多倾听对方需求'
        else:
            overall = '❌ 感情运需注意'
            advice = '此段大运感情多波折，宜低调处理情感事务，避免重大承诺'

        return score, overall, advice

    def _score_wealth(self, ten_god, is_wealth, is_source, is_drain, hidden_wealth, relations, wangshuai):
        score = 50
        if is_wealth:
            score += 25
            desc = '财星透出，财运显著，收入有望增加'
        elif is_source:
            score += 15
            desc = '食伤生财，靠才能变现，财运自然进账'
        elif is_drain:
            score -= 15
            desc = '比劫争财，财运受竞争影响，谨慎共财'
        elif ten_god in ['正官', '七杀']:
            score += 5
            desc = '官星临运，收入与地位挂钩，薪资有望提升'
        else:
            desc = '财运平稳，守成为主'

        if hidden_wealth:
            score += 10
        if relations.get('he'):
            score += 10
        if relations.get('chong'):
            score -= 10
        if wangshuai in ['临官', '帝旺']:
            score += 10
        elif wangshuai in ['死', '绝', '病']:
            score -= 10

        score = max(10, min(100, score))
        if score >= 75:
            overall = '✅ 财运旺盛'
            advice = '财运良好，适合投资扩张，但仍需量力而行，不可过于激进'
        elif score >= 55:
            overall = '☑️ 财运稳健'
            advice = '财运稳健，稳扎稳打，积累为主，可小额投资尝试'
        elif score >= 40:
            overall = '⚠️ 财运平平'
            advice = '财运一般，以守为攻，避免大额投资，防范破财风险'
        else:
            overall = '❌ 财运需防'
            advice = '财运较弱，谨慎理财，不宜冒险，避免被人拖累破财'

        return score, overall, advice

    def _score_children(self, ten_god, is_children, hidden_children, relations, wangshuai):
        score = 50
        if is_children:
            score += 20
            desc = '子女星透出，子女缘分深，有喜事或子女成就'
        elif ten_god in ['正印', '偏印']:
            score -= 5
            desc = '印星压食伤，子女缘分稍弱，宜关注子女健康'
        else:
            desc = '子女运平稳，亲子关系正常维系'

        if hidden_children:
            score += 10
        if relations.get('he'):
            score += 10
        if relations.get('chong'):
            score -= 15
        if wangshuai in ['长生', '冠带']:
            score += 5

        score = max(10, min(100, score))
        if score >= 70:
            overall = '✅ 子女缘深'
            advice = '子女缘分旺盛，多陪伴子女，关注成长教育，有共同发展机遇'
        elif score >= 50:
            overall = '☑️ 子女缘正常'
            advice = '亲子关系平稳，注重沟通交流，培养共同兴趣'
        else:
            overall = '⚠️ 子女运需关注'
            advice = '子女缘分需经营，关注子女健康与情绪，避免过度干涉'

        return score, overall, advice

    def _score_official(self, ten_god, is_official, is_talent, hidden_official, relations, wangshuai):
        score = 50
        if is_official:
            score += 25
            desc = '官星透干，职位有晋升机会，上司赏识'
        elif is_talent:
            score += 20
            desc = '食伤透干，才华发挥，适合创业或技艺展现'
        elif ten_god in ['正印', '偏印']:
            score += 10
            desc = '印星助身，贵人相助，学习进修有收获'
        elif ten_god in ['比肩', '劫财']:
            score -= 5
            desc = '比劫临运，同业竞争，需突出自身优势'
        else:
            desc = '事业运平稳，稳中求进'

        if hidden_official:
            score += 10
        if relations.get('he'):
            score += 10
        if relations.get('chong'):
            score -= 10
        if wangshuai in ['临官', '帝旺', '长生']:
            score += 10
        elif wangshuai in ['死', '绝']:
            score -= 10

        score = max(10, min(100, score))
        if score >= 75:
            overall = '✅ 禄运旺盛'
            advice = '事业运旺，主动把握机遇，积极争取晋升或扩展业务'
        elif score >= 55:
            overall = '☑️ 禄运稳健'
            advice = '事业稳健推进，脚踏实地，积累资历和人脉'
        elif score >= 40:
            overall = '⚠️ 禄运平平'
            advice = '事业需要耐心，避免急于求成，蓄势待发'
        else:
            overall = '❌ 禄运需防'
            advice = '事业有阻力，低调行事，巩固基础，待运势转好再出击'

        return score, overall, advice

    def _score_longevity(self, ten_god, is_help, is_drain, wangshuai, stem_element, branch_element):
        score = 60  # 健康基础分略高
        if is_help:
            score += 20
            desc = '印比助身，元气充足，健康状态良好'
        elif is_drain:
            score -= 15
            desc = '财官食伤耗身，体能消耗较大，注意养生'
        else:
            desc = '健康运平稳，注意日常保养'

        if wangshuai in ['长生', '冠带', '临官', '帝旺']:
            score += 10
        elif wangshuai in ['病', '死']:
            score -= 15
        elif wangshuai in ['绝']:
            score -= 20

        score = max(10, min(100, score))
        if score >= 75:
            overall = '✅ 健康运良好'
            advice = '此段大运健康状态佳，适合加强体能锻炼，保持良好生活习惯'
        elif score >= 55:
            overall = '☑️ 健康运平稳'
            advice = '健康平稳，注重规律作息，防微杜渐，定期体检'
        elif score >= 40:
            overall = '⚠️ 健康需关注'
            advice = '此段大运体质较弱，重视保健养生，避免过度劳累，注意情绪管理'
        else:
            overall = '❌ 健康运需谨慎'
            advice = '健康风险较高，宜全面体检，保守调养，避免高强度活动，及时就医'

        return score, overall, advice

    # ─── 摘要格式化 ────────────────────────────────────────────────────────────

    def build_summary_text(self, dayun_count=3, liunya_count=3):
        """
        生成五运摘要文字（用于主报告中的第八模块）

        参数:
            dayun_count:  近N个大运
            liunya_count: 接下来N年流年
        返回:
            摘要文字字符串
        """
        lines = []

        # 近几个大运概览
        recent_dayun = self.get_recent_dayun(dayun_count)
        lines.append(f"▶ 近{len(recent_dayun)}个大运概览：")
        for d in recent_dayun:
            strength = d.get('wangshuai_strength', '平')
            wangshuai = d.get('wangshuai', '')
            ten_god = d.get('ten_god', '')
            gz = d.get('gz', '')
            age_start = d.get('age_start', '')
            age_end = d.get('age_end', '')
            year_start = d.get('year_start', '')
            year_end = d.get('year_end', '')

            # 简要五运评估
            dims = self.analyze_all_dimensions(d)
            intimate_score = dims['intimate']['score']
            wealth_score = dims['wealth']['score']
            official_score = dims['official']['score']

            # 找出最强和最弱的维度
            scores = {
                '感情': intimate_score,
                '财运': wealth_score,
                '子运': dims['children']['score'],
                '禄运': official_score,
                '寿运': dims['longevity']['score'],
            }
            best_dim = max(scores, key=scores.get)
            worst_dim = min(scores, key=scores.get)

            lines.append(
                f"  • {age_start}岁 {gz}（{wangshuai}/{strength}）"
                f"  {year_start}-{year_end}年"
                f"  十神：{ten_god}"
            )
            lines.append(
                f"    优势：{best_dim}  ·  注意：{worst_dim}"
            )
            # 每个维度简评
            for dim_key, label in [
                ('intimate', '感情'), ('wealth', '财运'),
                ('children', '子运'), ('official', '禄运'), ('longevity', '寿运')
            ]:
                dim_data = dims[dim_key]
                lines.append(f"    {label}：{dim_data['overall']}")
            lines.append('')

        # 接下来几年流年展望
        next_liunya = self.get_next_liunya(liunya_count)
        if next_liunya:
            lines.append(f"▶ 接下来{len(next_liunya)}年流年展望：")
            current_year = datetime.date.today().year
            # 从luck_cycles找当前大运
            cycles = self.luck_info.get('cycles', {}).get('cycles', [])
            for pred in next_liunya:
                y = pred['year']
                gz = pred['gz']
                fd = pred.get('fortune_desc', '')
                aspects = pred.get('aspects', {})
                # 找对应大运
                cur_cycle = None
                for c in cycles:
                    if c['year_start'] <= y <= c['year_end']:
                        cur_cycle = c
                        break
                dayun_label = f"（{cur_cycle['gz']}运）" if cur_cycle else ''

                lines.append(f"  • {y}年 {gz}{dayun_label}")
                lines.append(f"    {fd}")
                if aspects:
                    career = aspects.get('career', '')
                    wealth = aspects.get('wealth', '')
                    love = aspects.get('love', '')
                    if career:
                        lines.append(f"    事业：{career}")
                    if wealth:
                        lines.append(f"    财运：{wealth}")
                    if love:
                        lines.append(f"    感情：{love}")
                lines.append('')

        # 注意事项
        lines.append("▶ 五运追踪提示：")
        lines.append("  可进一步追问任意大运的深度分析，例如：")
        lines.append("  「分析第1个大运的感情运」")
        lines.append("  「2026年流年财运如何」")
        lines.append("  「当前大运寿运分析」")

        return '\n'.join(lines)

    def build_summary_dict(self, dayun_count=3, liunya_count=3):
        """
        生成五运摘要结构化数据（用于 JSON 输出）
        """
        recent_dayun = self.get_recent_dayun(dayun_count)
        next_liunya = self.get_next_liunya(liunya_count)

        dayun_summaries = []
        for d in recent_dayun:
            dims = self.analyze_all_dimensions(d)
            dayun_summaries.append({
                'gz': d['gz'],
                'age_start': d['age_start'],
                'age_end': d['age_end'],
                'year_start': d['year_start'],
                'year_end': d['year_end'],
                'wangshuai': d['wangshuai'],
                'ten_god': d['ten_god'],
                'dimensions': {
                    k: {
                        'score': v['score'],
                        'overall': v['overall'],
                        'advice': v['advice'],
                    }
                    for k, v in dims.items()
                },
            })

        return {
            'recent_dayun': dayun_summaries,
            'next_liunya': [
                {
                    'year': p['year'],
                    'gz': p['gz'],
                    'fortune_desc': p.get('fortune_desc', ''),
                    'aspects': p.get('aspects', {}),
                }
                for p in next_liunya
            ],
        }
