"""
luck_cycle_analyzer.py - 大运流年分析模块

计算十年大运起点和方向，预测近几年流年运势。
参考《子平真诠》大运排法。
"""

from .ganzhi_calculator import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENTS,
    BRANCH_ELEMENTS, HIDDEN_STEMS, GENERATES, CONTROLS,
    STEM_POLARITY
)

# 大运方向规则
# 阳年男命、阴年女命 -> 顺排（大运顺数）
# 阴年男命、阳年女命 -> 逆排（大运逆数）


def calculate_luck_cycles(pillars, gender='unknown', birth_year=None):
    """
    计算大运
    参数:
        pillars: 四柱数据
        gender: 'male' | 'female' | 'unknown'
        birth_year: 出生年份
    返回: 大运数组（10条，每条10年）
    """
    year_stem = pillars['year_pillar']['stem']
    month_stem = pillars['month_pillar']['stem']
    month_branch = pillars['month_pillar']['branch']

    year_polarity = STEM_POLARITY[year_stem]

    # 确定大运方向
    if gender == 'male':
        forward = (year_polarity == '阳')  # 阳年男命顺排
    elif gender == 'female':
        forward = (year_polarity == '阴')  # 阴年女命顺排
    else:
        forward = True  # 默认顺排

    # 大运起点（从月柱顺/逆推）
    month_stem_idx = HEAVENLY_STEMS.index(month_stem)
    month_branch_idx = EARTHLY_BRANCHES.index(month_branch)

    cycles = []
    current_year = birth_year or 2000

    # 计算大运起运年龄（简化：约3岁起运，每10年一换）
    # 实际上需要计算距离下一/上一节气的天数，这里用近似值
    start_age = _estimate_start_age(pillars, forward)

    for i in range(10):
        if forward:
            stem_idx = (month_stem_idx + i + 1) % 10
            branch_idx = (month_branch_idx + i + 1) % 12
        else:
            stem_idx = (month_stem_idx - i - 1) % 10
            branch_idx = (month_branch_idx - i - 1) % 12

        stem = HEAVENLY_STEMS[stem_idx]
        branch = EARTHLY_BRANCHES[branch_idx]
        gz = stem + branch

        cycle_age_start = start_age + i * 10
        cycle_year_start = current_year + cycle_age_start

        cycles.append({
            'index': i + 1,
            'gz': gz,
            'stem': stem,
            'branch': branch,
            'stem_element': STEM_ELEMENTS[stem],
            'branch_element': BRANCH_ELEMENTS[branch],
            'age_start': cycle_age_start,
            'age_end': cycle_age_start + 9,
            'year_start': cycle_year_start,
            'year_end': cycle_year_start + 9,
        })

    return {
        'forward': forward,
        'start_age': start_age,
        'cycles': cycles,
        'direction': '顺排' if forward else '逆排',
    }


def _estimate_start_age(pillars, forward):
    """估算大运起运年龄（近似值）"""
    # 实际算法需要计算节气距离，这里用近似3-8岁
    # 月支节气距离影响起运早晚
    month_branch = pillars['month_pillar']['branch']
    branch_idx = EARTHLY_BRANCHES.index(month_branch)
    # 简化：用月支索引 mod 得到一个3-8之间的起运年龄
    return 3 + (branch_idx % 6)


def analyze_current_luck(luck_cycles, current_year):
    """
    分析当前所处大运
    """
    cycles = luck_cycles.get('cycles', [])
    current_cycle = None

    for cycle in cycles:
        if cycle['year_start'] <= current_year <= cycle['year_end']:
            current_cycle = cycle
            break

    # 如果没找到（起运前），取第一个
    if not current_cycle and cycles:
        current_cycle = cycles[0]

    return current_cycle


def predict_yearly_fortune(pillars, ten_gods_analysis, yong_shen_info, years_to_predict=None):
    """
    流年运势预测
    参数:
        years_to_predict: [2024, 2025, 2026, ...] 或 None（默认未来3年）
    """
    if years_to_predict is None:
        import datetime
        this_year = datetime.date.today().year
        years_to_predict = [this_year, this_year + 1, this_year + 2]

    yong_shen = yong_shen_info.get('yong_shen', '')
    ji_shen = yong_shen_info.get('ji_shen', [])
    strength = yong_shen_info.get('strength', '中')

    predictions = []
    for year in years_to_predict:
        prediction = _predict_single_year(year, pillars, yong_shen, ji_shen, strength)
        predictions.append(prediction)

    return predictions


def _predict_single_year(year, pillars, yong_shen, ji_shen, strength):
    """
    预测单一年份运势
    """
    # 计算流年干支
    year_stem_idx = (year - 4) % 10
    year_branch_idx = (year - 4) % 12
    year_stem = HEAVENLY_STEMS[year_stem_idx]
    year_branch = EARTHLY_BRANCHES[year_branch_idx]
    year_gz = year_stem + year_branch
    year_element = STEM_ELEMENTS[year_stem]
    branch_element = BRANCH_ELEMENTS[year_branch]

    # 流年天干与日主关系
    from .ten_gods_analyzer import get_ten_god
    day_stem = pillars['day_master']
    year_ten_god = get_ten_god(day_stem, year_stem)

    # 流年地支藏干
    hidden = [s for s in HIDDEN_STEMS[year_branch] if s]
    hidden_gods = []
    for h in hidden:
        hg = get_ten_god(day_stem, h)
        hidden_gods.append({'stem': h, 'ten_god': hg})

    # 与命局的刑冲克害合
    interactions = _check_year_interactions(year_branch, pillars)

    # 综合判断吉凶
    fortune_score, fortune_desc = _score_year_fortune(
        year_element, year_ten_god, yong_shen, ji_shen, interactions
    )

    # 各方面预测
    aspects = _predict_year_aspects(year_ten_god, hidden_gods, fortune_score)

    return {
        'year': year,
        'gz': year_gz,
        'stem': year_stem,
        'branch': year_branch,
        'stem_element': year_element,
        'year_ten_god': year_ten_god,
        'hidden_gods': hidden_gods,
        'interactions': interactions,
        'fortune_score': fortune_score,
        'fortune_desc': fortune_desc,
        'aspects': aspects,
    }


def _check_year_interactions(year_branch, pillars):
    """检查流年地支与命局地支的刑冲克害合"""
    interactions = []

    # 六冲
    CHONG_MAP = {
        '子': '午', '午': '子', '丑': '未', '未': '丑',
        '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
        '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳',
    }
    chong_branch = CHONG_MAP.get(year_branch)

    for pillar_key in ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']:
        branch = pillars[pillar_key]['branch']
        pillar_label = {'year_pillar': '年支', 'month_pillar': '月支',
                        'day_pillar': '日支', 'hour_pillar': '时支'}[pillar_key]

        if chong_branch and branch == chong_branch:
            interactions.append(f"流年{year_branch}冲{pillar_label}{branch}（动荡变化）")

    # 六合（简化）
    HE_MAP = {
        '子': '丑', '丑': '子', '寅': '亥', '亥': '寅',
        '卯': '戌', '戌': '卯', '辰': '酉', '酉': '辰',
        '巳': '申', '申': '巳', '午': '未', '未': '午',
    }
    he_branch = HE_MAP.get(year_branch)
    for pillar_key in ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']:
        branch = pillars[pillar_key]['branch']
        pillar_label = {'year_pillar': '年支', 'month_pillar': '月支',
                        'day_pillar': '日支', 'hour_pillar': '时支'}[pillar_key]
        if he_branch and branch == he_branch:
            interactions.append(f"流年{year_branch}合{pillar_label}{branch}（有助力或变化）")

    return interactions


def _score_year_fortune(year_element, year_ten_god, yong_shen, ji_shen, interactions):
    """综合评分流年吉凶"""
    score = 50  # 基础分

    # 流年天干五行与用神忌神的关系
    if year_element == yong_shen:
        score += 25
        desc_base = '流年用神得力，诸事顺遂'
    elif year_element in ji_shen:
        score -= 20
        desc_base = '流年遇忌神，需谨慎应对'
    else:
        desc_base = '流年平稳，稳中求进'

    # 冲的影响
    chong_count = sum(1 for i in interactions if '冲' in i)
    score -= chong_count * 10

    # 合的影响
    he_count = sum(1 for i in interactions if '合' in i)
    score += he_count * 5

    score = max(10, min(100, score))

    if score >= 75:
        fortune = '大吉'
        desc = f'{desc_base}，是发展、提升的好时机'
    elif score >= 55:
        fortune = '小吉'
        desc = f'{desc_base}，整体向好，局部需注意'
    elif score >= 40:
        fortune = '平'
        desc = f'{desc_base}，平稳度过，无大起伏'
    else:
        fortune = '需防'
        desc = f'{desc_base}，建议低调行事，避免大的决策'

    return fortune, desc


def _predict_year_aspects(year_ten_god, hidden_gods, fortune_score):
    """按各方面预测流年"""
    aspects = {}

    # 事业
    career_map = {
        '正官': '职位晋升机会，上司赏识',
        '七杀': '竞争激烈，需展现实力',
        '食神': '工作顺手，创意灵感多',
        '伤官': '发挥才华，但注意与上司关系',
        '正财': '薪资稳定增长',
        '偏财': '有偏财机遇，投资机会',
        '比肩': '竞争增多，需突出自身优势',
        '劫财': '小心合伙纠纷',
        '正印': '贵人相助，学习进修有收获',
        '偏印': '独立思考，可能有新方向',
    }
    aspects['career'] = career_map.get(year_ten_god, '事业平稳推进')

    # 财运
    wealth_map = {
        '正财': '正财进账稳定，适合储蓄理财',
        '偏财': '偏财运旺，适合投资或经商',
        '食神': '靠才能变现，财运自然进账',
        '伤官': '靠技能获财，注意不必要开支',
        '比肩': '财运受竞争影响，谨慎共财',
        '劫财': '破财风险，谨慎投资',
        '七杀': '财运波动，不宜大手笔投资',
        '正官': '收入与地位挂钩，薪资有望提升',
    }
    aspects['wealth'] = wealth_map.get(year_ten_god, '财运平稳')

    # 感情
    love_map = {
        '正财': '桃花运旺（男命），感情稳定',
        '偏财': '桃花出现，但需注意专一',
        '正官': '感情有缘（女命），适合确定关系',
        '七杀': '感情容易波折，需沟通耐心',
        '食神': '感情顺和，有浪漫气息',
        '伤官': '感情不稳，容易产生争吵',
        '比肩': '感情竞争多，注意第三者',
    }
    aspects['love'] = love_map.get(year_ten_god, '感情平稳')

    return aspects


def format_luck_cycle_report(luck_cycles, yearly_predictions, current_year=None):
    """
    生成大运流年分析文字报告
    """
    import datetime
    if current_year is None:
        current_year = datetime.date.today().year

    lines = []

    # 大运总述
    direction = luck_cycles.get('direction', '顺排')
    start_age = luck_cycles.get('start_age', 3)
    lines.append(f"▶ 大运排法：{direction}，约{start_age}岁起运，每10年一换")
    lines.append("")

    # 近3条大运
    cycles = luck_cycles.get('cycles', [])
    relevant_cycles = [c for c in cycles if c['year_end'] >= current_year - 5][:4]

    lines.append("▶ 大运一览：")
    for c in relevant_cycles:
        marker = " ← 当前" if c['year_start'] <= current_year <= c['year_end'] else ""
        lines.append(
            f"  {c['gz']}运（{c['year_start']}-{c['year_end']}，{c['age_start']}-{c['age_end']}岁）{marker}"
        )

    lines.append("")
    lines.append("▶ 流年预测：")
    for pred in yearly_predictions:
        lines.append(f"  {pred['year']}年（{pred['gz']}）【{pred['fortune_desc']}】")
        if pred.get('interactions'):
            lines.append(f"    特殊：{'；'.join(pred['interactions'][:2])}")
        lines.append(f"    事业：{pred['aspects'].get('career', '')}")
        lines.append(f"    财运：{pred['aspects'].get('wealth', '')}")
        lines.append(f"    感情：{pred['aspects'].get('love', '')}")

    return '\n'.join(lines)
