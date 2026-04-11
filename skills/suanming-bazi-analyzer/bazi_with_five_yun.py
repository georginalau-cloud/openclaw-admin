#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字精批 + 五运分析集成脚本 v2
集合完整的八字排盘和五运深度分析

调用链:
bin/bazi → bazi_with_five_yun.py → src/bazi_analyzer.py → src/bazi_src/bazi.py
                                        ↓
                                   src/cities_longitude.py（真太阳时）
                                        ↓
                                   lib/five_yun_analyzer.py（五运分析）
"""

import sys
import json
import subprocess
import argparse
import os
import re
from datetime import datetime

# 导入五运分析器
sys.path.insert(0, os.path.dirname(__file__))
from lib.five_yun_analyzer import BaziFortuneAnalyzer


def run_bazi_analyzer(year, month, day, hour, gender='male', city=None, minute=0, second=0):
    """调用 src/bazi_analyzer.py 获取完整报告（含真太阳时）"""
    script_dir = os.path.dirname(__file__)
    script_path = os.path.join(script_dir, 'src', 'bazi_analyzer.py')

    args = [
        'python3', script_path,
        '--year', str(year),
        '--month', str(month),
        '--day', str(day),
        '--hour', str(hour),
        '--minute', str(minute),
        '--second', str(second),
        '--gender', gender,
        '--level', 'full',
    ]

    if city:
        args.extend(['--city', city])

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {
                'success': False,
                'error': f'八字排盘失败: {result.stderr}'
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'执行八字排盘异常: {str(e)}'
        }


def extract_ganzhi_from_report(report_text):
    """从报告中提取四柱信息"""
    match = re.search(r'四柱：(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', report_text)
    if match:
        return {
            'year': match.group(1),
            'month': match.group(2),
            'day': match.group(3),
            'hour': match.group(4),
        }
    return {}


def get_current_dayun_index(dayun_list, current_year):
    """找到与当前年份匹配的大运索引"""
    for i, dayun in enumerate(dayun_list):
        age = dayun.get('age', 0)
        if age <= current_year - 1900 + 1:  # 简化估算
            continue
        return i
    return 0


def format_five_yun_analysis(analysis: dict, title: str) -> str:
    """将五运分析结果格式化为可读文本"""
    lines = [f"\n{'='*20} {title} {'='*20}"]
    lines.append(f"总评：{analysis.get('status', '平')}")
    lines.append("─" * 40)
    for insight in analysis.get('insights', []):
        lines.append(f"  • {insight}")
    return '\n'.join(lines)


def generate_five_yun_analysis(bazi_result, full_report, ganzhi, level='all'):
    """
    生成五运分析
    level: 'l1' = 原局分析, 'l2' = 大运分析, 'all' = 两者都有
    """
    try:
        analyzer = BaziFortuneAnalyzer(bazi_result, full_report)
        dayun_list = analyzer.dayun
        current_year = datetime.now().year

        # 五运分析维度
        five_yun_methods = {
            'intimate': analyzer.analyze_intimate,
            'wealth': analyzer.analyze_wealth,
            'children': analyzer.analyze_children,
            'official': analyzer.analyze_official,
            'longevity': analyzer.analyze_longevity,
        }

        result = {}

        # ─────────────────────────────────────────
        # L1: 原局五运分析
        # ─────────────────────────────────────────
        if level in ('l1', 'all'):
            l1_result = analyzer.analyze_original_chart()

            result['l1'] = {
                'name': '原局',
                'label': '【L1】原局五运分析',
                'intimate': l1_result.get('intimate', {}),
                'wealth': l1_result.get('wealth', {}),
                'children': l1_result.get('children', {}),
                'official': l1_result.get('official', {}),
                'longevity': l1_result.get('longevity', {}),
            }

        # ─────────────────────────────────────────
        # L2: 当下大运五运分析
        # 找到与当前年份最接近的大运
        # ─────────────────────────────────────────
        if level in ('l2', 'all') and dayun_list:
            # 找到当前大运（粗略：当前年龄对应的大运）
            birth_year = bazi_result.get('birth', {}).get('year', current_year)
            age = current_year - birth_year

            current_dayun = None
            for i, d in enumerate(dayun_list):
                next_age = dayun_list[i + 1]['age'] if i + 1 < len(dayun_list) else 999
                if d['age'] <= age < next_age:
                    current_dayun = d
                    break
            if current_dayun is None:
                current_dayun = dayun_list[0]

            l2_result = {}
            for key, method in five_yun_methods.items():
                l2_result[key] = method(current_dayun)

            result['l2'] = {
                'name': f"{current_dayun.get('ganzhi', '')}大运",
                'age_range': f"{current_dayun['age']}～{dayun_list[dayun_list.index(current_dayun) + 1]['age'] if dayun_list.index(current_dayun) + 1 < len(dayun_list) else current_dayun['age'] + 10}岁",
                'label': f"【L2】当前大运五运分析",
                'intimate': l2_result['intimate'],
                'wealth': l2_result['wealth'],
                'children': l2_result['children'],
                'official': l2_result['official'],
                'longevity': l2_result['longevity'],
            }

        return {'success': True, 'data': result}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def five_yun_to_text(result: dict) -> str:
    """将五运分析结构转为可读文本"""
    lines = ["\n\n" + "=" * 60]
    lines.append("【五运深度分析报告】")
    lines.append("=" * 60)

    dim_names = {
        'intimate': '💗 感情运',
        'wealth': '💰 财运',
        'children': '👶 子运',
        'official': '💼 禄运',
        'longevity': '🏥 寿运',
    }

    # L1 原局
    if 'l1' in result and result['l1']:
        lines.append(f"\n{'─' * 60}")
        lines.append(f"【L1】原局 — 命局基本特质")
        lines.append(f"{'─' * 60}")
        for key, name in dim_names.items():
            a = result['l1'].get(key, {})
            lines.append(f"\n{name}（{a.get('status', '平')}）")
            for insight in a.get('insights', []):
                lines.append(f"  • {insight}")

    # L2 大运
    if 'l2' in result and result['l2']:
        l2 = result['l2']
        lines.append(f"\n{'─' * 60}")
        lines.append(f"【L2】{l2.get('name', '')}（{l2.get('age_range', '')}）")
        lines.append(f"{'─' * 60}")
        for key, name in dim_names.items():
            a = l2.get(key, {})
            lines.append(f"\n{name}（{a.get('status', '平')}）")
            for insight in a.get('insights', []):
                lines.append(f"  • {insight}")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='八字精批 + 五运分析 v2')
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--month', type=int, required=True)
    parser.add_argument('--day', type=int, required=True)
    parser.add_argument('--hour', type=int, required=True)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--second', type=int, default=0)
    parser.add_argument('--city', type=str, default=None)
    parser.add_argument('--gender', type=str, default='male')
    parser.add_argument('--level', type=str, default='full')
    parser.add_argument('--five-yun-level', type=str, default='all',
                        help='l1=原局分析, l2=大运分析, all=两者')

    args = parser.parse_args()

    # 第一步：八字排盘（含真太阳时）
    bazi_result = run_bazi_analyzer(
        year=args.year,
        month=args.month,
        day=args.day,
        hour=args.hour,
        minute=args.minute,
        second=args.second,
        gender=args.gender,
        city=args.city
    )

    if not bazi_result.get('success'):
        print(json.dumps({
            'success': False,
            'error': bazi_result.get('error', '八字排盘失败'),
            'full_report': ''
        }, ensure_ascii=False, indent=2))
        return

    full_report = bazi_result.get('full_report', '')
    ganzhi = bazi_result.get('ganzhi', {})
    if not ganzhi:
        ganzhi = extract_ganzhi_from_report(full_report)

    # 第二步：生成 L1+L2 五运分析
    five_yun_result = generate_five_yun_analysis(
        bazi_result, full_report, ganzhi, level=args.five_yun_level
    )

    # 第三步：构建文本输出（拼在 full_report 后面）
    five_yun_text = ''
    if five_yun_result.get('success'):
        five_yun_text = five_yun_to_text(five_yun_result['data'])
        full_report = full_report + five_yun_text

    # 第四步：输出
    output = {
        'success': True,
        'full_report': full_report,
        'ganzhi': ganzhi,
        'birth': bazi_result.get('birth', {}),
        'five_yun': five_yun_result.get('data', {}) if five_yun_result.get('success') else None,
        'generated_at': datetime.now().isoformat()
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
