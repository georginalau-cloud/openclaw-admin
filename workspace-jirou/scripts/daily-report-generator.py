#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
肌肉 Agent 日报生成脚本
收集所有数据源，生成每日健康日报 markdown 文件

数据来源：
  - 有品秤 OCR（早/晚体重数据）
  - 三餐热量数据（USDA 查询结果）
  - Garmin 数据（步数、运动、睡眠、心率）

用法：
    python3 daily-report-generator.py
    python3 daily-report-generator.py --date 2024-01-15
    python3 daily-report-generator.py --date 2024-01-15 --output /path/to/report.md
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.expanduser("~/.openclaw/.env"))
except ImportError:
    pass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(
            os.path.expanduser('~/.openclaw/workspace-jirou/logs/daily-report.log'),
            mode='a',
            encoding='utf-8'
        ) if os.path.exists(os.path.expanduser('~/.openclaw/workspace-jirou/logs')) else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# 路径配置
WORKSPACE = os.path.expanduser('~/.openclaw/workspace-jirou')
PENDING_DIR = os.path.join(WORKSPACE, 'memory', 'pending')
REPORTS_DIR = os.path.join(WORKSPACE, 'memory', 'reports')


def load_json_file(filepath: str) -> dict:
    """安全加载 JSON 文件"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"加载文件失败 {filepath}：{e}")
    return {}


def load_scale_data(date_str: str, time_of_day: str) -> dict:
    """
    加载有品秤数据

    Args:
        date_str: 日期字符串 YYYY-MM-DD
        time_of_day: 'morning' 或 'evening'

    Returns:
        秤数据字典，失败返回空字典
    """
    filepath = os.path.join(PENDING_DIR, f'{date_str}-{time_of_day}-scale.json')
    data = load_json_file(filepath)
    if data.get('success') and data.get('data'):
        logger.info(f"加载{time_of_day}体重数据：{filepath}")
        return data['data']
    logger.info(f"{time_of_day}体重数据不存在：{filepath}")
    return {}


def load_meal_data(date_str: str, meal_type: str) -> dict:
    """
    加载餐食数据

    Args:
        date_str: 日期字符串 YYYY-MM-DD
        meal_type: 'breakfast'、'lunch'、'dinner' 或 'snack'

    Returns:
        餐食数据字典，失败返回空字典
    """
    filepath = os.path.join(PENDING_DIR, f'{date_str}-{meal_type}.json')
    data = load_json_file(filepath)
    if data.get('success') and data.get('items'):
        logger.info(f"加载{meal_type}数据：{filepath}")
        return data
    logger.info(f"{meal_type}数据不存在：{filepath}")
    return {}


def get_garmin_data(date_str: str) -> dict:
    """
    从 Garmin CLI 获取当天数据

    Args:
        date_str: 日期字符串 YYYY-MM-DD

    Returns:
        Garmin 数据字典
    """
    garmin_data = {}

    # 获取活动/步数数据
    try:
        result = subprocess.run(
            ['gccli', 'activities', '--date', date_str, '--json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            activities = json.loads(result.stdout)
            garmin_data['activities'] = activities
            logger.info(f"Garmin 活动数据获取成功：{len(activities)} 条")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Garmin 活动数据获取失败：{e}")

    # 获取步数数据
    try:
        result = subprocess.run(
            ['gccli', 'steps', '--date', date_str, '--json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            steps_data = json.loads(result.stdout)
            garmin_data['steps'] = steps_data
            logger.info("Garmin 步数数据获取成功")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Garmin 步数数据获取失败：{e}")

    # 获取睡眠数据（前一天的睡眠）
    try:
        result = subprocess.run(
            ['gccli', 'sleep', '--date', date_str, '--json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            sleep_data = json.loads(result.stdout)
            garmin_data['sleep'] = sleep_data
            logger.info("Garmin 睡眠数据获取成功")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Garmin 睡眠数据获取失败：{e}")

    # 获取心率数据
    try:
        result = subprocess.run(
            ['gccli', 'heartrate', '--date', date_str, '--json'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            hr_data = json.loads(result.stdout)
            garmin_data['heartrate'] = hr_data
            logger.info("Garmin 心率数据获取成功")
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Garmin 心率数据获取失败：{e}")

    return garmin_data


def parse_garmin_summary(garmin_data: dict) -> dict:
    """
    解析 Garmin 数据，提取关键指标

    Args:
        garmin_data: 原始 Garmin 数据

    Returns:
        解析后的摘要数据
    """
    summary = {
        'steps': None,
        'distance_km': None,
        'active_calories': None,
        'exercise_calories': None,
        'total_calories_burned': None,
        'resting_heart_rate': None,
        'hrv': None,
        'sleep_score': None,
        'sleep_duration_min': None,
        'sleep_deep_min': None,
        'sleep_light_min': None,
        'sleep_rem_min': None,
        'sleep_awake_min': None,
        'exercises': [],
    }

    # 解析步数数据
    steps_data = garmin_data.get('steps', {})
    if isinstance(steps_data, dict):
        summary['steps'] = steps_data.get('totalSteps') or steps_data.get('steps')
        summary['distance_km'] = steps_data.get('totalDistance') or steps_data.get('distanceInMeters', 0) / 1000
        summary['active_calories'] = steps_data.get('activeKilocalories') or steps_data.get('calories')
    elif isinstance(steps_data, list) and steps_data:
        day = steps_data[0]
        summary['steps'] = day.get('totalSteps')
        summary['distance_km'] = day.get('totalDistanceMeters', 0) / 1000
        summary['active_calories'] = day.get('activeKilocalories')

    # 解析心率数据
    hr_data = garmin_data.get('heartrate', {})
    if isinstance(hr_data, dict):
        summary['resting_heart_rate'] = hr_data.get('restingHeartRate') or hr_data.get('minHeartRate')
        summary['hrv'] = hr_data.get('lastNight5MinHigh') or hr_data.get('hrv')

    # 解析睡眠数据
    sleep_data = garmin_data.get('sleep', {})
    if isinstance(sleep_data, dict):
        summary['sleep_score'] = sleep_data.get('sleepScores', {}).get('overall') or sleep_data.get('score')
        duration = sleep_data.get('sleepTimeSeconds', 0)
        summary['sleep_duration_min'] = round(duration / 60) if duration else None
        # 睡眠阶段
        stages = sleep_data.get('sleepLevels', {})
        summary['sleep_deep_min'] = round(stages.get('deep', 0) / 60) if stages else None
        summary['sleep_light_min'] = round(stages.get('light', 0) / 60) if stages else None
        summary['sleep_rem_min'] = round(stages.get('rem', 0) / 60) if stages else None
        summary['sleep_awake_min'] = round(stages.get('awake', 0) / 60) if stages else None

    # 解析活动数据（运动）
    activities = garmin_data.get('activities', [])
    if isinstance(activities, list):
        for activity in activities:
            exercise = {
                'name': activity.get('activityName', '未知运动'),
                'duration_min': round(activity.get('duration', 0) / 60),
                'calories': activity.get('calories'),
                'avg_hr': activity.get('averageHR'),
                'max_hr': activity.get('maxHR'),
            }
            summary['exercises'].append(exercise)
            if exercise.get('calories'):
                summary['exercise_calories'] = (summary['exercise_calories'] or 0) + exercise['calories']

    # 计算总消耗
    active = summary.get('active_calories') or 0
    exercise = summary.get('exercise_calories') or 0
    if active or exercise:
        summary['total_calories_burned'] = active + exercise

    return summary


def format_minutes(minutes) -> str:
    """将分钟数格式化为 Xh Xm 格式"""
    if minutes is None:
        return '-'
    h = minutes // 60
    m = minutes % 60
    if h == 0:
        return f'{m}m'
    if m == 0:
        return f'{h}h'
    return f'{h}h {m}m'


def format_meal_section(meal_data: dict, meal_name: str) -> str:
    """格式化餐食章节"""
    if not meal_data or not meal_data.get('items'):
        return f'  - {meal_name}：-'

    lines = [f'  - {meal_name}：']
    for item in meal_data['items']:
        name = item.get('food_name', '未知')
        weight = item.get('weight_g', 0)
        cals = item.get('calories', 0)
        estimated = '（估算）' if item.get('estimated') else ''
        lines.append(f'    - {name}（{weight}g）：{cals} kcal{estimated}')

    total = meal_data.get('total_calories', 0)
    lines.append(f'    小计：{total} kcal')
    return '\n'.join(lines)


def get_calorie_status(calorie_diff: int) -> str:
    """根据热量差返回状态描述"""
    if calorie_diff < -500:
        return '⚠️ 摄入严重不足'
    elif calorie_diff < -200:
        return '✅ 健康减脂区间'
    elif calorie_diff < 200:
        return '⚖️ 基本持平'
    elif calorie_diff < 500:
        return '📈 轻度盈余'
    else:
        return '⚠️ 热量盈余过多'


def get_weekday_zh(date_obj: date) -> str:
    """获取中文星期"""
    weekdays = ['一', '二', '三', '四', '五', '六', '日']
    return f'星期{weekdays[date_obj.weekday()]}'


def generate_report(date_str: str) -> str:
    """
    生成指定日期的健康日报

    Args:
        date_str: 日期字符串 YYYY-MM-DD

    Returns:
        markdown 格式的日报内容
    """
    logger.info(f"开始生成 {date_str} 的日报...")

    report_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # ── 1. 加载所有数据 ──
    morning_scale = load_scale_data(date_str, 'morning')
    evening_scale = load_scale_data(date_str, 'evening')
    breakfast = load_meal_data(date_str, 'breakfast')
    lunch = load_meal_data(date_str, 'lunch')
    dinner = load_meal_data(date_str, 'dinner')
    snack = load_meal_data(date_str, 'snack')

    # ── 2. 获取 Garmin 数据 ──
    garmin_raw = get_garmin_data(date_str)
    garmin = parse_garmin_summary(garmin_raw)

    # ── 3. 计算热量 ──
    total_intake = sum([
        breakfast.get('total_calories', 0) or 0,
        lunch.get('total_calories', 0) or 0,
        dinner.get('total_calories', 0) or 0,
        snack.get('total_calories', 0) or 0,
    ])

    # BMR 优先从早晨有品秤获取
    bmr = morning_scale.get('bmr') or evening_scale.get('bmr')

    total_burned = None
    calorie_diff = None
    if garmin.get('total_calories_burned'):
        total_burned = garmin['total_calories_burned']
        if total_intake > 0 and total_burned > 0:
            calorie_diff = total_intake - total_burned

    # ── 4. 格式化日报 ──
    date_display = f"{report_date.year}年{report_date.month}月{report_date.day}日 {get_weekday_zh(report_date)}"

    # 体重数据行
    def fmt(val, unit=''):
        return f"{val}{unit}" if val is not None else '-'

    weight_morning = fmt(morning_scale.get('weight'), ' kg')
    weight_evening = fmt(evening_scale.get('weight'), ' kg')
    fat_morning = fmt(morning_scale.get('body_fat'), '%')
    fat_evening = fmt(evening_scale.get('body_fat'), '%')
    muscle_morning = fmt(morning_scale.get('muscle_rate'), '%')
    muscle_evening = fmt(evening_scale.get('muscle_rate'), '%')
    muscle_level_morning = fmt(morning_scale.get('muscle_level'))
    muscle_level_evening = fmt(evening_scale.get('muscle_level'))
    visceral_morning = fmt(morning_scale.get('visceral_fat'))
    visceral_evening = fmt(evening_scale.get('visceral_fat'))
    water_morning = fmt(morning_scale.get('water'), '%')
    water_evening = fmt(evening_scale.get('water'), '%')
    protein_morning = fmt(morning_scale.get('protein'), '%')
    protein_evening = fmt(evening_scale.get('protein'), '%')
    bone_morning = fmt(morning_scale.get('bone_mass'), ' kg')
    bone_evening = fmt(evening_scale.get('bone_mass'), ' kg')
    resting_hr = fmt(garmin.get('resting_heart_rate'), ' bpm')
    hrv = fmt(garmin.get('hrv'), ' ms')
    bmr_display = fmt(bmr, ' kcal')
    sleep_score = fmt(garmin.get('sleep_score'))
    sleep_duration = format_minutes(garmin.get('sleep_duration_min'))
    sleep_deep = format_minutes(garmin.get('sleep_deep_min'))
    sleep_light = format_minutes(garmin.get('sleep_light_min'))
    sleep_rem = format_minutes(garmin.get('sleep_rem_min'))
    sleep_awake = format_minutes(garmin.get('sleep_awake_min'))

    steps = fmt(garmin.get('steps'))
    if garmin.get('steps'):
        steps = f"{garmin['steps']:,}步"
    distance = f"{garmin['distance_km']:.1f} km" if garmin.get('distance_km') else '-'
    active_cals = fmt(garmin.get('active_calories'), ' kcal')
    exercise_cals = fmt(garmin.get('exercise_calories'), ' kcal')
    total_burned_display = fmt(total_burned, ' kcal')
    total_intake_display = f"~{total_intake} kcal" if total_intake > 0 else '-'

    # 热量差
    if calorie_diff is not None:
        status = get_calorie_status(calorie_diff)
        diff_sign = '+' if calorie_diff > 0 else ''
        calorie_diff_display = f"{diff_sign}{calorie_diff} kcal（{status}）"
    else:
        calorie_diff_display = '-'

    # 运动详情
    exercise_lines = []
    if garmin.get('exercises'):
        for ex in garmin['exercises']:
            ex_name = ex.get('name', '未知运动')
            ex_dur = format_minutes(ex.get('duration_min'))
            ex_cals = fmt(ex.get('calories'), ' kcal')
            ex_avg_hr = fmt(ex.get('avg_hr'), ' bpm')
            ex_max_hr = fmt(ex.get('max_hr'), ' bpm')
            exercise_lines.extend([
                f'  - 运动类型：{ex_name}',
                f'  - 运动时长：{ex_dur}',
                f'  - 运动消耗：{ex_cals}',
                f'  - 平均心率：{ex_avg_hr}',
                f'  - 最大心率：{ex_max_hr}',
            ])
    else:
        exercise_lines = [
            '  - 运动类型：-',
            '  - 运动时长：-',
            '  - 运动消耗：-',
            '  - 平均心率：-',
            '  - 最大心率：-',
        ]

    # 消耗说明
    active_sum = garmin.get('active_calories') or 0
    exercise_sum = garmin.get('exercise_calories') or 0
    consumption_note = f"*消耗 = 支出1 + 支出2 = {active_sum + exercise_sum} kcal" if (active_sum or exercise_sum) else '*消耗 = 数据不可用'

    report = f"""📊 {date_display} 健康日报

## ⚖️ 身体数据
  - 体重: {weight_morning}（晨）/ {weight_evening}（晚）
  - 体脂: {fat_morning}（晨）/ {fat_evening}（晚）
  - 肌肉：{muscle_morning}（晨）/ {muscle_evening}（晚）
  - 储肌能力：{muscle_level_morning}（晨）/ {muscle_level_evening}（晚）
  - 内脏脂肪：{visceral_morning}（晨）/ {visceral_evening}（晚）
  - 水分：{water_morning}（晨）/ {water_evening}（晚）
  - 蛋白质：{protein_morning}（晨）/ {protein_evening}（晚）
  - 骨量：{bone_morning}（晨）/ {bone_evening}（晚）
  - 静息心率: {resting_hr}
  - HRV: {hrv}
  - BMR: {bmr_display}
  - 最大摄氧量: -

## 😴 睡眠情况
  - 得分: {sleep_score}
  - 时长: {sleep_duration}
  - 阶段：深睡{sleep_deep} / 浅睡{sleep_light} / REM {sleep_rem} / 清醒{sleep_awake}

## 🔥 热量情况
  - 总摄入: {total_intake_display}
  - 总消耗: {total_burned_display}
  - 缺口: {calorie_diff_display}

### 🍽️ 昨日摄入
{format_meal_section(breakfast, '早餐')}
{format_meal_section(lunch, '午餐')}
{format_meal_section(dinner, '晚餐')}
{format_meal_section(snack, '零食')}

### 💪 昨日消耗
#### 🏃 日常活动（支出1）
  - 步数: {steps}
  - 距离: {distance}
  - 活动消耗: {active_cals}

#### 🏋️ 昨日运动（支出2）
{chr(10).join(exercise_lines)}

{consumption_note}
"""
    return report.strip()


def main():
    parser = argparse.ArgumentParser(
        description='肌肉 Agent 日报生成脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 daily-report-generator.py
  python3 daily-report-generator.py --date 2024-01-15
  python3 daily-report-generator.py --date 2024-01-15 --output /tmp/report.md
        """
    )
    parser.add_argument(
        '--date',
        default=datetime.now().strftime('%Y-%m-%d'),
        help='日期 YYYY-MM-DD（默认今天）'
    )
    parser.add_argument('--output', help='输出文件路径（默认：memory/pending/DailyReport-YYYY-MM-DD.md）')
    parser.add_argument('--debug', action='store_true', help='启用调试日志')

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # 确保目录存在
    os.makedirs(PENDING_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # 生成日报
    try:
        report_content = generate_report(args.date)
    except Exception as e:
        logger.error(f"日报生成失败：{e}", exc_info=True)
        sys.exit(1)

    # 确定输出路径（默认保存到 pending 目录，供 OpenClaw cron 系统发送）
    output_path = args.output or os.path.join(PENDING_DIR, f'DailyReport-{args.date}.md')
    output_path = os.path.expanduser(output_path)

    # 保存日报（pending 目录，待 OpenClaw cron 系统发送到飞书）
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"日报已保存至：{output_path}")

    # 同时归档到 reports 目录
    archive_path = os.path.join(REPORTS_DIR, f'{args.date}.md')
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    logger.info(f"日报已归档至：{archive_path}")

    # 同时输出到 stdout
    print(report_content)


if __name__ == '__main__':
    main()
