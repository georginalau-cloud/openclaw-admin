"""
[16] lib/wealth_career_analyzer.py - 财富事业分析模块
调用层级：被 bin/bazi 调用
依赖：lib/ganzhi_calculator.py [03]、data/industries-mapping.json

分析命局的财富等级、求财方式、适合行业和事业高低点。
"""

import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _load_industries():
    path = os.path.join(_DATA_DIR, 'industries-mapping.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


INDUSTRIES_DATA = _load_industries()

from .ganzhi_calculator import STEM_ELEMENTS, BRANCH_ELEMENTS, GENERATES, CONTROLS


def analyze_wealth_career(pillars, ten_gods_analysis, format_analysis, yong_shen_info):
    """
    财富事业综合分析
    """
    wealth_level = _assess_wealth_level(pillars, ten_gods_analysis, yong_shen_info)
    wealth_method = _determine_wealth_method(ten_gods_analysis, yong_shen_info)
    career_industries = _recommend_industries(pillars, yong_shen_info)
    career_peaks = _identify_career_peaks(pillars, ten_gods_analysis, yong_shen_info)

    return {
        'wealth_level': wealth_level,
        'wealth_method': wealth_method,
        'career_industries': career_industries,
        'career_peaks': career_peaks,
        'summary': _build_wealth_summary(wealth_level, wealth_method, career_industries, career_peaks),
    }


def _assess_wealth_level(pillars, ten_gods_analysis, yong_shen_info):
    """评估财富等级"""
    strength = yong_shen_info.get('strength', '中')
    yong_shen = yong_shen_info.get('yong_shen', '')
    day_element = STEM_ELEMENTS[pillars['day_master']]

    # 统计财星数量和位置
    cai_count = 0
    cai_in_month = False

    for pillar_key, data in ten_gods_analysis.items():
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg in ['正财', '偏财']:
            cai_count += 2
            if pillar_key == 'month_pillar':
                cai_in_month = True

        for hd in data.get('branch_hidden', []):
            if hd.get('ten_god') in ['正财', '偏财']:
                cai_count += 1

    # 官印相生（代表富贵兼备）
    has_guan = any(
        data.get('stem_ten_god') in ['正官', '七杀']
        for data in ten_gods_analysis.values()
    )
    has_yin = any(
        data.get('stem_ten_god') in ['正印', '偏印']
        for data in ten_gods_analysis.values()
    )

    # 评估逻辑
    score = cai_count
    if cai_in_month:
        score += 2  # 月令财星权重高
    if strength == '旺' and cai_count > 0:
        score += 1  # 身强财旺最佳
    if has_guan and has_yin:
        score += 2  # 官印相生加分

    if score >= 8:
        level = '巨富'
        desc = '命局财星旺盛，格局高贵，终身富贵，有望积累巨额财富'
    elif score >= 5:
        level = '中富'
        desc = '财运不俗，中年后财务宽裕，家庭富足，可积累可观资产'
    elif score >= 3:
        level = '小康'
        desc = '财运平稳，靠努力可达小康，衣食无忧但难成大富'
    else:
        level = '平稳'
        desc = '财运平平，以稳定收入为主，注重节俭积累'

    return {
        'level': level,
        'description': desc,
        'cai_count': cai_count,
        'score': score,
    }


def _determine_wealth_method(ten_gods_analysis, yong_shen_info):
    """
    确定求财方式
    - 正财旺：适合上班领薪、稳健理财
    - 偏财旺：适合经商、投机、广开财路
    - 食伤旺：靠才华和技能获财
    - 官杀旺：靠职位和地位获财
    """
    counts = {}
    for data in ten_gods_analysis.values():
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg:
            counts[stem_tg] = counts.get(stem_tg, 0) + 2
        for hd in data.get('branch_hidden', []):
            tg = hd.get('ten_god', '')
            if tg:
                counts[tg] = counts.get(tg, 0) + 1

    methods = []

    pian_cai = counts.get('偏财', 0)
    zheng_cai = counts.get('正财', 0)
    shi_shen = counts.get('食神', 0)
    shang_guan = counts.get('伤官', 0)
    zheng_guan = counts.get('正官', 0)
    qi_sha = counts.get('七杀', 0)

    if pian_cai > zheng_cai:
        methods.append('偏财旺：善于投机经营，适合经商做生意、投资理财，财来财往较大')
    elif zheng_cai > 0:
        methods.append('正财稳健：适合稳定工作领取薪资，或做传统行业，积累踏实')

    if shi_shen + shang_guan > 2:
        methods.append('食伤有力：靠才华、技能、创意变现，适合自由职业或创意行业')

    if zheng_guan + qi_sha > 2:
        methods.append('官杀入命：适合依靠职位晋升和权威地位获取财富，官场仕途可期')

    if not methods:
        methods.append('财运中平：以正当职业稳健积累为主，不宜冒险投机')

    return methods


def _recommend_industries(pillars, yong_shen_info):
    """根据用神五行推荐行业"""
    yong_shen_element = yong_shen_info.get('yong_shen', '')
    secondary_element = yong_shen_info.get('yong_shen_secondary', '')

    industries_data = INDUSTRIES_DATA.get('五行行业对应', {})
    yijin_data = INDUSTRIES_DATA.get('喜忌行业建议', {})

    result = {
        'primary': None,
        'secondary': None,
    }

    if yong_shen_element and yong_shen_element in industries_data:
        primary = industries_data[yong_shen_element]
        yijin_key = f'用神为{yong_shen_element}'
        yijin = yijin_data.get(yijin_key, {})
        # wealth_tips 原文是"X命人财运..."，替换为"用神为X，..."
        raw_tips = primary.get('wealth_tips', '')
        tips = raw_tips.replace(f'{yong_shen_element}命人', f'用神为{yong_shen_element}，')
        result['primary'] = {
            'element': yong_shen_element,
            'industries': primary.get('industries', [])[:5],
            'suitable_roles': primary.get('suitable_roles', [])[:3],
            'tips': tips,
            'best_direction': primary.get('direction', ''),
            'should_avoid': yijin.get('应避免', []),
        }

    if secondary_element and secondary_element in industries_data:
        secondary = industries_data[secondary_element]
        result['secondary'] = {
            'element': secondary_element,
            'industries': secondary.get('industries', [])[:3],
        }

    return result


def _identify_career_peaks(pillars, ten_gods_analysis, yong_shen_info):
    """
    识别事业高低点规律
    基于日主强弱和用神特点给出建议
    """
    strength = yong_shen_info.get('strength', '中')
    yong_shen = yong_shen_info.get('yong_shen', '')
    ji_shen   = yong_shen_info.get('ji_shen', [])

    # 年龄段规律
    peaks = {
        'expansion_timing': '',
        'consolidation_timing': '',
        'general_rule': '',
    }

    # 月柱代表中年（30-45岁）、年柱代表早年、时柱代表晚年
    month_tg = ten_gods_analysis.get('month_pillar', {}).get('stem_ten_god', '')
    year_tg = ten_gods_analysis.get('year_pillar', {}).get('stem_ten_god', '')
    hour_tg = ten_gods_analysis.get('hour_pillar', {}).get('stem_ten_god', '')

    if month_tg in ['正官', '偏财', '食神']:
        peaks['career_peak_age'] = '中年期（30-45岁）是事业高峰，应抓住机遇积极扩展'
    elif year_tg in ['正官', '偏财']:
        peaks['career_peak_age'] = '早年基础好，年轻时努力可打下坚实基础'
    elif hour_tg in ['正官', '偏财', '食神']:
        peaks['career_peak_age'] = '晚年事业不衰，50岁后仍有新的发展机遇'
    else:
        peaks['career_peak_age'] = '事业起伏与大运走势关系密切，需结合大运分析'

    # 用明确的五行说明扩张/守成时机
    yong_str = f'{yong_shen}（用神）' if yong_shen else '用神'
    ji_str   = '、'.join(f'{j}（忌神）' for j in ji_shen) if ji_shen else '忌神'

    if strength in ('极旺', '旺'):
        peaks['expansion_timing'] = f'走食伤、财星大运/流年时，是激进扩张的好时机'
        peaks['consolidation_timing'] = f'走比劫大运/流年时，竞争加剧，宜守成布局'
    elif strength in ('弱', '极弱'):
        peaks['expansion_timing'] = f'走印星、比劫大运/流年时，得到助力，可适度扩张'
        peaks['consolidation_timing'] = f'走财星、官杀大运/流年时，压力较大，宜稳健守成'
    else:
        peaks['expansion_timing'] = f'走{yong_str}五行大运/流年时是扩张良机'
        peaks['consolidation_timing'] = f'走{ji_str}五行大运/流年时宜保守应对'

    return peaks


def _build_wealth_summary(wealth_level, wealth_method, career_industries, career_peaks):
    """生成财富事业文字摘要"""
    lines = []

    lines.append(f"▶ 财富等级：{wealth_level['level']}")
    lines.append(f"  {wealth_level['description']}")

    lines.append(f"▶ 求财方式：")
    for m in wealth_method:
        lines.append(f"  • {m}")

    if career_industries.get('primary'):
        p = career_industries['primary']
        lines.append(f"▶ 最适合行业（用神{p['element']}）：{'、'.join(p['industries'][:4])}")
        lines.append(f"  适合职位：{'、'.join(p['suitable_roles'])}")
        if p.get('should_avoid'):
            lines.append(f"  应避免：{'、'.join(p['should_avoid'][:3])}")

    lines.append(f"▶ 事业高低点：")
    lines.append(f"  {career_peaks.get('career_peak_age', '')}")
    lines.append(f"  扩张时机：{career_peaks.get('expansion_timing', '')}")
    lines.append(f"  守成时机：{career_peaks.get('consolidation_timing', '')}")

    return '\n'.join(lines)
