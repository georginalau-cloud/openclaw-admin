"""
[11] lib/ten_gods_analyzer.py - 十神分析模块
调用层级：被 bin/bazi 调用（分析层第一步）
依赖：lib/ganzhi_calculator.py [03]

根据日主（日干）与其他干支的五行生克关系，计算十神，
并分析对应的性格特征。
"""

from .ganzhi_calculator import (
    STEM_ELEMENTS, STEM_POLARITY, BRANCH_ELEMENTS,
    HIDDEN_STEMS, HEAVENLY_STEMS
)

# 五行生克关系
GENERATES = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
CONTROLS  = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}

# 反向查找：谁生我，谁克我
def _who_generates(element):
    """返回生该五行的五行"""
    for k, v in GENERATES.items():
        if v == element:
            return k
    return None

def _who_controls(element):
    """返回克该五行的五行"""
    for k, v in CONTROLS.items():
        if v == element:
            return k
    return None


def get_ten_god(day_stem, other_stem):
    """
    计算日主与另一天干之间的十神关系
    参数:
        day_stem: 日主天干（如'甲'）
        other_stem: 另一天干（如'丙'）
    返回: 十神名称字符串
    """
    if day_stem == other_stem:
        return '比肩'

    day_element  = STEM_ELEMENTS[day_stem]
    other_element = STEM_ELEMENTS[other_stem]
    day_polarity = STEM_POLARITY[day_stem]
    other_polarity = STEM_POLARITY[other_stem]

    same_polarity = (day_polarity == other_polarity)

    # 比劫：同五行，异阴阳
    if day_element == other_element:
        return '比肩' if same_polarity else '劫财'

    # 食伤：日主生出的五行
    if GENERATES.get(day_element) == other_element:
        return '食神' if same_polarity else '伤官'

    # 财星：日主克制的五行
    if CONTROLS.get(day_element) == other_element:
        return '偏财' if same_polarity else '正财'

    # 官杀：克日主的五行
    if CONTROLS.get(other_element) == day_element:
        return '七杀' if same_polarity else '正官'

    # 印星：生日主的五行
    if GENERATES.get(other_element) == day_element:
        return '偏印' if same_polarity else '正印'

    return '未知'


def get_ten_god_from_element(day_stem, other_element, other_polarity):
    """
    通过五行和阴阳计算十神（用于地支藏干）
    """
    day_element = STEM_ELEMENTS[day_stem]
    day_polarity = STEM_POLARITY[day_stem]
    same_polarity = (day_polarity == other_polarity)

    if day_element == other_element:
        return '比肩' if same_polarity else '劫财'
    if GENERATES.get(day_element) == other_element:
        return '食神' if same_polarity else '伤官'
    if CONTROLS.get(day_element) == other_element:
        return '偏财' if same_polarity else '正财'
    if CONTROLS.get(other_element) == day_element:
        return '七杀' if same_polarity else '正官'
    if GENERATES.get(other_element) == day_element:
        return '偏印' if same_polarity else '正印'
    return '未知'


def analyze_ten_gods(pillars):
    """
    分析命局所有柱的十神关系
    返回包含各柱十神信息的字典
    """
    day_stem = pillars['day_master']
    result = {}

    pillar_names = {
        'year_pillar': '年柱',
        'month_pillar': '月柱',
        'day_pillar': '日柱',
        'hour_pillar': '时柱',
    }

    for pillar_key, pillar_label in pillar_names.items():
        p = pillars[pillar_key]
        stem = p['stem']
        branch = p['branch']

        # 天干十神（日柱天干为日主本身，不计算）
        if pillar_key == 'day_pillar':
            stem_ten_god = '日主'
        else:
            stem_ten_god = get_ten_god(day_stem, stem)

        # 地支藏干十神
        hidden = HIDDEN_STEMS[branch]
        hidden_ten_gods = []
        for h_stem in hidden:
            if h_stem:
                tg = get_ten_god(day_stem, h_stem)
                hidden_ten_gods.append({'stem': h_stem, 'ten_god': tg})

        result[pillar_key] = {
            'label': pillar_label,
            'stem': stem,
            'branch': branch,
            'stem_ten_god': stem_ten_god,
            'branch_hidden': hidden_ten_gods,
        }

    return result


def get_dominant_ten_gods(ten_gods_analysis):
    """
    统计命局中各十神出现次数（天干权重2，藏干主气权重2，余气权重1）
    返回排序后的十神列表
    """
    counts = {}
    weight_map = {0: 2, 1: 1, 2: 1}  # 主气权重2，中气余气权重1

    for pillar_key, data in ten_gods_analysis.items():
        # 天干十神（日主不计）
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg and stem_tg != '日主':
            counts[stem_tg] = counts.get(stem_tg, 0) + 2

        # 藏干十神
        for i, hidden in enumerate(data.get('branch_hidden', [])):
            tg = hidden.get('ten_god', '')
            if tg:
                w = weight_map.get(i, 1)
                counts[tg] = counts.get(tg, 0) + w

    return sorted(counts.items(), key=lambda x: x[1], reverse=True)


def identify_key_stars(ten_gods_analysis, pillars):
    """
    识别关键神星：正官、七杀、正印、偏印、正财、偏财、食神、伤官
    特别关注月令（格局）
    """
    month_pillar = ten_gods_analysis.get('month_pillar', {})
    month_hidden = month_pillar.get('branch_hidden', [])

    # 月令主气（格局的核心）
    month_lord = None
    if month_hidden:
        month_lord = month_hidden[0]  # 主气

    key_stars = {
        'month_lord': month_lord,
        'has_zheng_guan': False,
        'has_qi_sha': False,
        'has_zheng_yin': False,
        'has_pian_yin': False,
        'has_zheng_cai': False,
        'has_pian_cai': False,
        'has_shi_shen': False,
        'has_shang_guan': False,
    }

    ten_god_map = {
        '正官': 'has_zheng_guan',
        '七杀': 'has_qi_sha',
        '正印': 'has_zheng_yin',
        '偏印': 'has_pian_yin',
        '正财': 'has_zheng_cai',
        '偏财': 'has_pian_cai',
        '食神': 'has_shi_shen',
        '伤官': 'has_shang_guan',
    }

    for pillar_key, data in ten_gods_analysis.items():
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg in ten_god_map:
            key_stars[ten_god_map[stem_tg]] = True

        for hidden in data.get('branch_hidden', []):
            tg = hidden.get('ten_god', '')
            if tg in ten_god_map:
                key_stars[ten_god_map[tg]] = True

    return key_stars
