#!/usr/bin/env python3
"""
bazi_analyzer.py - 八字精批 Skill 主入口

基于《子平真诠》《滴天髓》《渊海子平》《三命通会》《穷通宝鉴》等经典著作，
提供包含7个模块的完整八字精批分析报告。

用法：
    python3 bazi_analyzer.py --year 1990 --month 1 --day 15 --hour 8 --gender male
    python3 bazi_analyzer.py --year 1990 --month 1 --day 15 --hour 8 --level quick

输出：JSON 格式的精批报告（stdout），诊断日志写入 stderr。
"""

import argparse
import json
import sys
import os
import datetime

# 将 lib 目录加入模块搜索路径
_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SKILL_DIR)

from lib.ganzhi_calculator import (
    calculate_four_pillars, get_element_counts, get_daymaster_strength
)
from lib.ten_gods_analyzer import (
    analyze_ten_gods, get_dominant_ten_gods, identify_key_stars
)
from lib.format_analyzer import format_full_analysis
from lib.character_profiler import build_character_profile
from lib.six_relations_analyzer import analyze_six_relations
from lib.wealth_career_analyzer import analyze_wealth_career
from lib.health_predictor import predict_health
from lib.luck_cycle_analyzer import (
    calculate_luck_cycles, predict_yearly_fortune, format_luck_cycle_report,
    analyze_current_luck
)
from lib.advice_generator import generate_advice
from lib.ancient_books_fetcher import get_relevant_passages, format_passages_for_report


def parse_args():
    parser = argparse.ArgumentParser(description='八字精批分析 - 基于经典著作')
    parser.add_argument('--year',   required=True,  type=int, help='出生年（公历）')
    parser.add_argument('--month',  required=True,  type=int, help='出生月（1-12）')
    parser.add_argument('--day',    required=True,  type=int, help='出生日（1-31）')
    parser.add_argument('--hour',   default=0,       type=int, help='出生时辰（0-23，默认0）')
    parser.add_argument('--gender', default='unknown',
                        choices=['male', 'female', 'unknown'],
                        help='性别：male/female/unknown')
    parser.add_argument('--level',  default='full',
                        choices=['full', 'quick'],
                        help='分析深度：full（完整精批）/ quick（快速分析）')
    parser.add_argument('--years',  nargs='*', type=int,
                        help='指定流年预测年份（如 2025 2026 2027），不指定则预测未来3年')
    return parser.parse_args()


def format_pillar_display(pillar):
    """格式化单柱显示"""
    hidden = pillar.get('hidden_stems', [])
    hidden_str = f"藏{'/'.join(hidden)}" if hidden else '无藏干'
    return f"{pillar['gz']}（{pillar['stem_element']}/{pillar['branch_element']}，{hidden_str}）"


def build_full_report(pillars, ten_gods_analysis, format_analysis, character_profile,
                      six_relations, wealth_career, health_info, luck_info, advice,
                      birth_info, gender, level='full'):
    """
    构建完整精批报告文字
    """
    lines = []
    separator = '═' * 50

    lines.append(separator)
    lines.append('          ✦ 八字精批报告 ✦')
    lines.append(separator)

    birth_str = (f"{birth_info['year']}年{birth_info['month']}月"
                 f"{birth_info['day']}日 {birth_info['hour']}时")
    gender_str = {'male': '男', 'female': '女', 'unknown': '未知'}[gender]
    lines.append(f"生辰：{birth_str}  性别：{gender_str}")
    lines.append(f"生肖：{pillars['zodiac']}")
    lines.append('')

    # ── 第一模块：基础命盘 ──────────────────────────────
    lines.append('【一】基础命盘排布与定格')
    lines.append('─' * 40)

    # 四柱展示
    for col, key in [('年柱', 'year_pillar'), ('月柱', 'month_pillar'),
                     ('日柱', 'day_pillar'), ('时柱', 'hour_pillar')]:
        lines.append(f"  {col}：{format_pillar_display(pillars[key])}")

    lines.append('')
    lines.append(f"  日主：{pillars['day_master']}（{pillars['day_master_element']}）")

    # 十神
    lines.append('')
    lines.append('  十神关系：')
    for key, data in ten_gods_analysis.items():
        label = data['label']
        stem_tg = data['stem_ten_god']
        hidden_str = '  '.join(f"{h['stem']}={h['ten_god']}" for h in data['branch_hidden'])
        lines.append(f"    {label}：天干 {data['stem']}（{stem_tg}）  地支 {data['branch']}[{hidden_str}]")

    lines.append('')
    # 格局与用神
    lines.append(format_analysis.get('summary', ''))

    if level == 'full':
        # 古籍参考
        format_name = format_analysis.get('format', {}).get('format_name', '')
        passages = get_relevant_passages(format_name,
                                          day_master=pillars['day_master'],
                                          format_name=format_name)
        if passages:
            lines.append('')
            lines.append(format_passages_for_report(passages, topic=format_name))

    lines.append('')

    # ── 第二模块：性格画像 ──────────────────────────────
    lines.append('【二】性格特质深度画像')
    lines.append('─' * 40)
    lines.append(character_profile.get('summary', ''))

    lines.append('')

    # ── 第三模块：六亲关系 ──────────────────────────────
    lines.append('【三】六亲关系与社会脉络')
    lines.append('─' * 40)
    lines.append(six_relations.get('summary', ''))

    lines.append('')

    # ── 第四模块：事业财运 ──────────────────────────────
    lines.append('【四】事业财运分析')
    lines.append('─' * 40)
    lines.append(wealth_career.get('summary', ''))

    if level == 'full':
        passages = get_relevant_passages('财星', day_master=pillars['day_master'])
        if passages:
            lines.append('')
            lines.append(format_passages_for_report(passages, topic='财星与求财'))

    lines.append('')

    # ── 第五模块：健康预警 ──────────────────────────────
    lines.append('【五】身体健康预警')
    lines.append('─' * 40)
    lines.append(health_info.get('summary', ''))

    lines.append('')

    # ── 第六模块：大运流年 ──────────────────────────────
    lines.append('【六】大运与流年预测')
    lines.append('─' * 40)
    lines.append(luck_info.get('report', ''))

    lines.append('')

    # ── 第七模块：趋吉避凶 ──────────────────────────────
    lines.append('【七】趋吉避凶建议')
    lines.append('─' * 40)
    lines.append(advice.get('summary', ''))

    lines.append('')
    lines.append(separator)
    lines.append('  ⚠ 本报告基于传统命理学，仅供参考。')
    lines.append('  命运在于自身努力，知命不认命，逢凶化吉。')
    lines.append(separator)

    return '\n'.join(lines)


def analyze(year, month, day, hour, gender='unknown', level='full', years_to_predict=None):
    """
    执行完整八字精批分析
    返回包含结构化数据和文字报告的字典
    """
    # ── 1. 四柱干支计算 ────────────────────────────────
    pillars = calculate_four_pillars(year, month, day, hour)

    # ── 2. 十神分析 ────────────────────────────────────
    ten_gods_analysis = analyze_ten_gods(pillars)
    dominant_ten_gods = get_dominant_ten_gods(ten_gods_analysis)
    key_stars = identify_key_stars(ten_gods_analysis, pillars)

    # ── 3. 格局判断与用神 ──────────────────────────────
    format_analysis = format_full_analysis(pillars, ten_gods_analysis)
    yong_shen_info = format_analysis.get('yong_shen', {})

    # ── 4. 性格画像 ────────────────────────────────────
    character_profile = build_character_profile(
        pillars, ten_gods_analysis, format_analysis, dominant_ten_gods
    )

    # ── 5. 六亲分析 ────────────────────────────────────
    six_relations = analyze_six_relations(
        pillars, ten_gods_analysis, yong_shen_info, gender
    )

    # ── 6. 财富事业 ────────────────────────────────────
    wealth_career = analyze_wealth_career(
        pillars, ten_gods_analysis, format_analysis, yong_shen_info
    )

    # ── 7. 健康预警 ────────────────────────────────────
    health_info = predict_health(pillars, yong_shen_info)

    # ── 8. 大运流年 ────────────────────────────────────
    luck_cycles = calculate_luck_cycles(pillars, gender=gender, birth_year=year)
    if years_to_predict is None:
        this_year = datetime.date.today().year
        years_to_predict = [this_year, this_year + 1, this_year + 2]
    yearly_predictions = predict_yearly_fortune(
        pillars, ten_gods_analysis, yong_shen_info, years_to_predict
    )
    current_cycle = analyze_current_luck(luck_cycles, datetime.date.today().year)
    luck_report = format_luck_cycle_report(luck_cycles, yearly_predictions)
    luck_info = {
        'cycles': luck_cycles,
        'current_cycle': current_cycle,
        'yearly_predictions': yearly_predictions,
        'report': luck_report,
    }

    # ── 9. 趋吉避凶 ────────────────────────────────────
    advice = generate_advice(pillars, yong_shen_info, format_analysis)

    # ── 10. 生成报告 ───────────────────────────────────
    report_text = build_full_report(
        pillars, ten_gods_analysis, format_analysis, character_profile,
        six_relations, wealth_career, health_info, luck_info, advice,
        pillars['birth_info'], gender, level
    )

    return {
        'success': True,
        'birth_info': pillars['birth_info'],
        'gender': gender,
        'level': level,
        'pillars': {
            'year': pillars['year_pillar']['gz'],
            'month': pillars['month_pillar']['gz'],
            'day': pillars['day_pillar']['gz'],
            'hour': pillars['hour_pillar']['gz'],
        },
        'day_master': pillars['day_master'],
        'day_master_element': pillars['day_master_element'],
        'zodiac': pillars['zodiac'],
        'format': format_analysis.get('format', {}).get('format_name', ''),
        'strength': yong_shen_info.get('strength', ''),
        'yong_shen': yong_shen_info.get('yong_shen', ''),
        'ji_shen': yong_shen_info.get('ji_shen', []),
        'dominant_ten_gods': [{'ten_god': tg, 'weight': w} for tg, w in dominant_ten_gods[:5]],
        'character_summary': character_profile.get('summary', ''),
        'six_relations_summary': six_relations.get('summary', ''),
        'wealth_summary': wealth_career.get('summary', ''),
        'health_summary': health_info.get('summary', ''),
        'luck_summary': luck_report,
        'advice_summary': advice.get('summary', ''),
        'full_report': report_text,
        'generated_at': datetime.datetime.now().isoformat(),
    }


def main():
    args = parse_args()

    # 输入校验
    errors = []
    if not (1 <= args.month <= 12):
        errors.append(f'月份无效：{args.month}（应为1-12）')
    if not (1 <= args.day <= 31):
        errors.append(f'日期无效：{args.day}（应为1-31）')
    if not (0 <= args.hour <= 23):
        errors.append(f'时辰无效：{args.hour}（应为0-23）')
    if not (1800 <= args.year <= 2100):
        errors.append(f'年份超出支持范围：{args.year}（应为1800-2100）')

    if errors:
        result = {'success': False, 'error': '输入参数错误：' + '；'.join(errors)}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    try:
        result = analyze(
            year=args.year,
            month=args.month,
            day=args.day,
            hour=args.hour,
            gender=args.gender,
            level=args.level,
            years_to_predict=args.years,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        import traceback
        print(f'[bazi_analyzer] 分析出错: {e}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        result = {'success': False, 'error': str(e)}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
