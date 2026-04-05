"""
liuyue_liuri_analyzer.py - 流月流日逐级追踪分析模块

从大运/流年推导流月天干地支，从流月推导流日，
计算旺衰和干支关系，支持五维度深度分析。

追踪链：大运 → 流年 → 流月 → 流日
"""

import datetime
import calendar

from .ganzhi_calculator import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENTS, BRANCH_ELEMENTS,
    HIDDEN_STEMS, STEM_POLARITY, GENERATES, CONTROLS,
    MONTH_STEM_START, MONTH_BRANCH_ORDER,
)
from .ten_gods_analyzer import get_ten_god
from .five_yun_analyzer import (
    get_wangshuai, get_nayin, WANGSHUAI_STRENGTH,
    CHONG_MAP, HE_MAP, SANHE_MAP, STEM_HE_MAP,
    _stem_relation, _get_relations,
)

# ─── 流月推算常量 ─────────────────────────────────────────────────────────────

# 月支顺序（寅=正月，卯=二月...）
LIUYUE_BRANCH_ORDER = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']

# 公历月份 → 流月地支序号（0-based，0=寅月，以节气近似）
SOLAR_MONTH_TO_BRANCH_IDX = {
    1: 11,  2: 0,  3: 1,  4: 2,  5: 3,  6: 4,
    7: 5,   8: 6,  9: 7, 10: 8, 11: 9, 12: 10,
}

# 流日推算参考：1900年1月1日为甲戌日
_REF_JULIAN_DAY_STEM_IDX   = 0   # 甲
_REF_JULIAN_DAY_BRANCH_IDX = 10  # 戌


def _julian_day(year, month, day):
    """计算儒略日数（与 ganzhi_calculator 中相同，避免循环导入）"""
    if month <= 2:
        year -= 1
        month += 12
    a = int(year / 100)
    b = 2 - a + int(a / 4)
    return (int(365.25 * (year + 4716))
            + int(30.6001 * (month + 1))
            + day + b - 1524)


# ─── 流月干支计算 ─────────────────────────────────────────────────────────────

def get_liuyue_ganzhi(year, month):
    """
    计算指定年月的流月干支（以节气近似月份为界）

    参数:
        year:  公历年份 (int)
        month: 公历月份 1-12 (int)
    返回:
        dict 包含 stem, branch, gz, stem_element, branch_element,
                  hidden_stems, wangshuai, nayin
    """
    # 流年天干（用于五虎遁年起月法）
    year_stem_idx = (year - 4) % 10
    year_stem = HEAVENLY_STEMS[year_stem_idx]

    # 流月地支序号
    branch_idx = SOLAR_MONTH_TO_BRANCH_IDX.get(month, 0)
    branch = LIUYUE_BRANCH_ORDER[branch_idx]

    # 流月天干（五虎遁年起月法）
    stem_start = MONTH_STEM_START.get(year_stem, 0)
    stem_idx = (stem_start + branch_idx) % 10
    stem = HEAVENLY_STEMS[stem_idx]

    gz = stem + branch
    hidden = [s for s in HIDDEN_STEMS.get(branch, []) if s]
    wangshuai = get_wangshuai(stem, branch)
    nayin = get_nayin(gz)

    return {
        'year':           year,
        'month':          month,
        'stem':           stem,
        'branch':         branch,
        'gz':             gz,
        'stem_element':   STEM_ELEMENTS[stem],
        'branch_element': BRANCH_ELEMENTS[branch],
        'hidden_stems':   hidden,
        'wangshuai':      wangshuai,
        'wangshuai_strength': WANGSHUAI_STRENGTH.get(wangshuai, '平'),
        'nayin':          nayin,
    }


# ─── 流日干支计算 ─────────────────────────────────────────────────────────────

def get_liuri_ganzhi(year, month, day):
    """
    计算指定日期的流日干支

    参数:
        year:  公历年份 (int)
        month: 公历月份 1-12 (int)
        day:   公历日期 1-31 (int)
    返回:
        dict 包含 stem, branch, gz, stem_element, branch_element,
                  hidden_stems, wangshuai, nayin
    """
    ref_jd = _julian_day(1900, 1, 1)
    cur_jd = _julian_day(year, month, day)
    diff = cur_jd - ref_jd

    stem_idx   = (_REF_JULIAN_DAY_STEM_IDX   + diff) % 10
    branch_idx = (_REF_JULIAN_DAY_BRANCH_IDX + diff) % 12

    stem   = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]
    gz = stem + branch
    hidden = [s for s in HIDDEN_STEMS.get(branch, []) if s]
    wangshuai = get_wangshuai(stem, branch)
    nayin = get_nayin(gz)

    return {
        'year':           year,
        'month':          month,
        'day':            day,
        'stem':           stem,
        'branch':         branch,
        'gz':             gz,
        'stem_element':   STEM_ELEMENTS[stem],
        'branch_element': BRANCH_ELEMENTS[branch],
        'hidden_stems':   hidden,
        'wangshuai':      wangshuai,
        'wangshuai_strength': WANGSHUAI_STRENGTH.get(wangshuai, '平'),
        'nayin':          nayin,
    }


# ─── 主分析器类 ───────────────────────────────────────────────────────────────

class LiuyueLiuriAnalyzer:
    """
    流月流日逐级追踪分析器

    从流年推导流月，从流月推导流日，
    计算旺衰和干支关系，支持五维度深度分析。

    参数:
        pillars: 四柱数据（来自 calculate_four_pillars）
        gender:  性别 'male' | 'female' | 'unknown'
    """

    def __init__(self, pillars, gender='unknown'):
        self.pillars = pillars
        self.gender = gender
        self.day_stem = pillars['day_master']
        self.day_element = STEM_ELEMENTS[self.day_stem]

        # 命局地支列表
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

    # ─── 公共接口 ──────────────────────────────────────────────────────────────

    def get_liuyue_for_month(self, year, month):
        """
        获取指定年月的流月数据，并补充与命局的关系信息

        参数:
            year:  公历年份
            month: 公历月份 (1-12)
        返回:
            流月数据字典（含干支、旺衰、纳音、十神、关系）
        """
        liuyue = get_liuyue_ganzhi(year, month)
        return self._enrich(liuyue)

    # Keep backward-compatible alias
    def get_liuyue_for_year(self, year, month):
        """Alias for get_liuyue_for_month (backward compatibility)."""
        return self.get_liuyue_for_month(year, month)

    def get_liuri_for_date(self, year, month, day):
        """
        获取指定日期的流日数据，并补充与命局的关系信息

        参数:
            year:  公历年份
            month: 公历月份 (1-12)
            day:   公历日期 (1-31)
        返回:
            流日数据字典（含干支、旺衰、纳音、十神、关系）
        """
        liuri = get_liuri_ganzhi(year, month, day)
        return self._enrich(liuri)

    def get_liuyue_list_for_year(self, year, months=None):
        """
        获取某年的多个流月列表（默认全年12个月）

        参数:
            year:   公历年份
            months: 指定月份列表（如 [1,2,3]），None 表示全年
        返回:
            流月数据列表
        """
        if months is None:
            months = list(range(1, 13))
        return [self.get_liuyue_for_month(year, m) for m in months]

    def analyze_liuyue(self, year, month, dimension=None):
        """
        分析指定年月的流月运势

        参数:
            year:      公历年份
            month:     公历月份 (1-12)
            dimension: 'intimate'|'wealth'|'children'|'official'|'longevity'|None（全部）
        返回:
            包含分析结果的字典
        """
        liuyue = self.get_liuyue_for_month(year, month)

        if dimension is None:
            return {
                'period': liuyue,
                'period_type': 'liuyue',
                'dimensions': self._analyze_all(liuyue),
            }

        return {
            'period': liuyue,
            'period_type': 'liuyue',
            'dimension': dimension,
            'result': self._analyze_dimension(liuyue, dimension),
        }

    def analyze_liuri(self, year, month, day, dimension=None):
        """
        分析指定日期的流日运势

        参数:
            year:      公历年份
            month:     公历月份 (1-12)
            day:       公历日期 (1-31)
            dimension: 'intimate'|'wealth'|'children'|'official'|'longevity'|None（全部）
        返回:
            包含分析结果的字典
        """
        liuri = self.get_liuri_for_date(year, month, day)

        if dimension is None:
            return {
                'period': liuri,
                'period_type': 'liuri',
                'dimensions': self._analyze_all(liuri),
            }

        return {
            'period': liuri,
            'period_type': 'liuri',
            'dimension': dimension,
            'result': self._analyze_dimension(liuri, dimension),
        }

    def find_best_months(self, year, dimension):
        """
        找出某年中指定维度最佳的流月

        参数:
            year:      公历年份
            dimension: 维度名称
        返回:
            按评分排序的流月列表（最高在前）
        """
        months_data = []
        for month in range(1, 13):
            liuyue = self.get_liuyue_for_month(year, month)
            result = self._analyze_dimension(liuyue, dimension)
            months_data.append({
                'month': month,
                'gz': liuyue['gz'],
                'wangshuai': liuyue['wangshuai'],
                'score': result.get('score', 50),
                'overall': result.get('overall', ''),
            })
        return sorted(months_data, key=lambda x: x['score'], reverse=True)

    def find_best_days(self, year, month, dimension):
        """
        找出某月中指定维度最佳的流日

        参数:
            year:      公历年份
            month:     公历月份
            dimension: 维度名称
        返回:
            按评分排序的流日列表（最高在前，取前10日）
        """
        _, days_in_month = calendar.monthrange(year, month)
        days_data = []

        for day in range(1, days_in_month + 1):
            liuri = self.get_liuri_for_date(year, month, day)
            result = self._analyze_dimension(liuri, dimension)
            days_data.append({
                'day': day,
                'gz': liuri['gz'],
                'wangshuai': liuri['wangshuai'],
                'score': result.get('score', 50),
                'overall': result.get('overall', ''),
            })

        return sorted(days_data, key=lambda x: x['score'], reverse=True)[:10]

    def format_liuyue_report(self, year, dimension=None):
        """
        生成某年全年流月分析文字报告

        参数:
            year:      公历年份
            dimension: 指定维度（None 则输出综合概述）
        返回:
            文字报告字符串
        """
        lines = []
        dim_label = {
            'intimate': '感情运', 'wealth': '财运', 'children': '子运',
            'official': '禄运', 'longevity': '寿运',
        }.get(dimension, '综合运势')

        lines.append(f"▶ {year}年全年流月{dim_label}分析")
        lines.append('─' * 44)

        for month in range(1, 13):
            liuyue = self.get_liuyue_for_month(year, month)
            gz = liuyue['gz']
            wangshuai = liuyue['wangshuai']
            ten_god = liuyue.get('ten_god', '')

            if dimension:
                result = self._analyze_dimension(liuyue, dimension)
                score = result.get('score', 50)
                overall = result.get('overall', '')
                bar = '▓' * (score // 20) + '░' * (5 - score // 20)
                lines.append(f"  {month:2d}月 {gz}（{wangshuai}，{ten_god}）  [{bar}] {overall}")
            else:
                lines.append(f"  {month:2d}月 {gz}（{wangshuai}，{ten_god}）  旺衰：{liuyue['wangshuai_strength']}")

        if dimension:
            lines.append('')
            best = self.find_best_months(year, dimension)[0]
            lines.append(f"  ✅ 最佳月份：{best['month']}月（{best['gz']}，评分{best['score']}）")

        return '\n'.join(lines)

    def format_liuri_report(self, year, month, dimension=None):
        """
        生成某月全月流日分析文字报告（仅列出最佳日期）

        参数:
            year:      公历年份
            month:     公历月份
            dimension: 指定维度
        返回:
            文字报告字符串
        """
        lines = []
        dim_label = {
            'intimate': '感情运', 'wealth': '财运', 'children': '子运',
            'official': '禄运', 'longevity': '寿运',
        }.get(dimension, '综合运势')

        lines.append(f"▶ {year}年{month}月流日{dim_label}分析（最佳日期）")
        lines.append('─' * 44)

        dim = dimension or 'official'
        best_days = self.find_best_days(year, month, dim)

        for d in best_days[:7]:
            bar = '▓' * (d['score'] // 20) + '░' * (5 - d['score'] // 20)
            lines.append(
                f"  {month}月{d['day']:2d}日 {d['gz']}（{d['wangshuai']}）  "
                f"[{bar}] {d['overall']}"
            )

        return '\n'.join(lines)

    # ─── 内部方法 ──────────────────────────────────────────────────────────────

    def _enrich(self, period_data):
        """补充干支关系信息（十神、与命局关系）"""
        stem = period_data['stem']
        branch = period_data['branch']

        ten_god = _stem_relation(stem, self.day_stem)
        branch_ten_god = ''
        hidden = period_data.get('hidden_stems', [])
        if hidden:
            branch_ten_god = _stem_relation(hidden[0], self.day_stem)

        relations = _get_relations(branch, self.natal_branches)
        stem_rels = []
        if stem in STEM_HE_MAP and STEM_HE_MAP[stem] in self.natal_stems:
            stem_rels.append(f"天干{stem}合{STEM_HE_MAP[stem]}")

        enriched = dict(period_data)
        enriched.update({
            'ten_god': ten_god,
            'branch_ten_god': branch_ten_god,
            'relations': relations,
            'stem_relations': stem_rels,
        })
        return enriched

    def _analyze_all(self, period_data):
        """五维度全面分析"""
        return {
            'intimate':  self._analyze_dimension(period_data, 'intimate'),
            'wealth':    self._analyze_dimension(period_data, 'wealth'),
            'children':  self._analyze_dimension(period_data, 'children'),
            'official':  self._analyze_dimension(period_data, 'official'),
            'longevity': self._analyze_dimension(period_data, 'longevity'),
        }

    def _analyze_dimension(self, period_data, dimension):
        """单维度分析（复用 five_yun_analyzer 的评分逻辑）"""
        ten_god = period_data.get('ten_god', '')
        relations = period_data.get('relations', {})
        wangshuai = period_data.get('wangshuai', '')
        hidden = period_data.get('hidden_stems', [])
        stem = period_data.get('stem', '')
        branch = period_data.get('branch', '')
        gz = period_data.get('gz', '')
        nayin = period_data.get('nayin', '')

        if dimension == 'intimate':
            return self._analyze_intimate(ten_god, hidden, relations, wangshuai, gz, nayin)
        elif dimension == 'wealth':
            return self._analyze_wealth(ten_god, hidden, relations, wangshuai, gz, nayin)
        elif dimension == 'children':
            return self._analyze_children(ten_god, hidden, relations, wangshuai, gz, nayin)
        elif dimension == 'official':
            return self._analyze_official(ten_god, hidden, relations, wangshuai, gz, nayin)
        elif dimension == 'longevity':
            stem_element = STEM_ELEMENTS.get(stem, '')
            return self._analyze_longevity(ten_god, wangshuai, stem_element, relations, gz, nayin)
        else:
            return {'score': 50, 'overall': '分析维度未知', 'advice': '', 'key_points': []}

    def _analyze_intimate(self, ten_god, hidden, relations, wangshuai, gz, nayin):
        if self.gender == 'female':
            romance_gods = ['正官', '七杀']
        else:
            romance_gods = ['正财', '偏财']

        is_romance = ten_god in romance_gods
        hidden_romance = [s for s in hidden if _stem_relation(s, self.day_stem) in romance_gods]

        score = 50
        points = []

        if is_romance:
            score += 25
            points.append(f"十神为{ten_god}，情缘星透出，感情机遇明显")
        elif ten_god in ['食神', '伤官']:
            score += 10
            points.append("食伤临期，桃花活跃，主动表达感情")
        elif ten_god in ['比肩', '劫财']:
            score -= 10
            points.append("比劫临期，感情有竞争，注意第三者")

        if hidden_romance:
            score += 10
            points.append("地支藏情缘星，感情机遇暗藏")
        if relations.get('he'):
            score += 15
            points.append(f"与命局{'/'.join(relations['he'])}相合，有情缘汇合")
        if relations.get('chong'):
            score -= 15
            points.append(f"冲{'/'.join(relations['chong'])}，感情易有波折")
        if relations.get('sanhe'):
            score += 5
            points.append("三合助力，人缘旺盛，桃花有机会")
        if wangshuai in ['临官', '帝旺', '长生']:
            score += 5
        elif wangshuai in ['死', '绝']:
            score -= 10

        score = max(10, min(100, score))
        overall, advice = self._score_to_text(score, '感情运', '感情')
        return {'score': score, 'overall': overall, 'advice': advice,
                'key_points': points, 'period_gz': gz, 'nayin': nayin}

    def _analyze_wealth(self, ten_god, hidden, relations, wangshuai, gz, nayin):
        wealth_gods = ['正财', '偏财']
        source_gods = ['食神', '伤官']
        drain_gods  = ['比肩', '劫财']

        is_wealth  = ten_god in wealth_gods
        is_source  = ten_god in source_gods
        is_drain   = ten_god in drain_gods
        hidden_wealth = [s for s in hidden if _stem_relation(s, self.day_stem) in wealth_gods]

        score = 50
        points = []

        if is_wealth:
            score += 25
            points.append(f"十神为{ten_god}，财星透出，收入增加机遇")
        elif is_source:
            score += 15
            points.append("食伤临期，靠才能赚钱，财运自然进账")
        elif is_drain:
            score -= 15
            points.append("比劫临期，财运受竞争影响，谨慎共财破财")
        if hidden_wealth:
            score += 10
            points.append("地支藏财星，偏财机遇暗动")
        if relations.get('he'):
            score += 10
            points.append("合局，贵人助财运")
        if relations.get('chong'):
            score -= 10
            points.append("冲命局，财运有动荡，防破财")
        if wangshuai in ['临官', '帝旺']:
            score += 10
        elif wangshuai in ['死', '绝', '病']:
            score -= 10

        score = max(10, min(100, score))
        overall, advice = self._score_to_text(score, '财运', '财运')
        return {'score': score, 'overall': overall, 'advice': advice,
                'key_points': points, 'period_gz': gz, 'nayin': nayin}

    def _analyze_children(self, ten_god, hidden, relations, wangshuai, gz, nayin):
        if self.gender == 'female':
            children_gods = ['正官', '七杀', '食神', '伤官']
        else:
            children_gods = ['食神', '伤官']

        is_children = ten_god in children_gods
        hidden_children = [s for s in hidden if _stem_relation(s, self.day_stem) in children_gods]

        score = 50
        points = []

        if is_children:
            score += 20
            points.append(f"十神为{ten_god}，子女星透出，子女缘分旺或有喜事")
        if hidden_children:
            score += 10
            points.append("地支藏子女星，子女缘潜藏")
        if ten_god in ['正印', '偏印']:
            score -= 5
            points.append("印星压食伤，子女缘稍弱")
        if relations.get('he'):
            score += 10
            points.append("合局，亲子关系融洽，有喜事机遇")
        if relations.get('chong'):
            score -= 15
            points.append("冲命局，子女关系有变动")

        score = max(10, min(100, score))
        overall, advice = self._score_to_text(score, '子运', '子女运')
        return {'score': score, 'overall': overall, 'advice': advice,
                'key_points': points, 'period_gz': gz, 'nayin': nayin}

    def _analyze_official(self, ten_god, hidden, relations, wangshuai, gz, nayin):
        official_gods = ['正官', '七杀']
        talent_gods   = ['食神', '伤官']
        hidden_official = [s for s in hidden if _stem_relation(s, self.day_stem) in official_gods]
        hidden_talent   = [s for s in hidden if _stem_relation(s, self.day_stem) in talent_gods]

        score = 50
        points = []

        if ten_god in official_gods:
            score += 25
            points.append(f"十神为{ten_god}，官星透出，职场机遇明显")
        elif ten_god in talent_gods:
            score += 20
            points.append("食伤临期，才华发挥，创意事业有成")
        elif ten_god in ['正印', '偏印']:
            score += 10
            points.append("印星临期，贵人相助，学习进修有收获")
        elif ten_god in ['比肩', '劫财']:
            score -= 5
            points.append("比劫临期，同业竞争增加")
        if hidden_official:
            score += 10
            points.append("地支藏官星，职场机遇暗动")
        if hidden_talent:
            score += 5
            points.append("地支藏食伤，才能发挥机遇在暗处")
        if relations.get('he'):
            score += 10
            points.append("合局，贵人助力事业")
        if relations.get('chong'):
            score -= 10
            points.append("冲命局，工作环境有变动")
        if wangshuai in ['临官', '帝旺', '长生']:
            score += 10
        elif wangshuai in ['死', '绝']:
            score -= 10

        score = max(10, min(100, score))
        overall, advice = self._score_to_text(score, '禄运', '事业运')
        return {'score': score, 'overall': overall, 'advice': advice,
                'key_points': points, 'period_gz': gz, 'nayin': nayin}

    def _analyze_longevity(self, ten_god, wangshuai, stem_element, relations, gz, nayin):
        help_gods  = ['正印', '偏印', '比肩', '劫财']
        drain_gods = ['正财', '偏财', '正官', '七杀', '食神', '伤官']

        is_help  = ten_god in help_gods
        is_drain = ten_god in drain_gods

        score = 60
        points = []

        if is_help:
            score += 20
            points.append(f"十神为{ten_god}，助身元气，健康状态良好")
        elif is_drain:
            score -= 15
            points.append(f"十神为{ten_god}，耗身，体能消耗较大，注意养生")
        if wangshuai in ['长生', '冠带', '临官', '帝旺']:
            score += 10
            points.append(f"流期处{wangshuai}，生命力旺盛")
        elif wangshuai in ['病', '死']:
            score -= 15
            points.append(f"流期处{wangshuai}，体质相对薄弱，需重视保健")
        elif wangshuai in ['绝']:
            score -= 20
            points.append("流期处绝，精力较弱，谨慎劳累")
        if relations.get('chong'):
            score -= 10
            points.append("冲命局，身体可能有应激反应，注意突发健康问题")

        score = max(10, min(100, score))
        overall, advice = self._score_to_text(score, '寿运', '健康')
        return {'score': score, 'overall': overall, 'advice': advice,
                'key_points': points, 'period_gz': gz, 'nayin': nayin}

    @staticmethod
    def _score_to_text(score, dim_label, aspect_label):
        """将评分转换为整体描述和建议文字"""
        if score >= 75:
            overall = f'✅ {dim_label}顺遂'
            advice = f'此期间{aspect_label}良好，主动把握机遇'
        elif score >= 55:
            overall = f'☑️ {dim_label}稳健'
            advice = f'此期间{aspect_label}平稳，稳中求进'
        elif score >= 40:
            overall = f'⚠️ {dim_label}一般'
            advice = f'此期间{aspect_label}需耐心，避免冲动'
        else:
            overall = f'❌ {dim_label}需谨慎'
            advice = f'此期间{aspect_label}多波折，低调行事'
        return overall, advice
