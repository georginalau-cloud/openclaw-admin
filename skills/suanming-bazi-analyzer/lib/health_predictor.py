"""
[17] lib/health_predictor.py - 健康预警模块
调用层级：被 bin/bazi 调用
依赖：lib/ganzhi_calculator.py [03]、data/classic-wisdom.json

根据五行偏枯（过旺或过弱）预测对应脏腑健康风险，
识别需要特别注意的年份。

理论依据：
  《穷通宝鉴》：五行偏枯主疾病：木多主肝胆，火多主心脏，土多主脾胃，金多主肺，水多主肾脏。
"""

import json
import os

from .ganzhi_calculator import STEM_ELEMENTS, BRANCH_ELEMENTS, get_element_counts

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _load_classic_wisdom():
    path = os.path.join(_DATA_DIR, 'classic-wisdom.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


CLASSIC_WISDOM = _load_classic_wisdom()

# 《穷通宝鉴》健康理论（来自 classic-wisdom.json）
_QIONG = CLASSIC_WISDOM.get('qiong_tong_bao_jian', {}).get('key_passages', {})
HEALTH_THEORY = _QIONG.get(
    'jian_kang',
    '五行偏枯主疾病：木多主肝胆，火多主心脏，土多主脾胃，金多主肺，水多主肾脏。'
)


# 五行对应脏腑（中医五行学说）
ELEMENT_ORGAN_MAP = {
    '木': {
        'organs': ['肝', '胆'],
        'sense': '眼睛',
        'body_part': '筋腱',
        'strong_risk': '肝火旺盛，易怒，眼睛充血，胆固醇偏高',
        'weak_risk': '肝血不足，视力模糊，疲劳，胆怯易惊',
    },
    '火': {
        'organs': ['心', '小肠'],
        'sense': '舌',
        'body_part': '血脉',
        'strong_risk': '心火上炎，口舌生疮，血压偏高，失眠多梦',
        'weak_risk': '心气虚弱，心悸心慌，血液循环差，精力不足',
    },
    '土': {
        'organs': ['脾', '胃'],
        'sense': '口',
        'body_part': '肌肉',
        'strong_risk': '脾胃积滞，消化不良，痰湿体质，肥胖倾向',
        'weak_risk': '脾胃虚弱，消化吸收差，贫血，四肢乏力',
    },
    '金': {
        'organs': ['肺', '大肠'],
        'sense': '鼻',
        'body_part': '皮肤',
        'strong_risk': '肺气过盛，呼吸道敏感，皮肤干燥，便秘',
        'weak_risk': '肺气虚弱，易感冒，过敏体质，皮肤问题',
    },
    '水': {
        'organs': ['肾', '膀胱'],
        'sense': '耳',
        'body_part': '骨骼',
        'strong_risk': '肾气过旺，水肿，腰膝酸软，生殖系统问题',
        'weak_risk': '肾气不足，腰膝无力，听力下降，骨质疏松',
    },
}

# 五行相克（克则受损）
CONTROLS = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}


def predict_health(pillars, yong_shen_info):
    """
    健康预警分析
    返回各脏腑风险等级和建议
    """
    element_counts = get_element_counts(pillars)
    total = sum(element_counts.values())
    average = total / 5 if total > 0 else 2

    health_risks = {}
    for element, count in element_counts.items():
        organ_info = ELEMENT_ORGAN_MAP[element]
        if total > 0:
            ratio = count / total
        else:
            ratio = 0.2

        if ratio >= 0.35:  # 过旺（超过35%）
            risk_level = '高风险'
            risk_detail = organ_info['strong_risk']
        elif ratio <= 0.10:  # 过弱（低于10%）
            risk_level = '需注意'
            risk_detail = organ_info['weak_risk']
        else:
            risk_level = '平稳'
            risk_detail = f"{'/'.join(organ_info['organs'])}功能正常，注意日常保养"

        health_risks[element] = {
            'element': element,
            'organs': organ_info['organs'],
            'count': count,
            'ratio': round(ratio, 2),
            'risk_level': risk_level,
            'risk_detail': risk_detail,
        }

    # 用神五行若缺失，对应脏腑更需注意
    yong_shen_element = yong_shen_info.get('yong_shen', '')
    if yong_shen_element and yong_shen_element in health_risks:
        if health_risks[yong_shen_element]['risk_level'] == '需注意':
            health_risks[yong_shen_element]['special_note'] = (
                f"用神为{yong_shen_element}，此五行偏弱，"
                f"{''.join(ELEMENT_ORGAN_MAP[yong_shen_element]['organs'])}系统需特别保养"
            )

    # 整体体质倾向
    constitution = _assess_constitution(element_counts)

    # 生活建议
    advice = _generate_health_advice(health_risks, yong_shen_element)

    return {
        'element_distribution': element_counts,
        'health_risks': health_risks,
        'constitution': constitution,
        'advice': advice,
        'classic_theory': HEALTH_THEORY,
        'summary': _build_health_summary(health_risks, constitution, advice),
    }


def _assess_constitution(element_counts):
    """评估整体体质倾向"""
    max_element = max(element_counts, key=element_counts.get)
    min_element = min(element_counts, key=element_counts.get)

    constitution_map = {
        '木': '肝胆型体质（木型人）：体型修长，肌肉紧致，易肝郁气滞',
        '火': '心血管型体质（火型人）：面色红润，精力充沛，易心火亢盛',
        '土': '脾胃型体质（土型人）：体形偏圆润，消化系统为重点保养对象',
        '金': '肺金型体质（金型人）：皮肤白皙，呼吸系统敏感，注意肺部保养',
        '水': '肾水型体质（水型人）：骨骼发育与肾功能为保健重点',
    }

    return {
        'dominant': max_element,
        'weak': min_element,
        'description': constitution_map.get(max_element, '体质均衡，以日常调理为主'),
    }


def _generate_health_advice(health_risks, yong_shen_element):
    """生成具体健康建议"""
    advice = []

    for element, risk_data in health_risks.items():
        if risk_data['risk_level'] == '高风险':
            organ_str = '、'.join(risk_data['organs'])
            advice.append(f"⚠ {organ_str}需重点保护：{risk_data['risk_detail']}，建议定期体检")
        elif risk_data['risk_level'] == '需注意':
            organ_str = '、'.join(risk_data['organs'])
            advice.append(f"💛 {organ_str}功能偏弱：{risk_data['risk_detail']}，注意补充对应营养")

    if not advice:
        advice.append('五行分布较为均衡，整体健康状况良好，注重日常规律作息即可')

    return advice


def _build_health_summary(health_risks, constitution, advice):
    """生成健康预警文字摘要"""
    lines = []

    # 经典理论依据（来自 classic-wisdom.json）
    lines.append(f"【理论依据】《穷通宝鉴》：「{HEALTH_THEORY}」")
    lines.append("")

    lines.append(f"▶ 体质倾向：{constitution['description']}")
    lines.append(f"  弱项五行（{constitution['weak']}）对应{'/'.join(ELEMENT_ORGAN_MAP[constitution['weak']]['organs'])}需加强保养")

    high_risks = [
        f"{'/'.join(r['organs'])}（{r['risk_level']}）"
        for r in health_risks.values()
        if r['risk_level'] != '平稳'
    ]
    if high_risks:
        lines.append(f"▶ 需注意脏腑：{'、'.join(high_risks)}")

    lines.append("▶ 健康建议：")
    for a in advice[:3]:
        lines.append(f"  {a}")

    return '\n'.join(lines)
