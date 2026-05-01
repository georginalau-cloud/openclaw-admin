"""
[18] lib/luck_cycle_analyzer.py - 大运流年分析模块
调用层级：被 bin/bazi 调用
依赖：lib/ganzhi_calculator.py [03]、lib/zhi_relations.py [10]、data/classic-wisdom.json

职责：对 bazi_chart 输出的大运/流年数据做深度分析，
      输出吉凶评估、各方面预测文字。

注意：大运/流年的排盘计算由 src/dayun.py 负责（精确节气算法）。
      本模块只做分析，不做排盘。

理论依据：
  《三命通会》：大运者，人生阶段之缩影，每十年一换，吉凶悔吝系于此。
  《滴天髓》：格局贵在清纯，忌混浊。
  《穷通宝鉴》：富贵贫贱，取决于格局之高下，用神之有力与否。
"""

import json
import os

from .ganzhi_calculator import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENTS,
    BRANCH_ELEMENTS, HIDDEN_STEMS, GENERATES, CONTROLS,
    STEM_POLARITY
)

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _load_classic_wisdom():
    path = os.path.join(_DATA_DIR, 'classic-wisdom.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


CLASSIC_WISDOM = _load_classic_wisdom()

# 大运流年经典论述（来自 classic-wisdom.json）
_SAN_MING = CLASSIC_WISDOM.get('san_ming_tonghui', {}).get('key_passages', {})
_DI_TIAN  = CLASSIC_WISDOM.get('di_tian_sui', {}).get('key_passages', {})
_QIONG    = CLASSIC_WISDOM.get('qiong_tong_bao_jian', {}).get('key_passages', {})

DAYUN_THEORY = _SAN_MING.get(
    'da_yun_liu_nian',
    '大运者，人生阶段之缩影，每十年一换，吉凶悔吝系于此。流年者，岁运之交会，与大运、原局三者互动，方知当年祸福。'
)
YONGSHEN_THEORY = _DI_TIAN.get(
    'yong_shen_qi_ji',
    '用神者，命局之主导，能调候、平衡、扶抑日主。忌神者，克泄用神，阻碍命局之发展。'
)
FUGUI_THEORY = _QIONG.get(
    'fu_gui_pin_jian',
    '富贵贫贱，取决于格局之高下，用神之有力与否。格局清纯有力者富贵，混浊无力者平庸。'
)


def _assess_jiacao_shift(chart: dict, dayun_gz: str, liuyear_gz: str) -> dict:
    """
    假从格动态评估：判断大运/流年是否将印星根气削弱到"趋近真从"的程度。

    理论依据（《滴天髓》任铁樵注）：
      假从者，局中有印比，本不能从。然大运流年将印比冲克合去，
      则假从变真从，富贵随之。反之，印比得救，从格破，命运大变。

    判断逻辑：
      1. 找出命局中所有印星/比劫的地支根气（主气/中气）
      2. 检测大运+流年是否通过冲/三会/三合/六合将这些根气削弱
      3. 若所有根气均被削弱，判为"趋近真从"

    返回：
      {
        'is_jiacao':        bool,   # 是否为假从格
        'trending_zhencong': bool,  # 是否趋近真从
        'yin_bi_roots':     list,   # 印星/比劫的根气地支列表
        'weakened_roots':   list,   # 被削弱的根气
        'intact_roots':     list,   # 仍然完好的根气
        'note':             str,    # 说明文字
      }
    """
    from .ganzhi_calculator import (
        ZHI_CHONG, ZHI_HE6, ZHI_SANHUI, ZHI_SANHE,
        STEM_ELEMENTS, BRANCH_ELEMENTS, HIDDEN_STEMS, GENERATES
    )

    yong_shen_info = chart.get('yong_shen', {})
    # 只对假从格（日主极弱但有印比根气）进行评估
    strength = yong_shen_info.get('strength', '')
    if strength not in ('弱', '极弱'):
        return {'is_jiacao': False}

    pillars_list = chart.get('pillars', [])
    day_gan = chart.get('day_gan', '')
    day_element = STEM_ELEMENTS.get(day_gan, '')
    input_element = next((k for k, v in GENERATES.items() if v == day_element), '')  # 印星五行

    # 找出命局中印星/比劫的地支根气（主气index=0，中气index=1）
    yin_bi_roots = []  # [(地支, 藏干, 力量等级, 五行)]
    for p in pillars_list:
        zhi = p.get('zhi', '')
        hidden = HIDDEN_STEMS.get(zhi, [])
        for idx, h in enumerate(hidden[:2]):  # 只看主气和中气
            if h is None:
                continue
            h_elem = STEM_ELEMENTS.get(h, '')
            if h_elem == day_element or h_elem == input_element:
                strength_level = '主气' if idx == 0 else '中气'
                yin_bi_roots.append({
                    'zhi': zhi, 'gan': h, 'level': strength_level, 'element': h_elem
                })

    if not yin_bi_roots:
        return {'is_jiacao': False}

    # 收集大运+流年的地支
    dayun_zhi  = dayun_gz[1]  if len(dayun_gz)  >= 2 else ''
    liuyear_zhi = liuyear_gz[1] if len(liuyear_gz) >= 2 else ''
    yun_zhis = set(z for z in [dayun_zhi, liuyear_zhi] if z)

    # 命局地支集合
    yuanju_zhis = frozenset(p['zhi'] for p in pillars_list if 'zhi' in p)
    # 大运+流年+命局的完整地支集合
    all_zhis = yuanju_zhis | yun_zhis

    weakened_roots = []
    intact_roots   = []

    for root in yin_bi_roots:
        zhi = root['zhi']
        weakened = False
        reason   = ''

        # 1. 六冲（最强，直接冲走）
        chong_of_zhi = ZHI_CHONG.get(zhi)
        if chong_of_zhi and chong_of_zhi in yun_zhis:
            weakened = True
            reason = f'{zhi}被{chong_of_zhi}冲（六冲破根，力量大损）'

        # 2. 三会局（将该地支的五行属性改变）
        if not weakened:
            for members, element, name in ZHI_SANHUI:
                if zhi in members and members.issubset(all_zhis):
                    # 三会局改变了该地支的五行属性
                    if element != root['element']:  # 化成了不同五行
                        weakened = True
                        reason = f'{name}成立，{zhi}的{root["element"]}性被{element}局吸收，印星根气大幅削弱'
                    break

        # 3. 三合局（力量次于三会）
        if not weakened:
            for members, element, name in ZHI_SANHE:
                if zhi in members and members.issubset(all_zhis):
                    if element != root['element']:
                        weakened = True
                        reason = f'{name}成立，{zhi}的{root["element"]}性被{element}局压制，印星根气削弱'
                    break

        # 4. 六合（合而不化，只是轻微牵制，不能真正合去印星根气）
        # 理论依据：地支六合极难化气，合而不化是常态，印星根气仍在
        # 因此六合不触发"趋近真从"，只记录为"轻微影响"
        if not weakened:
            he6_partner = ZHI_HE6.get(zhi)
            if he6_partner and he6_partner in yun_zhis:
                # 不标记为 weakened，只记录轻微影响
                intact_roots.append({**root, 'minor_note': f'{zhi}与{he6_partner}六合（合而不化，印星根气仍在，轻微牵制）'})
                continue  # 跳过后面的 weakened/intact 判断

        if weakened:
            weakened_roots.append({**root, 'reason': reason})
        else:
            intact_roots.append(root)

    # 判断是否趋近真从
    trending_zhencong = len(intact_roots) == 0 and len(weakened_roots) > 0

    if trending_zhencong:
        note = (
            f'⚠ 假从趋近真从：命局印星根气（'
            f'{"、".join(r["zhi"] + r["level"] for r in weakened_roots)}'
            f'）在{dayun_gz}大运×{liuyear_gz}流年中被削弱，'
            f'命局暂时呈现真从特征。此时顺从财官之气，运势大旺；'
            f'若印比大运来救，从格破，需防大起大落。'
        )
    elif weakened_roots:
        note = (
            f'印星根气部分削弱（{"、".join(r["reason"] for r in weakened_roots[:2])}），'
            f'仍有{len(intact_roots)}处根气完好，假从格未变，但财官运势有所增强。'
        )
    else:
        note = '印星根气完好，假从格稳定，顺从财官之气需谨慎。'

    return {
        'is_jiacao':         True,
        'trending_zhencong': trending_zhencong,
        'yin_bi_roots':      yin_bi_roots,
        'weakened_roots':    weakened_roots,
        'intact_roots':      intact_roots,
        'note':              note,
    }


def analyze_current_luck(chart: dict, current_year: int = None) -> dict:
    """
    分析当前大运和流年。
    接收 bazi_chart 的完整输出，返回分析结果。

    参数:
        chart: bazi_chart.build_bazi_chart() 的返回值
        current_year: 指定年份，默认取 chart 中的 current_year
    """
    import datetime
    cur_year = current_year or chart.get('current_year') or datetime.date.today().year

    current = chart.get('current', {})
    if not current:
        return {'error': '无当前大运信息'}

    dayun   = current.get('dayun', {})
    liuyear = current.get('liuyear', {})

    yong_shen_info = chart.get('yong_shen', {})
    yong_shen = yong_shen_info.get('yong_shen', '')
    ji_shen   = yong_shen_info.get('ji_shen', [])

    # 提取命局地支集合（用于三会/三合/六合/六冲检测）
    pillars_list = chart.get('pillars', [])
    yuanju_zhis = frozenset(p['zhi'] for p in pillars_list if 'zhi' in p)
    gender = chart.get('meta', {}).get('gender', 'unknown')

    # 大运分析
    dayun_analysis = _analyze_ganzhi_luck(
        dayun.get('ganzhi', ''),
        dayun.get('gan_shishen', ''),
        dayun.get('zhi_shishen', ''),
        yong_shen, ji_shen,
        label=f"{dayun.get('ganzhi','')}大运（{dayun.get('start_year')}-{dayun.get('end_year')}）",
        yuanju_zhis=yuanju_zhis,
        gender=gender,
    )

    # 流年分析（命局地支 + 大运地支一起参与合局检测）
    liuyear_analysis = None
    if liuyear:
        dayun_zhi = dayun.get('ganzhi', '')[1] if len(dayun.get('ganzhi', '')) >= 2 else ''
        combined_zhis = yuanju_zhis | ({dayun_zhi} if dayun_zhi else set())
        liuyear_analysis = _analyze_ganzhi_luck(
            liuyear.get('ganzhi', ''),
            liuyear.get('gan_shishen', ''),
            liuyear.get('zhi_shishen', ''),
            yong_shen, ji_shen,
            label=f"{cur_year}年{liuyear.get('ganzhi','')}（流年）",
            yuanju_zhis=combined_zhis,
            gender=gender,
        )

    return {
        'current_year':      cur_year,
        'dayun_analysis':    dayun_analysis,
        'liuyear_analysis':  liuyear_analysis,
        'classic_theory':    DAYUN_THEORY,
        'yongshen_theory':   YONGSHEN_THEORY,
        'jiacao_shift':      _assess_jiacao_shift(
            chart,
            dayun.get('ganzhi', ''),
            liuyear.get('ganzhi', '') if liuyear else '',
        ),
    }



def _analyze_ganzhi_luck(gz, gan_shishen, zhi_shishen, yong_shen, ji_shen, label='',
                         yuanju_zhis=None, gender='unknown') -> dict:
    """
    分析单个干支（大运或流年）的吉凶。
    yuanju_zhis: 命局所有地支集合，用于检测三会/三合/六合/六冲
    """
    if not gz or len(gz) < 2:
        return {}

    gan, zhi = gz[0], gz[1]
    gan_element = STEM_ELEMENTS.get(gan, '')
    zhi_element = BRANCH_ELEMENTS.get(zhi, '')

    # 吉凶评分
    score = 50
    notes = []
    interaction_notes = []

    # 天干与用神/忌神
    if gan_element == yong_shen:
        score += 20
        notes.append(f'天干{gan}（{gan_element}）为用神，得力')
    elif gan_element in ji_shen:
        score -= 15
        notes.append(f'天干{gan}（{gan_element}）为忌神，需防')

    # 地支与用神/忌神
    if zhi_element == yong_shen:
        score += 15
        notes.append(f'地支{zhi}（{zhi_element}）为用神，有根')
    elif zhi_element in ji_shen:
        score -= 10
        notes.append(f'地支{zhi}（{zhi_element}）为忌神，需防')

    # 地支与命局的刑冲合会（需要命局地支集合）
    if yuanju_zhis:
        from .zhi_relations import analyze_zhi_relations, score_relation_for_element
        rel_result = analyze_zhi_relations(zhi, yuanju_zhis)
        relations  = rel_result['relations']

        for r in relations:
            element = r.get('element', '')
            rtype   = r['type']
            rname   = r['name']
            rdesc   = r['desc']
            weight  = r['weight']

            # 根据关系类型和涉及五行调整评分
            if r['is_positive']:
                if rtype == '六合':
                    # 六合合而不化（常态）：
                    # 不用化神五行判断，而是看两支各自的原五行
                    # 六合的作用是"稳定"，对用神的影响通过地支本身的五行已经在前面计算过了
                    # 这里只加小额稳定加分，不按化神算
                    zhi_elem = BRANCH_ELEMENTS.get(zhi, '')
                    partner_elem = BRANCH_ELEMENTS.get(r.get('partner', ''), '')
                    if zhi_elem == yong_shen or partner_elem == yong_shen:
                        score += 5  # 六合稳定用神，小额加分
                        interaction_notes.append(f'✅ {rdesc}（用神{yong_shen}得稳，合而不化）')
                    elif zhi_elem in ji_shen and partner_elem in ji_shen:
                        score -= 3  # 两支都是忌神，合而更稳，轻微不利
                        interaction_notes.append(f'⚠ {rdesc}（忌神相合，合而不化）')
                    else:
                        interaction_notes.append(f'◆ {rdesc}')
                elif element == yong_shen:
                    raw_bonus = int(abs(weight) * 5)
                    # 三会/三合使用神极旺时，需判断日主是否能承受
                    is_sanhui_or_sanhe = rtype in ('三会', '三合')
                    if is_sanhui_or_sanhe and rtype == '三会':
                        score += raw_bonus // 2  # 三会用神过旺，减半加分
                        interaction_notes.append(
                            f'✅ {rdesc}（用神{element}得力）'
                            f'⚠ 注意：三会局力量极强，需结合日主强弱判断是否能承受'
                        )
                    else:
                        score += raw_bonus
                        interaction_notes.append(f'✅ {rdesc}（用神{element}得力）')
                elif element in ji_shen:
                    score -= int(abs(weight) * 3)
                    interaction_notes.append(f'⚠ {rdesc}（忌神{element}聚合，需防）')
                else:
                    interaction_notes.append(f'◆ {rdesc}')
            else:
                # 冲/刑/害/破：看被冲的五行是用神还是忌神
                if element == yong_shen:
                    score -= int(abs(weight) * 4)
                    interaction_notes.append(f'❌ {rdesc}（用神{element}受损）')
                elif element in ji_shen:
                    score += int(abs(weight) * 3)
                    interaction_notes.append(f'✅ {rdesc}（忌神{element}受制，反为有利）')
                else:
                    score += int(weight * 2)  # weight 为负，轻微扣分
                    interaction_notes.append(f'⚠ {rdesc}')

        notes.extend(interaction_notes)

    # 十神特征
    shishen_notes = _shishen_notes(gan_shishen, zhi_shishen)
    notes.extend(shishen_notes)

    score = max(10, min(100, score))

    if score >= 75:
        rating = '大吉'
    elif score >= 60:
        rating = '小吉'
    elif score >= 45:
        rating = '平'
    else:
        rating = '需防'

    return {
        'label':              label,
        'ganzhi':             gz,
        'rating':             rating,
        'score':              score,
        'notes':              notes,
        'interaction_notes':  interaction_notes,
        'aspects':            _predict_aspects(gan_shishen, gender),
    }


def _shishen_notes(gan_shishen: str, zhi_shishen: str) -> list:
    """根据十神给出简要特征说明。"""
    notes = []
    mapping = {
        '比': '比肩透出，自主独立，竞争意识强',
        '劫': '劫财透出，注意财务损耗或合伙纠纷',
        '食': '食神透出，才华发挥，事业顺遂',
        '伤': '伤官透出，创意旺盛，注意与上司关系',
        '才': '偏财透出，偏财机遇，适合投资',
        '财': '正财透出，正财稳进，收入有望提升',
        '杀': '七杀透出，竞争压力大，需展现实力',
        '官': '正官透出，事业机遇，升职有望',
        '枭': '偏印透出，独立思考，注意过于保守',
        '印': '正印透出，贵人相助，学习进修有收获',
        '日主': '',
    }
    if gan_shishen and gan_shishen in mapping and mapping[gan_shishen]:
        notes.append(mapping[gan_shishen])
    return notes


def _predict_aspects(gan_shishen: str, gender: str = 'unknown') -> dict:
    """按十神给出各方面简要预测（性别敏感）。"""
    career_map = {
        '官': '职位晋升机会，上司赏识',
        '杀': '竞争激烈，需展现实力',
        '食': '工作顺手，创意灵感多',
        '伤': '发挥才华，注意与上司关系',
        '财': '薪资稳定增长',
        '才': '有偏财机遇，投资机会',
        '比': '竞争增多，需突出自身优势',
        '劫': '小心合伙纠纷',
        '印': '贵人相助，学习进修有收获',
        '枭': '独立思考，可能有新方向',
    }
    wealth_map = {
        '财': '正财进账稳定，适合储蓄理财',
        '才': '偏财运旺，适合投资或经商',
        '食': '靠才能变现，财运自然进账',
        '伤': '靠技能获财，注意不必要开支',
        '比': '财运受竞争影响，谨慎共财',
        '劫': '破财风险，谨慎投资',
        '杀': '财运波动，不宜大手笔投资',
        '官': '收入与地位挂钩，薪资有望提升',
    }
    # 感情分析根据性别区分：男命财星为妻，女命官杀为夫
    is_female = gender.lower() in ('female', 'f', '女')
    love_map = {
        '财': '桃花运旺，感情稳定' if not is_female else '财运带动人际，感情间接受益',
        '才': '桃花出现，注意专一',
        '官': '感情有缘，适合确定关系' if is_female else '事业稳定，感情随之稳固',
        '杀': '感情容易波折，需沟通耐心',
        '食': '感情顺和，有浪漫气息',
        '伤': '感情不稳，容易产生争吵',
        '比': '感情竞争多，注意第三者',
    }
    return {
        'career': career_map.get(gan_shishen, '事业平稳推进'),
        'wealth': wealth_map.get(gan_shishen, '财运平稳'),
        'love':   love_map.get(gan_shishen, '感情平稳'),
    }


def predict_yearly_fortune(chart: dict, years_to_predict: list = None) -> list:
    """
    流年运势预测。
    接收 bazi_chart 输出，对指定年份列表做预测。

    参数:
        chart: bazi_chart 的完整输出
        years_to_predict: 年份列表，默认取当前大运下的所有流年
    """
    import datetime
    cur_year = chart.get('current_year') or datetime.date.today().year

    yong_shen_info = chart.get('yong_shen', {})
    yong_shen = yong_shen_info.get('yong_shen', '')
    ji_shen   = yong_shen_info.get('ji_shen', [])

    # 从 dayun_list 里找流年数据
    predictions = []
    yuanju_zhis = frozenset(p['zhi'] for p in chart.get('pillars', []) if 'zhi' in p)
    for dy in chart.get('dayun_list', []):
        dayun_zhi = dy.get('ganzhi', '')[1] if len(dy.get('ganzhi', '')) >= 2 else ''
        combined_zhis = yuanju_zhis | ({dayun_zhi} if dayun_zhi else set())
        for ln in dy.get('liu_nian', []):
            if years_to_predict and ln['year'] not in years_to_predict:
                continue
            analysis = _analyze_ganzhi_luck(
                ln.get('ganzhi', ''),
                ln.get('gan_shishen', ''),
                ln.get('zhi_shishen', ''),
                yong_shen, ji_shen,
                label=f"{ln['year']}年{ln.get('ganzhi','')}（虚岁{ln.get('age','')}）",
                yuanju_zhis=combined_zhis,
            )
            analysis['year'] = ln['year']
            analysis['age']  = ln.get('age', '')
            predictions.append(analysis)

    return predictions


def format_luck_cycle_report(chart: dict, current_year: int = None) -> str:
    """
    生成大运流年分析文字报告。
    接收 bazi_chart 的完整输出。
    """
    import datetime
    cur_year = current_year or chart.get('current_year') or datetime.date.today().year

    lines = []

    # 经典理论依据（来自 classic-wisdom.json）
    lines.append(f"【理论依据】《三命通会》：「{DAYUN_THEORY}」")
    lines.append(f"《穷通宝鉴》：「{FUGUI_THEORY}」")
    lines.append("")

    # 起运信息
    qiyun = chart.get('qiyun', {})
    lines.append(f"▶ 大运排法：{qiyun.get('direction', '')}，{qiyun.get('description', '')}")
    lines.append("")

    # 大运一览
    lines.append("▶ 大运一览：")
    for dy in chart.get('dayun_list', []):
        marker = " ← 当前" if dy.get('is_current') else ""
        lines.append(
            f"  {dy['ganzhi']}运（{dy['start_year']}-{dy['end_year']}，"
            f"虚岁{dy['start_age']}-{dy['end_age']}）{marker}"
        )

    # 当前大运深度分析
    current = chart.get('current', {})
    yong_shen_info = chart.get('yong_shen', {})
    yong_shen = yong_shen_info.get('yong_shen', '')
    ji_shen   = yong_shen_info.get('ji_shen', [])
    pillars_list = chart.get('pillars', [])
    yuanju_zhis = frozenset(p['zhi'] for p in pillars_list if 'zhi' in p)
    gender = chart.get('meta', {}).get('gender', 'unknown')

    if current:
        dy = current.get('dayun', {})
        dy_gz = dy.get('ganzhi', '')
        lines.append("")
        lines.append(f"▶ 当前大运：{dy_gz}（{dy.get('start_year')}-{dy.get('end_year')}，虚岁{dy.get('start_age')}-{dy.get('end_age')}）")

        # 大运吉凶分析
        dayun_analysis = _analyze_ganzhi_luck(
            dy_gz,
            dy.get('gan_shishen', ''),
            dy.get('zhi_shishen', ''),
            yong_shen, ji_shen,
            label=f"{dy_gz}大运",
            yuanju_zhis=yuanju_zhis,
            gender=gender,
        )
        if dayun_analysis:
            lines.append(f"  大运评级：【{dayun_analysis['rating']}】（评分{dayun_analysis['score']}）")
            for note in dayun_analysis.get('notes', []):
                lines.append(f"  • {note}")
            aspects = dayun_analysis.get('aspects', {})
            if aspects:
                lines.append(f"  事业：{aspects.get('career', '')}  财运：{aspects.get('wealth', '')}  感情：{aspects.get('love', '')}")

        # 流年分析
        ly = current.get('liuyear', {})
        if ly:
            ly_gz = ly.get('ganzhi', '')
            dayun_zhi = dy_gz[1] if len(dy_gz) >= 2 else ''
            combined_zhis = yuanju_zhis | ({dayun_zhi} if dayun_zhi else set())
            liuyear_analysis = _analyze_ganzhi_luck(
                ly_gz,
                ly.get('gan_shishen', ''),
                ly.get('zhi_shishen', ''),
                yong_shen, ji_shen,
                label=f"{cur_year}年{ly_gz}流年",
                yuanju_zhis=combined_zhis,
                gender=gender,
            )
            lines.append("")
            lines.append(f"▶ 当前流年：{cur_year}年 {ly_gz}（虚岁{ly.get('age','')}）")
            if liuyear_analysis:
                lines.append(f"  流年评级：【{liuyear_analysis['rating']}】（评分{liuyear_analysis['score']}）")
                for note in liuyear_analysis.get('notes', []):
                    lines.append(f"  • {note}")
                aspects = liuyear_analysis.get('aspects', {})
                if aspects:
                    lines.append(f"  事业：{aspects.get('career', '')}  财运：{aspects.get('wealth', '')}  感情：{aspects.get('love', '')}")

            lines.append("  流月一览：")
            for lm in ly.get('liu_yue', []):
                lines.append(f"    {lm.get('month_cn','')}月 {lm.get('ganzhi','')}  天干十神:{lm.get('gan_shishen','')}")

    # 假从格动态评估
    if current:
        dy = current.get('dayun', {})
        ly = current.get('liuyear', {})
        jiacao = _assess_jiacao_shift(
            chart,
            dy.get('ganzhi', ''),
            ly.get('ganzhi', '') if ly else '',
        )
        if jiacao.get('is_jiacao'):
            lines.append("")
            lines.append("▶ 假从格动态评估：")
            lines.append(f"  {jiacao['note']}")
            if jiacao.get('trending_zhencong'):
                lines.append("  ⚡ 当前运年印星根气被大幅削弱，命局暂呈真从特征：")
                lines.append("    • 财官运势大旺，宜顺势而为，主动出击")
                lines.append("    • 切忌逆势而动，此时印比大运来救反为凶")
            elif jiacao.get('weakened_roots'):
                lines.append("  印星根气部分削弱，财官运势有所增强，但仍需谨慎。")
            if jiacao.get('intact_roots'):
                intact_desc = '、'.join(
                    f"{r['zhi']}中{r['gan']}（{r['level']}）"
                    for r in jiacao['intact_roots']
                )
                lines.append(f"  仍有完好根气：{intact_desc}，假从格未完全转变。")

    return '\n'.join(lines)

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
