"""
format_analyzer.py - 格局判断模块

根据月令藏干、天干透出情况判断命局格局，
并辨别日主强弱，取用神和忌神。

参考《子平真诠》：八字用神，专求月令。
"""

from .ganzhi_calculator import (
    STEM_ELEMENTS, BRANCH_ELEMENTS, HIDDEN_STEMS,
    GENERATES, get_daymaster_strength
)

# 格局名称映射（月令主气十神 -> 格局名）
FORMAT_NAME_MAP = {
    '正官': '正官格',
    '七杀': '偏官格（七杀格）',
    '正印': '印绶格（正印格）',
    '偏印': '偏印格（枭神格）',
    '正财': '正财格',
    '偏财': '偏财格',
    '食神': '食神格',
    '伤官': '伤官格',
    '比肩': '建禄格',
    '劫财': '月劫格',
}

CONTROLS = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}


def determine_format(pillars, ten_gods_analysis):
    """
    判断命局格局
    《子平真诠》：以月令地支藏干为基础，看哪个藏干透出天干成为格局
    返回格局分析字典
    """
    month_branch = pillars['month_pillar']['branch']
    month_hidden = HIDDEN_STEMS[month_branch]

    # 月令藏干（主气、中气、余气）
    month_lord = month_hidden[0] if month_hidden[0] else None

    # 检查月令藏干是否透出天干（年干、月干、时干）
    transparent_stems = [
        pillars['year_pillar']['stem'],
        pillars['month_pillar']['stem'],
        pillars['hour_pillar']['stem'],
    ]

    # 找出哪个藏干透出
    format_ten_god = None
    format_source = None

    for hidden_stem in month_hidden:
        if hidden_stem and hidden_stem in transparent_stems:
            # 该藏干已透出，成格
            month_data = ten_gods_analysis.get('month_pillar', {})
            for hd in month_data.get('branch_hidden', []):
                if hd['stem'] == hidden_stem:
                    format_ten_god = hd['ten_god']
                    format_source = f"月令{month_branch}中{hidden_stem}透出"
                    break
            if format_ten_god:
                break

    # 若无透出，以月令主气定格
    if not format_ten_god and month_lord:
        month_data = ten_gods_analysis.get('month_pillar', {})
        for hd in month_data.get('branch_hidden', []):
            if hd['stem'] == month_lord:
                format_ten_god = hd['ten_god']
                format_source = f"月令{month_branch}主气{month_lord}定格"
                break

    format_name = FORMAT_NAME_MAP.get(format_ten_god, f'{format_ten_god}格' if format_ten_god else '杂气格')

    # 检查是否为从格
    cong_ge = _check_cong_ge(pillars, ten_gods_analysis)

    return {
        'format_name': cong_ge['name'] if cong_ge else format_name,
        'format_ten_god': format_ten_god,
        'format_source': format_source,
        'is_cong_ge': cong_ge is not None,
        'cong_ge_detail': cong_ge,
        'month_branch': month_branch,
        'month_lord': month_lord,
    }


def _check_cong_ge(pillars, ten_gods_analysis):
    """
    检查是否为从格
    从格条件：日主极弱，且某一类十神极旺（占4个以上位置）
    """
    strength = get_daymaster_strength(pillars)
    if strength != '弱':
        return None

    # 统计各类十神数量
    counts = {}
    for pillar_key, data in ten_gods_analysis.items():
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg and stem_tg != '日主':
            counts[stem_tg] = counts.get(stem_tg, 0) + 2
        for hd in data.get('branch_hidden', []):
            tg = hd.get('ten_god', '')
            if tg:
                counts[tg] = counts.get(tg, 0) + 1

    # 检查是否某类一家独大（超过6分）
    for tg, count in counts.items():
        if count >= 6:
            cong_ge_names = {
                '食神': '从儿格', '伤官': '从儿格',
                '正财': '从财格', '偏财': '从财格',
                '七杀': '从杀格', '正官': '从官格',
            }
            if tg in cong_ge_names:
                return {
                    'name': cong_ge_names[tg],
                    'dominant_god': tg,
                    'note': '从格命局，用神与忌神与普通命局相反，需特殊分析',
                }
    return None


def get_yong_shen(pillars, format_info):
    """
    取用神和忌神
    用神：对日主有利、能平衡命局的五行
    忌神：对日主不利的五行
    """
    day_stem = pillars['day_master']
    day_element = STEM_ELEMENTS[day_stem]
    strength = get_daymaster_strength(pillars)

    # 从格特殊处理
    if format_info.get('is_cong_ge'):
        cong_ge = format_info['cong_ge_detail']
        dominant_god = cong_ge.get('dominant_god', '')
        if dominant_god in ['食神', '伤官']:
            # 从儿格：顺从食伤之气，用神为食伤对应的输出五行
            return {
                'yong_shen': _get_output_element(day_element),
                'ji_shen': [day_element, _get_input_element(day_element)],
                'yong_shen_reason': '从儿格，顺从食伤之气',
                'strength': '弱（从格）',
            }
        elif dominant_god in ['正财', '偏财']:
            return {
                'yong_shen': CONTROLS[day_element],
                'ji_shen': [day_element, _get_input_element(day_element)],
                'yong_shen_reason': '从财格，顺从财星之气',
                'strength': '弱（从格）',
            }
        elif dominant_god in ['七杀', '正官']:
            return {
                'yong_shen': _who_controls(day_element),
                'ji_shen': [day_element],
                'yong_shen_reason': '从杀格，顺从官杀之气',
                'strength': '弱（从格）',
            }

    # 普通格局
    if strength == '旺':
        # 日主旺：需要克泄耗，用食伤（泄）、财星（耗）、官杀（克）
        yong = CONTROLS[day_element]  # 官杀克身
        yong2 = _get_output_element(day_element)  # 食伤泄身
        ji = _get_input_element(day_element)  # 印比帮身为忌
        return {
            'yong_shen': yong,
            'yong_shen_secondary': yong2,
            'ji_shen': [ji, day_element],
            'yong_shen_reason': f'日主{strength}，需官杀制化或食伤泄秀',
            'strength': strength,
        }
    elif strength == '弱':
        # 日主弱：需要帮扶，用比劫（帮）、印星（生）
        yong = day_element  # 比劫帮身
        yong2 = _get_input_element(day_element)  # 印星生身
        ji = CONTROLS[day_element]  # 官杀克身为忌
        ji2 = _get_output_element(day_element)  # 财星耗印为忌
        return {
            'yong_shen': yong2,  # 印星更稳
            'yong_shen_secondary': yong,
            'ji_shen': [ji, CONTROLS[ji2]],
            'yong_shen_reason': f'日主{strength}，需印星生扶或比劫帮身',
            'strength': strength,
        }
    else:
        # 中和：以格局需要为准，看月令定用神
        month_element = BRANCH_ELEMENTS[pillars['month_pillar']['branch']]
        return {
            'yong_shen': month_element,
            'ji_shen': [CONTROLS[month_element]],
            'yong_shen_reason': f'日主{strength}，以月令{month_element}为基础调候',
            'strength': strength,
        }


def _get_output_element(element):
    """我生的五行（食伤所属五行）"""
    return GENERATES.get(element, '')


def _get_input_element(element):
    """生我的五行（印星所属五行）"""
    for k, v in GENERATES.items():
        if v == element:
            return k
    return ''


def _who_controls(element):
    """克我的五行（官杀所属五行）"""
    for k, v in CONTROLS.items():
        if v == element:
            return k
    return ''


def format_full_analysis(pillars, ten_gods_analysis):
    """
    综合格局分析：格局 + 用神忌神
    """
    format_info = determine_format(pillars, ten_gods_analysis)
    yong_shen_info = get_yong_shen(pillars, format_info)

    return {
        'format': format_info,
        'yong_shen': yong_shen_info,
        'summary': _build_format_summary(format_info, yong_shen_info),
    }


def _build_format_summary(format_info, yong_shen_info):
    """生成格局分析文字摘要"""
    lines = []
    lines.append(f"▶ 格局：{format_info['format_name']}")
    if format_info.get('format_source'):
        lines.append(f"  成格依据：{format_info['format_source']}")
    if format_info.get('is_cong_ge'):
        lines.append(f"  ⚠ 特殊从格，{format_info['cong_ge_detail']['note']}")

    strength = yong_shen_info.get('strength', '')
    lines.append(f"▶ 日主强弱：{strength}")
    lines.append(f"▶ 用神：{yong_shen_info.get('yong_shen', '')}（{yong_shen_info.get('yong_shen_reason', '')}）")
    if yong_shen_info.get('yong_shen_secondary'):
        lines.append(f"  辅用神：{yong_shen_info.get('yong_shen_secondary', '')}")
    ji_list = yong_shen_info.get('ji_shen', [])
    if ji_list:
        lines.append(f"▶ 忌神：{'、'.join(ji_list)}")

    return '\n'.join(lines)
