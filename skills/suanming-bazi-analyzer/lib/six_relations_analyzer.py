"""
[15] lib/six_relations_analyzer.py - 六亲关系分析模块
调用层级：被 bin/bazi 调用
依赖：lib/ganzhi_calculator.py [03]、data/classic-wisdom.json

通过命局中父母星、财星、官星、子女星等位置，
分析父母缘、婚姻感情、子女情况。

理论依据：
  《三命通会》：父母宫在年柱，兄弟宫在月柱，妻财宫在日支，子女宫在时柱
  《渊海子平》：论六亲，以十神配六亲
"""

import json
import os

from .ganzhi_calculator import STEM_ELEMENTS, BRANCH_ELEMENTS, GENERATES, CONTROLS

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _load_classic_wisdom():
    path = os.path.join(_DATA_DIR, 'classic-wisdom.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


CLASSIC_WISDOM = _load_classic_wisdom()

# 六亲理论经典论述（来自 classic-wisdom.json）
_SAN_MING = CLASSIC_WISDOM.get('san_ming_tonghui', {}).get('key_passages', {})
_YUAN_HAI = CLASSIC_WISDOM.get('yuan_hai_zi_ping', {}).get('key_passages', {})

# 《三命通会》六亲宫位理论
LIU_QIN_PALACE_THEORY = _SAN_MING.get(
    'liu_qin_fen_xi',
    '父母宫在年柱，兄弟宫在月柱，妻财宫在日支，子女宫在时柱。'
)

# 六亲十神对应理论（综合子平法经典）
LIU_QIN_SHISHEN_THEORY = (
    '子平法六亲对应：正财偏财为父，正印偏印为母，官杀为夫（女命），'
    '财星为妻（男命），比肩劫财为兄弟，官杀为子女（男命），食伤为子女（女命），日支为配偶宫。'
    '（综合《渊海子平》《三命通会》）'
)


def analyze_six_relations(pillars, ten_gods_analysis, yong_shen_info, gender='unknown'):
    """
    六亲关系分析
    参数:
        pillars: 四柱数据
        ten_gods_analysis: 十神分析
        yong_shen_info: 用神忌神信息
        gender: 'male' | 'female' | 'unknown'
    """
    parent_analysis = _analyze_parents(pillars, ten_gods_analysis, yong_shen_info)
    marriage_analysis = _analyze_marriage(pillars, ten_gods_analysis, yong_shen_info, gender)
    children_analysis = _analyze_children(pillars, ten_gods_analysis, yong_shen_info, gender)

    return {
        'parents': parent_analysis,
        'marriage': marriage_analysis,
        'children': children_analysis,
        'classic_theory': {
            'palace_theory': LIU_QIN_PALACE_THEORY,
            'shishen_theory': LIU_QIN_SHISHEN_THEORY,
        },
        'summary': _build_relations_summary(parent_analysis, marriage_analysis, children_analysis),
    }


def _analyze_parents(pillars, ten_gods_analysis, yong_shen_info):
    """
    父母缘分分析
    父：偏财（男命）；正印（女命父）
    母：正印（男命）；正财（女命父亲的财）
    年柱代表祖辈，月柱代表父母
    """
    yong_shen = yong_shen_info.get('yong_shen', '')
    strength = yong_shen_info.get('strength', '中')

    # 月柱代表父母宫
    month_tg = ten_gods_analysis.get('month_pillar', {}).get('stem_ten_god', '')
    year_tg = ten_gods_analysis.get('year_pillar', {}).get('stem_ten_god', '')

    result = {
        'month_pillar_god': month_tg,
        'year_pillar_god': year_tg,
    }

    # 父母缘深浅
    good_signs = ['正印', '偏印', '正官', '正财']
    challenge_signs = ['七杀', '伤官', '劫财']

    if month_tg in good_signs:
        result['parent_bond'] = '深厚'
        result['parent_detail'] = '月柱得力，父母缘分深厚，早年得家庭助力，有祖荫可依'
    elif month_tg in challenge_signs:
        result['parent_bond'] = '一般'
        result['parent_detail'] = '月柱现挑战之象，与父母关系可能有摩擦，或早年需自立门户'
    else:
        result['parent_bond'] = '普通'
        result['parent_detail'] = '父母缘分平平，家庭环境普通，靠自身努力为主'

    # 祖荫
    if year_tg in ['正印', '偏印', '正官', '偏财']:
        result['ancestral_blessing'] = '有祖荫，家族背景对早年发展有正面影响'
    else:
        result['ancestral_blessing'] = '祖荫较淡，需靠自身打拼'

    return result


def _analyze_marriage(pillars, ten_gods_analysis, yong_shen_info, gender):
    """
    婚姻感情分析
    男命：财星为妻（正财为正配，偏财为情人/外遇）
    女命：官星为夫（正官为正配，七杀为情人/外遇）
    """
    yong_shen = yong_shen_info.get('yong_shen', '')
    day_element = STEM_ELEMENTS[pillars['day_master']]

    # 确定配偶星
    if gender == 'male':
        spouse_star_main = '正财'
        spouse_star_side = '偏财'
        spouse_label = '妻星'
    elif gender == 'female':
        spouse_star_main = '正官'
        spouse_star_side = '七杀'
        spouse_label = '夫星'
    else:
        spouse_star_main = '正财'
        spouse_star_side = '七杀'
        spouse_label = '配偶星'

    # 统计配偶星数量
    spouse_count = 0

    for pillar_key, data in ten_gods_analysis.items():
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg in [spouse_star_main, spouse_star_side]:
            spouse_count += 1

        for hd in data.get('branch_hidden', []):
            if hd.get('ten_god') in [spouse_star_main, spouse_star_side]:
                spouse_count += 1

    result = {
        'spouse_label': spouse_label,
        'spouse_count': spouse_count,
    }

    # 日支代表配偶宫
    day_branch_hidden = ten_gods_analysis.get('day_pillar', {}).get('branch_hidden', [])
    day_branch_gods = [hd['ten_god'] for hd in day_branch_hidden]

    if spouse_star_main in day_branch_gods or spouse_star_side in day_branch_gods:
        result['spouse_palace'] = '配偶宫有力'
        result['marriage_quality'] = '日支见配偶星，婚姻缘分较好，伴侣能力不俗'
    else:
        result['spouse_palace'] = '配偶宫中性'
        result['marriage_quality'] = '婚姻平稳，需双方共同经营'

    # 婚姻风险
    if spouse_count == 0:
        result['marriage_risk'] = '命局中配偶星缺失，感情路可能较为曲折，或晚婚'
    elif spouse_count >= 3:
        result['marriage_risk'] = '配偶星多现，感情生活丰富，但也存在感情波折或二婚风险'
    else:
        result['marriage_risk'] = '感情运势平稳，一段为主'

    # 配偶特质（根据配偶星五行）
    if gender == 'male':
        # 妻星为财，财的五行代表妻子特质
        cai_element = CONTROLS[day_element]  # 日主克的五行即财
        spouse_traits = _get_spouse_traits_by_element(cai_element, '妻')
    elif gender == 'female':
        # 夫星为官，官的五行代表夫特质
        guan_element = _who_controls(day_element)  # 克日主的五行
        spouse_traits = _get_spouse_traits_by_element(guan_element, '夫')
    else:
        spouse_traits = '配偶特质需结合实际命盘具体分析'

    result['spouse_traits'] = spouse_traits

    return result


def _analyze_children(pillars, ten_gods_analysis, yong_shen_info, gender):
    """
    子女情况分析
    子平法六亲对应（《渊海子平》）：
      男命：官杀（正官/七杀）为子女星
      女命：食伤（食神/伤官）为子女星
    统计规则：
      - 天干透出：力量最强，权重3
      - 地支主气（藏干第一位）：力量较强，权重2
      - 地支中气（藏干第二位）：力量中等，权重1
      - 地支余气（藏干第三位）：力量极弱，不计入"入命"判断
    """
    if gender == 'male':
        child_stars = ['正官', '七杀']
        child_label = '子女星（官杀）'
        child_logic = '男命以官杀为子女星'
    elif gender == 'female':
        child_stars = ['食神', '伤官']
        child_label = '子女星（食伤）'
        child_logic = '女命以食伤为子女星'
    else:
        child_stars = ['食神', '伤官', '正官', '七杀']
        child_label = '子女星'
        child_logic = '性别未知，综合食伤官杀判断'

    # 短码到全称的映射（cangygan_details 用短码）
    short_to_full = {
        '食': '食神', '伤': '伤官',
        '官': '正官', '杀': '七杀',
        '财': '正财', '才': '偏财',
        '印': '正印', '枭': '偏印',
        '比': '比肩', '劫': '劫财',
    }

    child_score = 0   # 加权分数
    child_details = []  # 记录具体来源

    for pillar_key, data in ten_gods_analysis.items():
        # 天干透出（权重3，力量最强）
        stem_tg = data.get('stem_ten_god', '')
        if stem_tg in child_stars and pillar_key != 'day_pillar':
            child_score += 3
            child_details.append(f'{pillar_key}天干{stem_tg}透出')

        # 地支藏干（按主气/中气/余气分权重）
        branch_hidden = data.get('branch_hidden', [])
        for idx, hd in enumerate(branch_hidden):
            tg = hd.get('ten_god', '')
            if tg in child_stars:
                if idx == 0:    # 主气，权重2
                    child_score += 2
                    child_details.append(f'{pillar_key}地支主气{tg}')
                elif idx == 1:  # 中气，权重1
                    child_score += 1
                    child_details.append(f'{pillar_key}地支中气{tg}（力量较弱）')
                # 余气（idx==2）不计入，力量太弱

    result = {
        'child_score': child_score,
        'child_details': child_details,
        'child_label': child_label,
        'child_logic': child_logic,
    }

    # 根据加权分数判断子女缘
    if child_score == 0:
        result['children_bond'] = f'命局{child_label}缺失，子女缘较淡，或子女较少，或与子女聚少离多'
    elif child_score <= 2:
        result['children_bond'] = f'{child_label}有微弱根气（藏于地支），子女缘一般，通常有一至两位子女'
    elif child_score <= 4:
        result['children_bond'] = f'{child_label}有力，子女缘较好，子女聪慧，亲子关系融洽'
    else:
        result['children_bond'] = f'{child_label}旺盛，子女缘深，子女贤孝，晚年有子女福'

    # 时柱代表晚年/子女宫（时干透出才算有力）
    hour_stem_tg = ten_gods_analysis.get('hour_pillar', {}).get('stem_ten_god', '')
    if hour_stem_tg in child_stars:
        result['late_life'] = f'时柱天干透出{child_label}，晚年享子女福，晚景温馨'
    elif hour_stem_tg in ['正印', '偏印']:
        result['late_life'] = '时柱见印星，晚年多有贵人助力，精神富足，适合修身养性'
    elif hour_stem_tg in ['正财', '偏财']:
        result['late_life'] = '时柱见财星，晚年财运不衰，物质充裕'
    elif hour_stem_tg in ['正官', '七杀']:
        if gender == 'female':
            result['late_life'] = '时柱见官杀（夫星），晚年感情生活仍有波澜，或子女事业有成'
        else:
            result['late_life'] = '时柱见官杀，晚年仍有事业心，地位受人尊重'
    elif hour_stem_tg in ['食神', '伤官']:
        if gender == 'male':
            result['late_life'] = '时柱见食伤，晚年生活享受，才华仍在，子女孝顺'
        else:
            result['late_life'] = '时柱见食伤（子女星），晚年享子女福，晚景温馨'
    elif hour_stem_tg in ['比肩', '劫财']:
        result['late_life'] = '时柱见比劫，晚年独立自主，靠自身努力，朋友相伴'
    else:
        result['late_life'] = '晚年运势中平，安稳度日'

    return result


def _get_spouse_traits_by_element(element, role):
    """根据配偶星五行描述配偶特质"""
    traits = {
        '木': f'{role}属木型，外形清秀高挑，性格温和有条理，重情义',
        '火': f'{role}属火型，热情开朗，有魅力，行动力强，但脾气较急',
        '土': f'{role}属土型，稳重踏实，包容性强，是可靠的生活伴侣',
        '金': f'{role}属金型，外形气质佳，有原则，处事果断，重效率',
        '水': f'{role}属水型，聪明灵活，社交能力强，感情细腻',
    }
    return traits.get(element, f'{role}特质需结合具体命盘分析')


def _who_controls(element):
    """克该五行的五行"""
    for k, v in CONTROLS.items():
        if v == element:
            return k
    return ''


def _build_relations_summary(parent_analysis, marriage_analysis, children_analysis):
    """生成六亲关系文字摘要"""
    lines = []

    # 经典理论依据（来自 classic-wisdom.json）
    lines.append(f"【理论依据】《三命通会》：「{LIU_QIN_PALACE_THEORY}」")
    lines.append(f"《渊海子平》：「{LIU_QIN_SHISHEN_THEORY}」")
    lines.append("")

    # 父母
    lines.append(f"▶ 父母缘分：{parent_analysis.get('parent_detail', '')}")
    lines.append(f"  祖荫：{parent_analysis.get('ancestral_blessing', '')}")

    # 婚姻
    lines.append(f"▶ 婚姻感情：{marriage_analysis.get('marriage_quality', '')}")
    lines.append(f"  配偶特质：{marriage_analysis.get('spouse_traits', '')}")
    lines.append(f"  婚姻提示：{marriage_analysis.get('marriage_risk', '')}")

    # 子女
    lines.append(f"▶ 子女情况：{children_analysis.get('children_bond', '')}")
    lines.append(f"  晚年福气：{children_analysis.get('late_life', '')}")

    return '\n'.join(lines)
