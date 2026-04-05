#!/usr/bin/env python3
"""
bazi_with_five_yun.py - 八字+五运集成分析脚本

在八字精批基础上，对当前大运进行五个维度的深度分析（五运概览），
并将分析结果作为第八模块追加到报告中。

用法：
    python3 bazi_with_five_yun.py --year 1990 --month 1 --day 15 --hour 8 --gender male
    python3 bazi_with_five_yun.py --year 1990 --month 1 --day 15 --hour 8 --gender female --city Shanghai

参数与 bazi_analyzer.py 完全兼容，额外支持 --city（暂备用，不影响计算）。

输出：增强型 JSON（stdout），包含 five_yun_summary 字段及扩展后的 full_report。
"""

import argparse
import json
import sys
import os
import datetime

# 将技能目录加入模块搜索路径，以便导入同目录下的模块
_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SKILL_DIR)

from bazi_analyzer import analyze as bazi_analyze
from fortune_analyzer import BaziFortuneAnalyzer
from lib.ganzhi_calculator import (
    EARTHLY_BRANCHES, STEM_ELEMENTS, calculate_four_pillars,
)
from lib.luck_cycle_analyzer import calculate_luck_cycles, analyze_current_luck


# ── 纳音查找表（六十甲子纳音） ─────────────────────────────────────

_NAYIN_PAIRS = [
    (('甲子', '乙丑'), '海中金'),
    (('丙寅', '丁卯'), '炉中火'),
    (('戊辰', '己巳'), '大林木'),
    (('庚午', '辛未'), '路旁土'),
    (('壬申', '癸酉'), '剑锋金'),
    (('甲戌', '乙亥'), '山头火'),
    (('丙子', '丁丑'), '涧下水'),
    (('戊寅', '己卯'), '城头土'),
    (('庚辰', '辛巳'), '白蜡金'),
    (('壬午', '癸未'), '杨柳木'),
    (('甲申', '乙酉'), '泉中水'),
    (('丙戌', '丁亥'), '屋上土'),
    (('戊子', '己丑'), '霹雳火'),
    (('庚寅', '辛卯'), '松柏木'),
    (('壬辰', '癸巳'), '长流水'),
    (('甲午', '乙未'), '砂中金'),
    (('丙申', '丁酉'), '山下火'),
    (('戊戌', '己亥'), '平地木'),
    (('庚子', '辛丑'), '壁上土'),
    (('壬寅', '癸卯'), '金箔金'),
    (('甲辰', '乙巳'), '覆灯火'),
    (('丙午', '丁未'), '天河水'),
    (('戊申', '己酉'), '大驿土'),
    (('庚戌', '辛亥'), '钗钏金'),
    (('壬子', '癸丑'), '桑柘木'),
    (('甲寅', '乙卯'), '大溪水'),
    (('丙辰', '丁巳'), '沙中土'),
    (('戊午', '己未'), '天上火'),
    (('庚申', '辛酉'), '石榴木'),
    (('壬戌', '癸亥'), '大海水'),
]

NAYIN_LOOKUP = {}
for (gz1, gz2), nayin in _NAYIN_PAIRS:
    NAYIN_LOOKUP[gz1] = nayin
    NAYIN_LOOKUP[gz2] = nayin


# ── 十二长生宫：日主五行 → 地支 → 旺衰阶段 ────────────────────────

_LIFE_STAGES = [
    '长生', '沐浴', '冠带', '临官', '帝旺',
    '衰',   '病',   '死',   '墓',   '绝',   '胎', '养',
]

# 各五行长生起始地支（顺数）
_CHANG_SHENG_START = {
    '木': '亥',
    '火': '寅',
    '土': '寅',   # 戊己土按火行计（传统阳土同火长生）
    '金': '巳',
    '水': '申',
}


def get_wangshuai(day_master_element, cycle_branch):
    """
    计算大运地支相对于日主元素的十二长生阶段。

    返回如 '长生'、'临官'、'帝旺'、'衰'、'病'、'死'、'墓'、'绝' 等。
    """
    start_branch = _CHANG_SHENG_START.get(day_master_element)
    if not start_branch or cycle_branch not in EARTHLY_BRANCHES:
        return '平'
    start_idx = EARTHLY_BRANCHES.index(start_branch)
    branch_idx = EARTHLY_BRANCHES.index(cycle_branch)
    stage_idx = (branch_idx - start_idx) % 12
    return _LIFE_STAGES[stage_idx]


# ── 干支关系映射 ───────────────────────────────────────────────────

_CHONG_MAP = {
    '子': '午', '午': '子', '丑': '未', '未': '丑',
    '寅': '申', '申': '寅', '卯': '酉', '酉': '卯',
    '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳',
}

_HE_BRANCH_MAP = {
    '子': '丑', '丑': '子', '寅': '亥', '亥': '寅',
    '卯': '戌', '戌': '卯', '辰': '酉', '酉': '辰',
    '巳': '申', '申': '巳', '午': '未', '未': '午',
}

_HE_STEM_MAP = {
    '甲': '己', '己': '甲',
    '乙': '庚', '庚': '乙',
    '丙': '辛', '辛': '丙',
    '丁': '壬', '壬': '丁',
    '戊': '癸', '癸': '戊',
}

_XING_MAP = {
    '寅': ['巳', '申'], '巳': ['申', '寅'], '申': ['寅', '巳'],
    '丑': ['戌', '未'], '戌': ['未', '丑'], '未': ['丑', '戌'],
    '子': ['卯'], '卯': ['子'],
    '辰': ['辰'], '午': ['午'], '酉': ['酉'], '亥': ['亥'],
}

_HAI_MAP = {
    '子': '未', '未': '子',
    '丑': '午', '午': '丑',
    '寅': '巳', '巳': '寅',
    '卯': '辰', '辰': '卯',
    '申': '亥', '亥': '申',
    '酉': '戌', '戌': '酉',
}

# ── 五运模块展示配置 ───────────────────────────────────────────────

_DIM_LABELS = {
    'intimate':  '一、感情运',
    'wealth':    '二、财　运',
    'children':  '三、子　运',
    'official':  '四、禄　运',
    'longevity': '五、寿　运',
}

_STATUS_ICONS = {'吉': '✅', '平': '⚖️', '凶': '⚠️'}


def compute_cycle_relations(cycle_stem, cycle_branch, pillars):
    """
    计算大运干支与命局四柱的刑冲合害关系。

    参数：
        cycle_stem:   大运天干
        cycle_branch: 大运地支
        pillars:      简化四柱结构，每个柱含 {'stem': ..., 'branch': ...}

    返回：
        {'chong': [...], 'xing': [...], 'hai': [...], 'he': [...], 'po': []}
    """
    chong, xing, hai, he = [], [], [], []

    natal_branches = [
        pillars['year_pillar']['branch'],
        pillars['month_pillar']['branch'],
        pillars['day_pillar']['branch'],
        pillars['hour_pillar']['branch'],
    ]
    natal_stems = [
        pillars['year_pillar']['stem'],
        pillars['month_pillar']['stem'],
        pillars['day_pillar']['stem'],
        pillars['hour_pillar']['stem'],
    ]

    # 地支六冲
    chong_target = _CHONG_MAP.get(cycle_branch)
    if chong_target:
        for b in natal_branches:
            if b == chong_target:
                chong.append(b)

    # 地支六合
    he_branch_target = _HE_BRANCH_MAP.get(cycle_branch)
    if he_branch_target:
        for b in natal_branches:
            if b == he_branch_target:
                he.append(b)

    # 天干合
    he_stem_target = _HE_STEM_MAP.get(cycle_stem)
    if he_stem_target:
        for s in natal_stems:
            if s == he_stem_target:
                he.append(s)

    # 地支六刑
    xing_targets = _XING_MAP.get(cycle_branch, [])
    for b in natal_branches:
        if b in xing_targets:
            xing.append(b)

    # 地支六害
    hai_target = _HAI_MAP.get(cycle_branch)
    if hai_target:
        for b in natal_branches:
            if b == hai_target:
                hai.append(b)

    return {
        'chong': list(set(chong)),
        'xing':  list(set(xing)),
        'hai':   list(set(hai)),
        'he':    list(set(he)),
        'po':    [],
    }


def _split_gz(gz_str):
    """将干支字符串拆分为 (天干, 地支) 元组。"""
    if len(gz_str) >= 2:
        return gz_str[0], gz_str[1]
    return gz_str, ''


def build_five_yun_module(bazi_pillars, full_report, luck_cycles_data):
    """
    构建五运概览模块（第八模块）。

    参数：
        bazi_pillars:     四柱干支字典 {'year': '甲子', 'month': ..., 'day': ..., 'hour': ...}
        full_report:      已生成的完整八字精批报告文字
        luck_cycles_data: calculate_luck_cycles() 返回的结构

    返回：
        (five_yun_results, five_yun_text)
        five_yun_results: 字典，键为维度名，值为 BaziFortuneAnalyzer.analyze() 的返回值
        five_yun_text:    模块文字（可直接追加到 full_report）
    """
    current_cycle = analyze_current_luck(luck_cycles_data, datetime.date.today().year)
    if not current_cycle:
        return {}, '（当前未处于大运期，五运概览不可用）'

    gz        = current_cycle['gz']
    stem      = current_cycle['stem']
    branch    = current_cycle['branch']
    age_start = current_cycle.get('age_start', 0)

    # 纳音
    nayin = NAYIN_LOOKUP.get(gz, '')

    # 日主元素（用于计算旺衰）
    day_gz             = bazi_pillars.get('day', '')
    day_stem_char      = day_gz[0] if day_gz else ''
    day_master_element = STEM_ELEMENTS.get(day_stem_char, '')

    # 旺衰
    wangshuai = get_wangshuai(day_master_element, branch)

    # 构建简化四柱结构，供 compute_cycle_relations 使用
    year_stem,  year_branch  = _split_gz(bazi_pillars.get('year',  ''))
    month_stem, month_branch = _split_gz(bazi_pillars.get('month', ''))
    day_stem_p, day_branch   = _split_gz(bazi_pillars.get('day',   ''))
    hour_stem,  hour_branch  = _split_gz(bazi_pillars.get('hour',  ''))

    simple_pillars = {
        'year_pillar':  {'stem': year_stem,   'branch': year_branch},
        'month_pillar': {'stem': month_stem,  'branch': month_branch},
        'day_pillar':   {'stem': day_stem_p,  'branch': day_branch},
        'hour_pillar':  {'stem': hour_stem,   'branch': hour_branch},
    }

    relations = compute_cycle_relations(stem, branch, simple_pillars)

    cycle_for_analyzer = {
        'age':       age_start,
        'ganzhi':    gz,
        'wangshuai': wangshuai,
        'nayin':     nayin,
        'relations': relations,
    }

    analyzer = BaziFortuneAnalyzer(bazi_pillars, full_report)
    dimensions = ['intimate', 'wealth', 'children', 'official', 'longevity']
    five_yun_results = {}
    for dim in dimensions:
        five_yun_results[dim] = analyzer.analyze(dim, cycle_for_analyzer)

    # 构建文字摘要
    separator = '═' * 50
    thin_sep  = '─' * 40
    lines = ['', separator]
    lines.append(f'【八】五运概览（当前大运 {gz}，{age_start}岁起）')
    lines.append(separator)
    lines.append(f'当前大运：{gz}  旺衰：{wangshuai}  纳音：{nayin}')
    lines.append('')

    for dim in dimensions:
        res    = five_yun_results[dim]
        icon   = _STATUS_ICONS.get(res['status'], '')
        label  = _DIM_LABELS.get(dim, res['name'])
        lines.append(f'{label}  {icon} {res["status"]}')
        lines.append(thin_sep)
        for insight in res['insights']:
            lines.append(f'  · {insight}')
        lines.append('')

    lines.append(separator)

    five_yun_text = '\n'.join(lines)
    return five_yun_results, five_yun_text


def parse_args():
    parser = argparse.ArgumentParser(description='八字+五运集成分析 - 包含五运概览第八模块')
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
                        help='指定流年预测年份（如 2025 2026 2027）')
    parser.add_argument('--city',   default='',
                        help='出生城市（暂备用，不影响计算结果）')
    return parser.parse_args()


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
        # 1. 获取基础八字精批报告
        base_result = bazi_analyze(
            year=args.year,
            month=args.month,
            day=args.day,
            hour=args.hour,
            gender=args.gender,
            level=args.level,
            years_to_predict=args.years,
        )

        if not base_result.get('success'):
            print(json.dumps(base_result, ensure_ascii=False))
            sys.exit(1)

        # 2. 提取四柱干支
        bazi_pillars = base_result['pillars']

        # 3. 计算大运（需要完整 pillars 结构）
        pillars_full     = calculate_four_pillars(args.year, args.month, args.day, args.hour)
        luck_cycles_data = calculate_luck_cycles(
            pillars_full, gender=args.gender, birth_year=args.year
        )

        # 4. 构建五运概览第八模块
        five_yun_results, five_yun_text = build_five_yun_module(
            bazi_pillars,
            base_result.get('full_report', ''),
            luck_cycles_data,
        )

        # 5. 将五运概览追加到 full_report
        enhanced_report = base_result.get('full_report', '') + '\n' + five_yun_text

        # 6. 构建输出 JSON
        result = dict(base_result)
        result['full_report']      = enhanced_report
        result['five_yun_summary'] = five_yun_results

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        import traceback
        print(f'[bazi_with_five_yun] 分析出错: {e}', file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        result = {'success': False, 'error': str(e)}
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
