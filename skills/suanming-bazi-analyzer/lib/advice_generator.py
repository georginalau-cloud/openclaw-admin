"""
[19] lib/advice_generator.py - 趋吉避凶建议模块
调用层级：被 bin/bazi 调用
依赖：data/feng-shui-data.json

根据用神忌神和命局特点，
生成开运色、吉祥数字、最佳方位、合作建议等。
"""

import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _load_feng_shui():
    path = os.path.join(_DATA_DIR, 'feng-shui-data.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


FENG_SHUI_DATA = _load_feng_shui()


def generate_advice(pillars, yong_shen_info, format_analysis):
    """
    生成完整的趋吉避凶建议
    """
    yong_shen = yong_shen_info.get('yong_shen', '')
    yong_shen_secondary = yong_shen_info.get('yong_shen_secondary', '')
    ji_shen = yong_shen_info.get('ji_shen', [])

    lucky_colors = _get_lucky_colors(yong_shen, yong_shen_secondary, ji_shen)
    lucky_numbers = _get_lucky_numbers(yong_shen)
    best_direction = _get_best_direction(yong_shen)
    partner_advice = _get_partner_zodiac(pillars)
    life_advice = _generate_life_advice(pillars, yong_shen_info, format_analysis)

    return {
        'lucky_colors': lucky_colors,
        'lucky_numbers': lucky_numbers,
        'best_direction': best_direction,
        'partner_advice': partner_advice,
        'life_advice': life_advice,
        'summary': _build_advice_summary(
            lucky_colors, lucky_numbers, best_direction,
            partner_advice, life_advice
        ),
    }


def _get_lucky_colors(yong_shen, secondary, ji_shen):
    """获取开运色（根据用神五行）"""
    feng_shui = FENG_SHUI_DATA.get('开运色', {})
    result = {
        'primary': [],
        'secondary': [],
        'avoid': [],
        'tips': '',
    }

    if yong_shen and yong_shen in feng_shui:
        data = feng_shui[yong_shen]
        result['primary'] = data.get('lucky_colors', [])
        result['tips'] = data.get('color_usage', '')
        result['avoid'] = data.get('avoid_colors', [])

    if secondary and secondary in feng_shui:
        data = feng_shui[secondary]
        secondary_colors = data.get('lucky_colors', [])
        # 过滤掉与主用神 avoid 重叠的颜色，避免矛盾
        avoid_set = set(result['avoid'])
        result['secondary'] = [c for c in secondary_colors if c not in avoid_set]

    return result


def _get_lucky_numbers(yong_shen):
    """获取吉祥数字（根据用神五行）"""
    feng_shui = FENG_SHUI_DATA.get('吉祥数字', {})
    if yong_shen and yong_shen in feng_shui:
        data = feng_shui[yong_shen]
        return {
            'numbers': data.get('lucky_numbers', []),
            'tips': data.get('number_tips', ''),
        }
    return {'numbers': [], 'tips': ''}


def _get_best_direction(yong_shen):
    """获取最佳居住/办公方位"""
    feng_shui = FENG_SHUI_DATA.get('居住方位', {})
    if yong_shen and yong_shen in feng_shui:
        data = feng_shui[yong_shen]
        return {
            'primary': data.get('best_direction', ''),
            'secondary': data.get('secondary', ''),
            'avoid': data.get('avoid', ''),
            'tips': data.get('home_tips', ''),
        }
    return {}


def _get_partner_zodiac(pillars):
    """推荐合作伙伴属相"""
    year_branch = pillars['year_pillar']['branch']
    feng_shui = FENG_SHUI_DATA.get('合作伙伴建议', {})

    # 构建地支->建议的映射
    branch_key = None
    for key in feng_shui:
        if year_branch in key:
            branch_key = key
            break

    if branch_key and branch_key in feng_shui:
        data = feng_shui[branch_key]
        return {
            'own_zodiac': data.get('zodiac', ''),
            'compatible': data.get('compatible_with', []),
            'avoid': data.get('avoid_with', []),
            'tips': f"与{'、'.join(data.get('compatible_with', []))}属相合作最为顺遂，避免与{'、'.join(data.get('avoid_with', []))}属相产生重大冲突",
        }
    return {}


def _generate_life_advice(pillars, yong_shen_info, format_analysis):
    """
    生成综合生活建议
    基于格局特点和用神忌神
    """
    advice = []
    strength = yong_shen_info.get('strength', '中')
    yong_shen = yong_shen_info.get('yong_shen', '')
    format_name = format_analysis.get('format', {}).get('format_name', '')

    # 基于日主强弱的建议
    if strength == '极旺':
        advice.append('日主极旺，宜大力泄秀，主动开创，切忌闭门造车')
        advice.append('善用才华和技能变现，广结人脉，财运自然跟随')
    elif strength == '旺':
        advice.append('日主旺，宜发挥才干，主动开创，不宜守株待兔')
        advice.append('注意避免过于强势，善用柔化之道')
    elif strength == '弱' or strength == '极弱':
        advice.append('日主偏弱，宜借势而为，多寻贵人助力，不宜单打独斗')
        advice.append('多学习充实自己，积累内力是关键')
    else:
        advice.append('日主中和，平衡是关键，进退有度')

    # 基于格局的建议
    format_advice_map = {
        '正官格': '正官格重名誉，行事须光明磊落，诚信是最大的资本',
        '偏官格（七杀格）': '七杀格需磨砺，逆境中成长，保持健康最重要',
        '正财格': '正财格宜稳健，勤劳积累，避免投机冒进',
        '偏财格': '偏财格人缘为财，广交益友，善用社交资源',
        '食神格': '食神格享福，注意健康饮食，不宜过度安逸',
        '伤官格': '伤官格有才，需学会收敛锋芒，尊重权威',
        '印绶格（正印格）': '印绶格重知识，多读书学习，贵人自然来',
    }
    if format_name in format_advice_map:
        advice.append(format_advice_map[format_name])

    return advice


def _build_advice_summary(lucky_colors, lucky_numbers, best_direction, partner_advice, life_advice):
    """生成趋吉避凶建议文字摘要"""
    lines = []

    if lucky_colors.get('primary'):
        lines.append(f"▶ 开运颜色：{'、'.join(lucky_colors['primary'])}")
        # 只显示真正需要避免的颜色（已排除辅用神颜色）
        avoid = [c for c in lucky_colors.get('avoid', [])
                 if c not in lucky_colors.get('secondary', [])]
        if avoid:
            lines.append(f"  避免颜色：{'、'.join(avoid)}")
        if lucky_colors.get('secondary'):
            lines.append(f"  次选颜色（辅用神）：{'、'.join(lucky_colors['secondary'])}")
        if lucky_colors.get('tips'):
            lines.append(f"  使用建议：{lucky_colors['tips']}")

    if lucky_numbers.get('numbers'):
        nums_str = '、'.join(str(n) for n in lucky_numbers['numbers'])
        lines.append(f"▶ 吉祥数字：{nums_str}")
        if lucky_numbers.get('tips'):
            lines.append(f"  数字含义：{lucky_numbers['tips']}")

    if best_direction.get('primary'):
        lines.append(f"▶ 最佳方位：{best_direction['primary']}")
        if best_direction.get('avoid'):
            lines.append(f"  避免方位：{best_direction['avoid']}")
        if best_direction.get('tips'):
            lines.append(f"  家居建议：{best_direction['tips']}")

    if partner_advice.get('compatible'):
        lines.append(f"▶ 合作伙伴：宜与{'、'.join(partner_advice['compatible'])}属相合作")
        if partner_advice.get('avoid'):
            lines.append(f"  谨慎对象：{'、'.join(partner_advice['avoid'])}属相（需更多磨合）")

    if life_advice:
        lines.append("▶ 人生建议：")
        for a in life_advice:
            lines.append(f"  • {a}")

    return '\n'.join(lines)
