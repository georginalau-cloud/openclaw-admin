#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import subprocess
import argparse
import os
import re
from datetime import datetime
from cities_longitude import get_longitude, calculate_solar_time

def parse_bazi_output(output_text):
    """
    从 bazi.py 的文本输出中提取干支信息
    """
    ganzhi = {}
    
    # 查找 "四柱：己巳 丁丑 庚辰 庚辰" 这样的格式
    match = re.search(r'四柱：(\S+)\s+(\S+)\s+(\S+)\s+(\S+)', output_text)
    if match:
        ganzhi = {
            'year': match.group(1),
            'month': match.group(2),
            'day': match.group(3),
            'hour': match.group(4),
        }
    
    return ganzhi

def main():
    parser = argparse.ArgumentParser(description='八字精批分析器')
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--month', type=int, required=True)
    parser.add_argument('--day', type=int, required=True)
    parser.add_argument('--hour', type=int, required=True)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--second', type=int, default=0)
    parser.add_argument('--city', type=str, default=None, help='城市名称，用于真太阳时转换')
    parser.add_argument('--longitude', type=float, default=None, help='经度(度)，用于真太阳时转换')
    parser.add_argument('--gender', type=str, default='male')
    parser.add_argument('--level', type=str, default='full')
    
    args = parser.parse_args()
    
    original_hour = args.hour
    original_minute = args.minute
    adjusted_hour = args.hour
    adjusted_minute = args.minute
    solar_time_applied = False
    
    # 获取经度
    longitude = None
    if args.longitude:
        longitude = args.longitude
    elif args.city:
        longitude = get_longitude(args.city)
    
    # 如果有经度信息，计算真太阳时
    if longitude is not None:
        adjusted_hour, adjusted_minute = calculate_solar_time(
            args.hour, args.minute, args.second, longitude
        )
        solar_time_applied = True
    
    # 调用 bazi.py
    bazi_dir = os.path.join(os.path.dirname(__file__), 'bazi_src')
    bazi_script = os.path.join(bazi_dir, 'bazi.py')
    
    # 构建命令（使用调整后的时间）
    cmd = [
        'python3',
        bazi_script,
        str(args.year),
        str(args.month),
        str(args.day),
        str(adjusted_hour),
        '-g',  # 公历
    ]
    
    if args.gender == 'female':
        cmd.append('-n')  # 女命
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=bazi_dir)
        
        if result.returncode != 0:
            output = {
                'success': False,
                'error': result.stderr or 'bazi.py 执行失败',
                'birth': {
                    'year': args.year,
                    'month': args.month,
                    'day': args.day,
                    'hour': args.hour,
                    'minute': args.minute,
                    'gender': args.gender,
                    'city': args.city,
                    'longitude': longitude
                },
                'generated_at': datetime.now().isoformat()
            }
        else:
            # 解析干支信息
            ganzhi = parse_bazi_output(result.stdout)
            
            # 构建输出信息
            solar_note = ""
            if solar_time_applied:
                solar_note = f"\n📍 真太阳时调整:\n  城市/经度: {args.city or longitude}°E\n  原时间: {args.hour:02d}:{args.minute:02d}\n  调整后: {adjusted_hour:02d}:{adjusted_minute:02d}\n"
            
            output = {
                'success': True,
                'full_report': solar_note + result.stdout,
                'ganzhi': ganzhi,
                'birth': {
                    'year': args.year,
                    'month': args.month,
                    'day': args.day,
                    'hour': args.hour,
                    'minute': args.minute,
                    'adjusted_hour': adjusted_hour,
                    'adjusted_minute': adjusted_minute,
                    'gender': args.gender,
                    'city': args.city,
                    'longitude': longitude,
                    'solar_time_applied': solar_time_applied
                },
                'generated_at': datetime.now().isoformat()
            }
        
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except subprocess.TimeoutExpired:
        output = {
            'success': False,
            'error': '八字分析超时',
            'birth': {
                'year': args.year,
                'month': args.month,
                'day': args.day,
                'hour': args.hour,
                'minute': args.minute,
                'gender': args.gender,
                'city': args.city,
                'longitude': longitude
            },
            'generated_at': datetime.now().isoformat()
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except Exception as e:
        output = {
            'success': False,
            'error': str(e),
            'birth': {
                'year': args.year,
                'month': args.month,
                'day': args.day,
                'hour': args.hour,
                'minute': args.minute,
                'gender': args.gender,
                'city': args.city,
                'longitude': longitude
            },
            'generated_at': datetime.now().isoformat()
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
