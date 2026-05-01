"""
[14] lib/character_profiler.py - 性格深度画像模块
调用层级：被 bin/bazi 调用
依赖：lib/ten_gods_analyzer.py [11]、data/ten-gods-traits.json

通过日主特征、十神组合、格局分析，
生成显性性格、隐性性格、优缺点的深度画像。
"""

import json
import os

# 加载十神性格库
_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def _load_traits():
    path = os.path.join(_DATA_DIR, 'ten-gods-traits.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

TRAITS_DATA = _load_traits()


def build_character_profile(pillars, ten_gods_analysis, format_analysis, dominant_ten_gods):
    """
    生成完整的性格画像
    参数:
        pillars: 四柱数据
        ten_gods_analysis: 十神分析
        format_analysis: 格局分析
        dominant_ten_gods: 主导十神列表 [(十神, 权重), ...]
    返回: 性格画像字典
    """
    day_stem = pillars['day_master']
    day_master_traits = TRAITS_DATA.get('日主性格库', {}).get(day_stem, {})
    ten_gods_traits = TRAITS_DATA.get('十神性格库', {})

    # 显性性格（别人眼中的你）= 日主 + 月柱天干十神 + 主导十神
    overt_traits = _build_overt_personality(day_stem, day_master_traits, ten_gods_analysis, ten_gods_traits, dominant_ten_gods)

    # 隐性性格（内心真实渴望）= 日主内心 + 正印/偏印 + 年柱信息
    covert_traits = _build_covert_personality(day_stem, day_master_traits, pillars, ten_gods_analysis, ten_gods_traits)

    # 优缺点
    strengths, weaknesses = _build_strengths_weaknesses(day_master_traits, dominant_ten_gods, ten_gods_traits)

    # 社交风格
    social_style = _build_social_style(day_stem, dominant_ten_gods, ten_gods_traits)

    return {
        'day_master_symbol': day_master_traits.get('symbol', day_stem),
        'overt_personality': overt_traits,
        'covert_personality': covert_traits,
        'strengths': strengths,
        'weaknesses': weaknesses,
        'social_style': social_style,
        'summary': _build_character_summary(day_stem, day_master_traits, overt_traits, covert_traits, strengths, weaknesses),
    }


def _build_overt_personality(day_stem, day_master_traits, ten_gods_analysis, ten_gods_traits, dominant_ten_gods):
    """显性性格：别人眼中的你"""
    traits = list(day_master_traits.get('core_traits', []))

    # 加入月柱天干十神的性格（月柱代表社会面貌）
    month_stem_tg = ten_gods_analysis.get('month_pillar', {}).get('stem_ten_god', '')
    if month_stem_tg and month_stem_tg in ten_gods_traits:
        traits.extend(ten_gods_traits[month_stem_tg].get('positive_traits', [])[:2])

    # 加入最主导的十神（前2位）
    for tg, _ in dominant_ten_gods[:2]:
        if tg in ten_gods_traits:
            traits.extend(ten_gods_traits[tg].get('positive_traits', [])[:1])

    # 去重
    seen = set()
    unique_traits = []
    for t in traits:
        if t not in seen:
            seen.add(t)
            unique_traits.append(t)

    return unique_traits[:6]  # 最多展示6个


def _build_covert_personality(day_stem, day_master_traits, pillars, ten_gods_analysis, ten_gods_traits):
    """
    隐性性格：内心深处的渴望与恐惧。
    命理依据：
      - 天干透出 → 显性（外在表现）
      - 地支藏干 → 隐性（内心深处）
    取年柱和时柱的地支主气（第一藏干）来判断内心渴望，
    月柱代表社会面，日支代表配偶宫，均不用于隐性性格。
    """
    inner = day_master_traits.get('inner_world', '')
    covert_notes = [inner] if inner else []

    # 取年柱和时柱的地支主气（藏干第一位）
    pillar_cn = {'year_pillar': '年', 'hour_pillar': '时'}
    for pillar_key in ['year_pillar', 'hour_pillar']:
        data = ten_gods_analysis.get(pillar_key, {})
        branch_hidden = data.get('branch_hidden', [])
        if not branch_hidden:
            continue
        # 只取主气（第一藏干），主气代表地支最核心的能量
        main_hidden = branch_hidden[0]
        tg = main_hidden.get('ten_god', '')
        cn = pillar_cn.get(pillar_key, '')
        if tg in ['正印', '偏印']:
            covert_notes.append(f"有{tg}藏于{cn}支，内心渴望被认可与保护，有深厚的学习欲望")
        elif tg in ['正财', '偏财']:
            covert_notes.append(f"有{tg}藏于{cn}支，内心深处重视物质安全感和家庭保障")
        elif tg in ['正官', '七杀']:
            covert_notes.append(f"有{tg}藏于{cn}支，内心渴望被认可、有地位，对规则和权威有复杂情感")
        elif tg in ['食神', '伤官']:
            covert_notes.append(f"有{tg}藏于{cn}支，内心深处渴望自由表达，有强烈的创作欲和表达欲")

    if not covert_notes:
        covert_notes.append(f"日主{day_stem}，内心{day_master_traits.get('inner_world', '渴望自我实现')}")

    return covert_notes


def _build_strengths_weaknesses(day_master_traits, dominant_ten_gods, ten_gods_traits):
    """提炼优点和缺点"""
    strengths = list(day_master_traits.get('core_traits', [])[:3])
    weaknesses = [day_master_traits.get('weakness', '')] if day_master_traits.get('weakness') else []

    for tg, weight in dominant_ten_gods[:3]:
        if tg in ten_gods_traits:
            tg_data = ten_gods_traits[tg]
            strengths.extend(tg_data.get('positive_traits', [])[:1])
            weaknesses.extend(tg_data.get('negative_traits', [])[:1])

    # 去重
    strengths = list(dict.fromkeys(s for s in strengths if s))[:5]
    weaknesses = list(dict.fromkeys(w for w in weaknesses if w))[:4]

    return strengths, weaknesses


def _build_social_style(day_stem, dominant_ten_gods, ten_gods_traits):
    """社交风格"""
    # 根据主导十神判断社交风格
    style_map = {
        '食神': '温和随和，善于营造轻松氛围，朋友众多',
        '伤官': '才华外露，有个人魅力，但有时显得傲慢',
        '偏财': '社交达人，人缘极佳，异性缘旺',
        '正财': '诚实可靠，交友谨慎，但一旦建立关系则忠诚长久',
        '正官': '稳重有礼，重视规则，在社交中往往扮演领导角色',
        '七杀': '个性鲜明，行事果断，令人既敬又畏',
        '正印': '温文尔雅，有气质，容易获得长辈认可',
        '偏印': '独立神秘，有独特魅力，朋友圈小而精',
        '比肩': '重义气，讲原则，交朋友讲究对等',
        '劫财': '豪爽大方，人脉广但交情多浅',
    }

    if dominant_ten_gods:
        top_tg = dominant_ten_gods[0][0]
        return style_map.get(top_tg, '性格均衡，社交方式中规中矩')
    return '性格均衡，社交方式中规中矩'


def _build_character_summary(day_stem, day_master_traits, overt_traits, covert_traits, strengths, weaknesses):
    """生成性格分析文字摘要"""
    lines = []
    symbol = day_master_traits.get('symbol', day_stem)
    lines.append(f"▶ 日主 {day_stem}（{symbol}）")
    lines.append(f"  显性性格（别人眼中的你）：{'、'.join(overt_traits)}")

    covert_str = '；'.join(covert_traits) if isinstance(covert_traits, list) else covert_traits
    lines.append(f"  隐性性格（内心真实渴望）：{covert_str}")

    if strengths:
        lines.append(f"  核心优势：{'、'.join(strengths)}")
    if weaknesses:
        lines.append(f"  性格盲点：{'、'.join(weaknesses)}")

    return '\n'.join(lines)
