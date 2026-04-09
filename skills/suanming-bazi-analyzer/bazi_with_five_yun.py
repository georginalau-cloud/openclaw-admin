#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八��精批 + 五运分析集成脚本
集合完整的八字排盘和五运深度分析
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
    """调用原有的 bazi_analyzer.py 获取完整报告"""
    script_dir = os.path.dirname(__file__)
    script_path = os.path.join(script_dir, 'bazi_analyzer.py')
    
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
    ganzhi = {}
    
    # 查找 "四柱：己巳 丁丑 庚辰 庚辰" 这样的格式
    match = re.search(r'四柱：(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', report_text)
    if match:
        ganzhi = {
            'year': match.group(1),
            'month': match.group(2),
            'day': match.group(3),
            'hour': match.group(4),
        }
    
    return ganzhi


def generate_five_yun_section(bazi_result, full_report):
    """生成五运分析摘要"""
    try:
        analyzer = BaziFortuneAnalyzer(bazi_result, full_report)
        
        # 获取近3个大运
        recent_dayun = analyzer.dayun[:3] if analyzer.dayun else []
        
        # 生成格式化摘要
        summary_lines = [
            "\n【八】五运深度分析概览",
            "─" * 50,
        ]
        
        if recent_dayun:
            summary_lines.append("📊 近3个大运分析")
            for dayun in recent_dayun:
                age = dayun.get('age', '?')
                ganzhi = dayun.get('ganzhi', '?')
                wangshuai = dayun.get('wangshuai', '?')
                nayin = dayun.get('nayin', '?')
                
                summary_lines.append(f"  • {age}岁 {ganzhi} ({wangshuai}) 【{nayin}】")
        else:
            summary_lines.append("📊 五运分析：数据生成中...")
        
        summary_lines.extend([
            "",
            "💡 可进一步查询以获得深度分析",
        ])
        
        return {
            'success': True,
            'recent_dayun': recent_dayun,
            'formatted_summary': '\n'.join(summary_lines)
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'formatted_summary': f'\n【八】五运分析\n[数据生成异常，请稍后重试]'
        }


def main():
    parser = argparse.ArgumentParser(description='八字精批 + 五运分析')
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--month', type=int, required=True)
    parser.add_argument('--day', type=int, required=True)
    parser.add_argument('--hour', type=int, required=True)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--second', type=int, default=0)
    parser.add_argument('--city', type=str, default=None)
    parser.add_argument('--gender', type=str, default='male')
    parser.add_argument('--level', type=str, default='full')
    
    args = parser.parse_args()
    
    # 第一步：调用原有的八字排盘
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
        }))
        return
    
    # 第二步：提取四柱信息和完整报告
    full_report = bazi_result.get('full_report', '')
    ganzhi = bazi_result.get('ganzhi', {})
    
    if not ganzhi:
        ganzhi = extract_ganzhi_from_report(full_report)
    
    # 第三步：生成五运摘要
    five_yun_result = generate_five_yun_section(bazi_result, full_report)
    
    # 第四步：构建增强型报告
    if five_yun_result['success']:
        enhanced_report = full_report + five_yun_result['formatted_summary']
    else:
        enhanced_report = full_report
    
    # 第五步：输出最终结果
    output = {
        'success': True,
        'full_report': enhanced_report,
        'ganzhi': ganzhi,
        'birth': bazi_result.get('birth', {}),
        'five_yun_summary': five_yun_result.get('formatted_summary', ''),
        'generated_at': datetime.now().isoformat()
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
