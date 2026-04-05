#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bazi_with_five_yun.py - 八字精批 + 五运深度分析集成脚本

在原有7个模块的基础上添加第八模块：五运深度分析概览。

用法：
    python3 bazi_with_five_yun.py --year 1990 --month 1 --day 15 --hour 8 --gender male
    python3 bazi_with_five_yun.py --year 1985 --month 6 --day 20 --hour 14 --gender female

输出：JSON 格式，包含 five_yun_summary 和增强型 full_report（stdout）。
"""

import argparse
import json
import sys
import os
import datetime

# 将 skill 目录加入模块搜索路径
_SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SKILL_DIR)

from bazi_analyzer import analyze
from fortune_analyzer import BaziFortuneAnalyzer
from lib.ganzhi_calculator import (
    HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_POLARITY,
)

# ── 纳音对照表（60甲子） ────────────────────────────────────────────

NAYIN_TABLE = {
    '甲子': '海中金', '乙丑': '海中金',
    '丙寅': '炉中火', '丁卯': '炉中火',
    '戊辰': '大林木', '己巳': '大林木',
    '庚午': '路旁土', '辛未': '路旁土',
    '壬申': '剑锋金', '癸酉': '剑锋金',
    '甲戌': '山头火', '乙亥': '山头火',
    '丙子': '涧下水', '丁丑': '涧下水',
    '戊寅': '城头土', '己卯': '城头土',
    '庚辰': '白蜡金', '辛巳': '白蜡金',
    '壬午': '杨柳木', '癸未': '杨柳木',
    '甲申': '泉中水', '乙酉': '泉中水',
    '丙戌': '屋上土', '丁亥': '屋上土',
    '戊子': '霹雳火', '己丑': '霹雳火',
    '庚寅': '松柏木', '辛卯': '松柏木',
    '壬辰': '长流水', '癸巳': '长流水',
    '甲午': '砂中金', '乙未': '砂中金',
    '丙申': '山下火', '丁酉': '山下火',
    '戊戌': '平地木', '己亥': '平地木',
    '庚子': '壁上土', '辛丑': '壁上土',
    '壬寅': '金箔金', '癸卯': '金箔金',
    '甲辰': '覆灯火', '乙巳': '覆灯火',
    '丙午': '天河水', '丁未': '天河水',
    '戊申': '大驿土', '己酉': '大驿土',
    '庚戌': '钗钏金', '辛亥': '钗钏金',
    '壬子': '桑柘木', '癸丑': '桑柘木',
    '甲寅': '大溪水', '乙卯': '大溪水',
    '丙辰': '沙中土', '丁巳': '沙中土',
    '戊午': '天上火', '己未': '天上火',
    '庚申': '石榴木', '辛酉': '石榴木',
    '壬戌': '大海水', '癸亥': '大海水',
}

# ── 十二长生起点表 ──────────────────────────────────────────────────
# (起长生的地支索引, 是否顺排)
# 阳干顺排，阴干逆排

_BRANCHES = EARTHLY_BRANCHES  # ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

CHANG_SHENG_MAP = {
    '甲': (11, True),   # 亥 index=11, 顺排
    '乙': (6,  False),  # 午 index=6,  逆排
    '丙': (2,  True),   # 寅 index=2,  顺排
    '丁': (9,  False),  # 酉 index=9,  逆排
    '戊': (2,  True),   # 寅 index=2,  顺排
    '己': (9,  False),  # 酉 index=9,  逆排
    '庚': (5,  True),   # 巳 index=5,  顺排
    '辛': (0,  False),  # 子 index=0,  逆排
    '壬': (8,  True),   # 申 index=8,  顺排
    '癸': (3,  False),  # 卯 index=3,  逆排
}

# 临官在标准典籍中亦称"建禄"，统一用"建禄"呈现
TWELVE_STAGES = ['长生', '沐浴', '冠带', '建禄', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养']

# 强度标签映射
STRENGTH_LABELS = {
    '帝旺': '至强',
    '建禄': '强',
    '长生': '较强', '冠带': '较强',
    '沐浴': '中',   '衰': '中', '养': '中', '胎': '中',
    '病':   '弱',   '死': '弱', '墓': '弱', '绝': '极弱',
}

# 旺衰描述
WANGSHUAI_DESC = {
    '长生': '长生（生机勃发，蓄势而起）',
    '沐浴': '沐浴（气势柔弱，需磨砺蜕变）',
    '冠带': '冠带（成长有为，逐步建立声望）',
    '建禄': '建禄（禄旺身强，正当其时）',
    '帝旺': '帝旺（巅峰至强，声势最盛）',
    '衰':   '衰（气势渐减，宜守成不进）',
    '病':   '病（精力耗散，需调养蓄力）',
    '死':   '死（气息收藏，等待转机）',
    '墓':   '墓（收藏沉潜，厚积薄发）',
    '绝':   '绝（旧气已绝，等待新生）',
    '胎':   '胎（孕育新机，变革萌动）',
    '养':   '养（休养生息，积蓄能量）',
}

# 纳音特质简述
NAYIN_DESC = {
    '海中金': '主深藏内敛，大器晚成',
    '炉中火': '主锻炼磨砺，刚烈果断',
    '大林木': '主茂盛繁荣，广纳人脉',
    '路旁土': '主广博包容，踏实奉献',
    '剑锋金': '主收敛，主决断',
    '山头火': '主光明显达，志向高远',
    '涧下水': '主深流不息，智慧内敛',
    '城头土': '主稳固守成，重视根基',
    '白蜡金': '主可塑性强，温柔细腻',
    '杨柳木': '主柔韧随和，随机应变',
    '泉中水': '主源源不断，生命力强',
    '屋上土': '主安稳居家，守护家业',
    '霹雳火': '主震动变革，行动迅猛',
    '松柏木': '主坚韧不拔，长青长寿',
    '长流水': '主流动四方，广泛人脉',
    '砂中金': '主内敛含蓄，踏实积累',
    '山下火': '主内蕴热情，温暖他人',
    '平地木': '主平和宽广，利于发展',
    '壁上土': '主稳健朴实，耐力强',
    '金箔金': '主外在光鲜，注重形象',
    '覆灯火': '主温柔照耀，亲和力强',
    '天河水': '主广施恩泽，上善若水',
    '大驿土': '主奔走四方，适应力强',
    '钗钏金': '主精致华美，贵气十足',
    '桑柘木': '主实用务实，踏实肯干',
    '大溪水': '主宽广包容，随机应变',
    '沙中土': '主变动不拘，善于应变',
    '天上火': '主光明正大，志向远大',
    '石榴木': '主内结其实，利于后代',
    '大海水': '主深沉广博，器量宏大',
}

# 干支六合（地支）
BRANCH_HE_MAP = {
    '子': '丑', '丑': '子',
    '寅': '亥', '亥': '寅',
    '卯': '戌', '戌': '卯',
    '辰': '酉', '酉': '辰',
    '巳': '申', '申': '巳',
    '午': '未', '未': '午',
}

# 天干五合
STEM_HE_MAP = {
    '甲': '己', '己': '甲',
    '乙': '庚', '庚': '乙',
    '丙': '辛', '辛': '丙',
    '丁': '壬', '壬': '丁',
    '戊': '癸', '癸': '戊',
}

# 地支六冲
BRANCH_CHONG_MAP = {
    '子': '午', '午': '子',
    '丑': '未', '未': '丑',
    '寅': '申', '申': '寅',
    '卯': '酉', '酉': '卯',
    '辰': '戌', '戌': '辰',
    '巳': '亥', '亥': '巳',
}

# 地支六害
BRANCH_HAI_MAP = {
    '子': '未', '未': '子',
    '丑': '午', '午': '丑',
    '寅': '巳', '巳': '寅',
    '卯': '辰', '辰': '卯',
    '申': '亥', '亥': '申',
    '酉': '戌', '戌': '酉',
}

# 地支相刑（三刑）
BRANCH_XING_MAP = {
    '寅': ['巳', '申'],
    '巳': ['寅', '申'],
    '申': ['寅', '巳'],
    '丑': ['戌', '未'],
    '戌': ['丑', '未'],
    '未': ['丑', '戌'],
    '子': ['卯'],
    '卯': ['子'],
    '辰': ['辰'],
    '午': ['午'],
    '酉': ['酉'],
    '亥': ['亥'],
}


# ── 工具函数 ────────────────────────────────────────────────────────


def get_nayin(ganzhi):
    """获取干支的纳音名称"""
    return NAYIN_TABLE.get(ganzhi, '')


def get_wangshuai(day_stem, cycle_branch):
    """
    计算大运/流年地支相对于日主天干的十二长生状态。

    参数：
        day_stem:     日主天干（如 '庚'）
        cycle_branch: 大运或流年地支（如 '申'）

    返回：十二长生状态字符串（如 '建禄'）
    """
    if day_stem not in CHANG_SHENG_MAP:
        return ''
    start_idx, is_forward = CHANG_SHENG_MAP[day_stem]
    branch_idx = _BRANCHES.index(cycle_branch) if cycle_branch in _BRANCHES else -1
    if branch_idx < 0:
        return ''
    if is_forward:
        stage_idx = (branch_idx - start_idx) % 12
    else:
        stage_idx = (start_idx - branch_idx) % 12
    return TWELVE_STAGES[stage_idx]


def get_relations(cycle_stem, cycle_branch, pillars):
    """
    计算大运天干地支与命局四柱的刑冲害合关系。

    返回格式与 BaziFortuneAnalyzer.analyze() 期望的 relations 字段一致：
        {"chong": [...], "xing": [...], "hai": [...], "he": [...], "po": []}
    """
    natal_stems = [
        pillars['year_pillar']['stem'],
        pillars['month_pillar']['stem'],
        pillars['day_pillar']['stem'],
        pillars['hour_pillar']['stem'],
    ]
    natal_branches = [
        pillars['year_pillar']['branch'],
        pillars['month_pillar']['branch'],
        pillars['day_pillar']['branch'],
        pillars['hour_pillar']['branch'],
    ]

    chong = []
    xing  = []
    hai   = []
    he    = []
    po    = []

    # 地支六冲
    chong_target = BRANCH_CHONG_MAP.get(cycle_branch)
    if chong_target and chong_target in natal_branches:
        chong.append(chong_target)

    # 地支六害
    hai_target = BRANCH_HAI_MAP.get(cycle_branch)
    if hai_target and hai_target in natal_branches:
        hai.append(hai_target)

    # 地支相刑
    xing_targets = BRANCH_XING_MAP.get(cycle_branch, [])
    for xt in xing_targets:
        if xt in natal_branches:
            xing.append(xt)

    # 地支六合
    he_branch = BRANCH_HE_MAP.get(cycle_branch)
    if he_branch and he_branch in natal_branches:
        he.append(he_branch)

    # 天干五合
    he_stem = STEM_HE_MAP.get(cycle_stem)
    if he_stem and he_stem in natal_stems:
        he.append(he_stem)

    return {'chong': chong, 'xing': xing, 'hai': hai, 'he': he, 'po': po}


def build_cycle_object(cycle, day_stem, pillars):
    """
    从 luck_cycle_analyzer 的大运数据构建 BaziFortuneAnalyzer 所需的 cycle 对象。
    """
    ganzhi = cycle['gz']
    stem   = cycle['stem']
    branch = cycle['branch']
    return {
        'age':       cycle['age_start'],
        'ganzhi':    ganzhi,
        'wangshuai': get_wangshuai(day_stem, branch),
        'nayin':     get_nayin(ganzhi),
        'relations': get_relations(stem, branch, pillars),
    }


def build_liunya_cycle_object(year_pred, day_stem, pillars):
    """
    从 predict_yearly_fortune 的流年数据构建用于展示的简化对象。
    """
    ganzhi = year_pred['gz']
    stem   = year_pred['stem']
    branch = year_pred['branch']
    return {
        'year':      year_pred['year'],
        'ganzhi':    ganzhi,
        'wangshuai': get_wangshuai(day_stem, branch),
        'nayin':     get_nayin(ganzhi),
    }


def get_recent_dayun(luck_cycles, current_year, count=3):
    """
    获取近 N 个大运（包含当前大运及之后的）。
    """
    cycles = luck_cycles.get('cycles', [])
    relevant = [c for c in cycles if c['year_end'] >= current_year]
    return relevant[:count]


def analyze_dayun_dimensions(cycle_obj, bazi_pillars):
    """
    对一个大运进行全部五个维度的分析。

    参数：
        cycle_obj:    由 build_cycle_object() 构建的大运对象
        bazi_pillars: calculate_four_pillars() 的返回值

    返回：dimensions 字典
    """
    bazi = {
        'year':  bazi_pillars['year_pillar']['gz'],
        'month': bazi_pillars['month_pillar']['gz'],
        'day':   bazi_pillars['day_pillar']['gz'],
        'hour':  bazi_pillars['hour_pillar']['gz'],
    }
    analyzer = BaziFortuneAnalyzer(bazi)
    dimensions = {}
    for dim in ('intimate', 'wealth', 'children', 'official', 'longevity'):
        result = analyzer.analyze(dim, cycle_obj)
        dimensions[dim] = {
            'status':       result['status'],
            'key_insights': result['insights'],
        }
    return dimensions


# 维度中文名
_DIM_NAMES = {
    'intimate':  '感情运',
    'wealth':    '财运',
    'children':  '子运',
    'official':  '禄运',
    'longevity': '寿运',
}


def _format_relations(relations):
    """将 relations 字典格式化为人类可读字符串"""
    parts = []
    rel_labels = {'chong': '冲', 'xing': '刑', 'hai': '害', 'he': '合', 'po': '破'}
    for key in ('he', 'chong', 'xing', 'hai', 'po'):
        items = relations.get(key, [])
        if items:
            parts.append(f"相{rel_labels[key]}{'、'.join(items)}")
    return '；'.join(parts) if parts else '无特殊关系'


def format_five_yun_summary(
    recent_dayun_analyzed,
    next_liunya_objects,
    birth_year,
    current_year,
):
    """
    生成第八模块五运深度分析概览的文字报告。

    参数：
        recent_dayun_analyzed: list of {cycle_obj, dimensions}
        next_liunya_objects:   list of liunya cycle objects
        birth_year:            出生年份（int）
        current_year:          当前年份（int）

    返回：格式化字符串
    """
    lines = []
    lines.append('【八】五运深度分析概览')
    lines.append('─' * 33)
    lines.append('')
    lines.append('📊 近3个大运分析')

    for item in recent_dayun_analyzed:
        co   = item['cycle_obj']
        dims = item['dimensions']

        strength     = STRENGTH_LABELS.get(co['wangshuai'], '中')
        ws_desc      = WANGSHUAI_DESC.get(co['wangshuai'], co['wangshuai'])
        nayin_desc   = NAYIN_DESC.get(co['nayin'], co['nayin'])
        rel_str      = _format_relations(co['relations'])

        lines.append(
            f"  • {co['age']}岁 {co['ganzhi']} ({co['wangshuai']}) 【{strength}】"
        )
        lines.append(f"    旺衰：{ws_desc}")
        lines.append(f"    纳音：{co['nayin']}（{nayin_desc}）")
        lines.append(f"    干支关系：{rel_str}")
        lines.append('')

        for dim_key, dim_name in _DIM_NAMES.items():
            dim_data = dims.get(dim_key, {})
            status   = dim_data.get('status', '平')
            insights = dim_data.get('key_insights', [])
            first    = insights[0] if insights else '平稳'
            lines.append(f"    {dim_name}：{first}")

        lines.append('')

    lines.append('📅 接下来3年流年展望')
    for lo in next_liunya_objects:
        age = lo['year'] - birth_year
        ws  = lo['wangshuai']
        lines.append(f"  • {lo['year']}年 {lo['ganzhi']} ({ws}) 年龄 {age}岁")

    lines.append('')
    lines.append('💡 五运追踪提示：')
    lines.append('可进一步咨询以下内容获得深度分析：')
    if recent_dayun_analyzed:
        lines.append('  • "分析第2个大运的感情运"')
    if next_liunya_objects:
        first_year = next_liunya_objects[0]['year']
        lines.append(f'  • "{first_year}年财运如何"')
    lines.append('  • "禄运要注意什么"')

    return '\n'.join(lines)


def build_five_yun_result(analyze_result, current_year=None):
    """
    在已有的 analyze() 返回值基础上叠加五运分析。

    参数：
        analyze_result: bazi_analyzer.analyze() 的完整返回值（含 pillars 原始数据）
        current_year:   当前年份，默认 datetime.date.today().year

    返回：增强后的结果字典（含 five_yun_summary / full_report）
    """
    if current_year is None:
        current_year = datetime.date.today().year

    # ── 重建 pillars（bazi_analyzer.analyze 内部已计算，这里重算以获原始结构） ──
    from lib.ganzhi_calculator import calculate_four_pillars
    from lib.luck_cycle_analyzer import (
        calculate_luck_cycles, predict_yearly_fortune,
    )
    from lib.format_analyzer import format_full_analysis
    from lib.ten_gods_analyzer import analyze_ten_gods

    birth = analyze_result['birth_info']
    pillars = calculate_four_pillars(
        birth['year'], birth['month'], birth['day'], birth['hour']
    )
    day_stem = pillars['day_master']
    gender   = analyze_result.get('gender', 'unknown')

    ten_gods_analysis = analyze_ten_gods(pillars)
    format_analysis   = format_full_analysis(pillars, ten_gods_analysis)
    yong_shen_info    = format_analysis.get('yong_shen', {})

    # ── 大运 ─────────────────────────────────────────────────────────
    luck_cycles = calculate_luck_cycles(
        pillars, gender=gender, birth_year=birth['year']
    )
    recent_cycles = get_recent_dayun(luck_cycles, current_year, count=3)

    # ── 流年（接下来3年） ──────────────────────────────────────────────
    next_years     = [current_year, current_year + 1, current_year + 2]
    yearly_preds   = predict_yearly_fortune(
        pillars, ten_gods_analysis, yong_shen_info, next_years
    )

    # ── 五运分析 ──────────────────────────────────────────────────────
    recent_dayun_analyzed = []
    recent_dayun_json     = []

    for cycle in recent_cycles:
        cycle_obj  = build_cycle_object(cycle, day_stem, pillars)
        dimensions = analyze_dayun_dimensions(cycle_obj, pillars)
        recent_dayun_analyzed.append({'cycle_obj': cycle_obj, 'dimensions': dimensions})

        # JSON-serializable 版本
        recent_dayun_json.append({
            'age':       cycle_obj['age'],
            'ganzhi':    cycle_obj['ganzhi'],
            'wangshuai': cycle_obj['wangshuai'],
            'nayin':     cycle_obj['nayin'],
            'relations': cycle_obj['relations'],
            'dimensions': {
                dim_key: {
                    'status':       dims['status'],
                    'key_insights': dims['key_insights'],
                }
                for dim_key, dims in dimensions.items()
            },
        })

    # 流年对象列表
    next_liunya_objects = [
        build_liunya_cycle_object(yp, day_stem, pillars)
        for yp in yearly_preds
    ]
    next_liunya_json = [
        {
            'year':      lo['year'],
            'ganzhi':    lo['ganzhi'],
            'wangshuai': lo['wangshuai'],
            'nayin':     lo['nayin'],
        }
        for lo in next_liunya_objects
    ]

    # ── 格式化摘要文字 ────────────────────────────────────────────────
    formatted_summary = format_five_yun_summary(
        recent_dayun_analyzed,
        next_liunya_objects,
        birth['year'],
        current_year,
    )

    five_yun_summary = {
        'recent_dayun':    recent_dayun_json,
        'next_liunya':     next_liunya_json,
        'formatted_summary': formatted_summary,
    }

    # ── 增强型完整报告（原报告 + 第八模块） ───────────────────────────
    original_report  = analyze_result.get('full_report', '')
    separator        = '═' * 50

    # 移除原报告末尾的分隔线，再拼接第八模块
    footer_lines = [
        separator,
        '  ⚠ 本报告基于传统命理学，仅供参考。',
        '  命运在于自身努力，知命不认命，逢凶化吉。',
        separator,
    ]
    footer_block = '\n'.join(footer_lines)
    if original_report.endswith(footer_block):
        report_body = original_report[: -len(footer_block)].rstrip('\n')
    else:
        report_body = original_report

    full_report = '\n'.join([
        report_body,
        '',
        formatted_summary,
        '',
        footer_block,
    ])

    # ── 合并输出 ──────────────────────────────────────────────────────
    result = dict(analyze_result)
    result['five_yun_summary'] = five_yun_summary
    result['full_report']      = full_report
    result['generated_at']     = datetime.datetime.now().isoformat()
    return result


# ── 参数解析 ────────────────────────────────────────────────────────


def parse_args():
    parser = argparse.ArgumentParser(
        description='八字精批 + 五运深度分析集成脚本'
    )
    parser.add_argument('--year',   required=True,  type=int, help='出生年（公历）')
    parser.add_argument('--month',  required=True,  type=int, help='出生月（1-12）')
    parser.add_argument('--day',    required=True,  type=int, help='出生日（1-31）')
    parser.add_argument('--hour',   default=0,       type=int, help='出生时辰（0-23，默认0）')
    parser.add_argument('--gender', default='unknown',
                        choices=['male', 'female', 'unknown'],
                        help='性别：male/female/unknown')
    parser.add_argument('--level',  default='full',
                        choices=['full', 'quick'],
                        help='分析深度：full / quick')
    parser.add_argument('--city',   default=None,   type=str,
                        help='城市（预留参数，保持与 bazi_analyzer 接口一致）')
    return parser.parse_args()


# ── 主入口 ──────────────────────────────────────────────────────────


def main():
    args = parse_args()

    # 基础校验
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
        out = {'success': False, 'error': '输入参数错误：' + '；'.join(errors)}
        print(json.dumps(out, ensure_ascii=False))
        sys.exit(1)

    try:
        # 1. 调用完整八字精批
        base_result = analyze(
            year=args.year,
            month=args.month,
            day=args.day,
            hour=args.hour,
            gender=args.gender,
            level=args.level,
        )
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({'success': False, 'error': f'八字排盘失败：{e}'},
                         ensure_ascii=False))
        sys.exit(1)

    try:
        # 2. 叠加五运分析
        result = build_five_yun_result(base_result)
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        # 五运失败时仍返回基础报告，并附错误提示
        base_result['five_yun_error'] = str(e)
        print(json.dumps(base_result, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
