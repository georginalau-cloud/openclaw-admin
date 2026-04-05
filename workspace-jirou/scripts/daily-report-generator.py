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


def _run_gccli(args: list, label: str, timeout: int = 30):
    """
    执行 gccli 命令并返回解析后的 JSON 数据。

    Args:
        args: gccli 子命令及参数列表（不含 'gccli' 本身）
        label: 日志中显示的数据名称
        timeout: 超时秒数

    Returns:
        解析后的 JSON 对象，失败返回 None
    """
    try:
        result = subprocess.run(
            ['gccli'] + args,
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            logger.info(f"Garmin {label} 数据获取成功")
            return data
        else:
            if result.stderr.strip():
                logger.warning(f"Garmin {label} 命令返回错误：{result.stderr.strip()}")
    except subprocess.TimeoutExpired:
        logger.warning(f"Garmin {label} 数据获取超时")
    except FileNotFoundError:
        logger.warning("gccli 未安装或不在 PATH 中")
    except json.JSONDecodeError as e:
        logger.warning(f"Garmin {label} 数据解析失败：{e}")
    return None


def get_garmin_data(date_str: str) -> dict:
    """
    从 Garmin CLI 获取当天数据

    Args:
        date_str: 日期字符串 YYYY-MM-DD

    Returns:
        Garmin 数据字典
    """
    garmin_data = {}

    # 一次性获取健康摘要（步数、心率、活动、SpO2、身体能量、压力等大量指标）
    summary = _run_gccli(['health', 'summary', date_str, '--json'], '健康摘要')
    if summary:
        garmin_data['summary'] = summary

    # 睡眠数据（得分与睡眠阶段）
    sleep = _run_gccli(['health', 'sleep', date_str, '--json'], '睡眠')
    if sleep:
        garmin_data['sleep'] = sleep

    # 心率详细数据
    hr = _run_gccli(['health', 'hr', date_str, '--json'], '心率')
    if hr:
        garmin_data['heartrate'] = hr

    # HRV 数据（summary 不含，需单独获取）
    hrv = _run_gccli(['health', 'hrv', date_str, '--json'], 'HRV')
    if hrv:
        garmin_data['hrv'] = hrv

    # SpO2 详细数据（含 lastSevenDaysAvgSpO2，summary 中没有）
    spo2 = _run_gccli(['health', 'spo2', date_str, '--json'], 'SpO2')
    if spo2:
        garmin_data['spo2'] = spo2

    # 压力详细数据（含 stressValuesArray 可统计数据点数）
    stress = _run_gccli(['health', 'stress', 'view', date_str, '--json'], '压力')
    if stress:
        garmin_data['stress'] = stress

    # VO2max / 最大摄氧量
    max_metrics = _run_gccli(['health', 'max-metrics', '--json'], 'VO2max')
    if max_metrics:
        garmin_data['max_metrics'] = max_metrics

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
        # 基础运动
        'steps': None,
        'distance_km': None,
        'active_calories': None,
        'total_calories_burned': None,
        'bmr_calories': None,
        # 心率
        'resting_heart_rate': None,
        'max_heart_rate': None,
        # 睡眠
        'sleep_score': None,
        'sleep_duration_min': None,
        'sleep_deep_min': None,
        'sleep_light_min': None,
        'sleep_rem_min': None,
        'sleep_awake_min': None,
        # HRV
        'hrv_weekly_avg': None,
        'hrv_last_night_avg': None,
        'hrv_last_night_5min_high': None,
        'hrv_status': None,
        'hrv_baseline_low': None,
        'hrv_baseline_high': None,
        # 压力
        'max_stress_level': None,
        'avg_stress_level': None,
        'stress_count': None,
        'low_stress_pct': None,
        'medium_stress_pct': None,
        'high_stress_pct': None,
        # SpO2 / 血氧
        'avg_spo2': None,
        'lowest_spo2': None,
        'latest_spo2': None,
        'seven_day_avg_spo2': None,
        # 呼吸
        'avg_respiration': None,
        'highest_respiration': None,
        'lowest_respiration': None,
        # 身体能量
        'body_battery_charged': None,
        'body_battery_drained': None,
        'body_battery_highest': None,
        'body_battery_lowest': None,
        'body_battery_most_recent': None,
        'body_battery_at_wake': None,
        # 活动详情
        'highly_active_seconds': None,
        'active_seconds': None,
        'sedentary_seconds': None,
        'floors_ascended': None,
        'floors_descended': None,
        # VO2max
        'vo2max': None,
        # 运动记录（暂无来源，保留结构兼容）
        'exercises': [],
    }

    # ── health summary（最全面的基础数据源）──
    health_summary = garmin_data.get('summary', {})
    if isinstance(health_summary, dict):
        summary['steps'] = health_summary.get('totalSteps')
        dist_m = health_summary.get('totalDistanceMeters')
        if dist_m is not None:
            summary['distance_km'] = round(dist_m / 1000, 2)
        summary['active_calories'] = health_summary.get('activeKilocalories')
        summary['bmr_calories'] = health_summary.get('bmrKilocalories')
        summary['resting_heart_rate'] = health_summary.get('restingHeartRate')
        summary['max_heart_rate'] = health_summary.get('maxHeartRate')
        # 压力（summary 字段名 averageStressLevel）
        summary['avg_stress_level'] = health_summary.get('averageStressLevel')
        summary['max_stress_level'] = health_summary.get('maxStressLevel')
        summary['low_stress_pct'] = health_summary.get('lowStressPercentage')
        summary['medium_stress_pct'] = health_summary.get('mediumStressPercentage')
        summary['high_stress_pct'] = health_summary.get('highStressPercentage')
        # SpO2（summary 字段名 averageSpo2，注意大小写与 spo2 命令不同）
        summary['avg_spo2'] = health_summary.get('averageSpo2')
        summary['lowest_spo2'] = health_summary.get('lowestSpo2')
        summary['latest_spo2'] = health_summary.get('latestSpo2')
        # 呼吸
        summary['avg_respiration'] = health_summary.get('avgWakingRespirationValue')
        summary['highest_respiration'] = health_summary.get('highestRespirationValue')
        summary['lowest_respiration'] = health_summary.get('lowestRespirationValue')
        # 身体能量
        summary['body_battery_charged'] = health_summary.get('bodyBatteryChargedValue')
        summary['body_battery_drained'] = health_summary.get('bodyBatteryDrainedValue')
        summary['body_battery_highest'] = health_summary.get('bodyBatteryHighestValue')
        summary['body_battery_lowest'] = health_summary.get('bodyBatteryLowestValue')
        summary['body_battery_most_recent'] = health_summary.get('bodyBatteryMostRecentValue')
        summary['body_battery_at_wake'] = health_summary.get('bodyBatteryAtWakeTime')
        # 活动分解
        summary['highly_active_seconds'] = health_summary.get('highlyActiveSeconds')
        summary['active_seconds'] = health_summary.get('activeSeconds')
        summary['sedentary_seconds'] = health_summary.get('sedentarySeconds')
        summary['floors_ascended'] = health_summary.get('floorsAscended')
        summary['floors_descended'] = health_summary.get('floorsDescended')

    # ── 睡眠数据 ──
    sleep_data = garmin_data.get('sleep', {})
    if isinstance(sleep_data, dict):
        scores = sleep_data.get('sleepScores', {})
        summary['sleep_score'] = (
            (scores.get('overall') if isinstance(scores, dict) else None)
            or sleep_data.get('overallScore')
            or sleep_data.get('score')
        )
        duration = sleep_data.get('sleepTimeSeconds', 0)
        summary['sleep_duration_min'] = round(duration / 60) if duration else None
        stages = sleep_data.get('sleepLevels', {})
        if isinstance(stages, dict) and stages:
            summary['sleep_deep_min'] = round(stages.get('deep', 0) / 60)
            summary['sleep_light_min'] = round(stages.get('light', 0) / 60)
            summary['sleep_rem_min'] = round(stages.get('rem', 0) / 60)
            summary['sleep_awake_min'] = round(stages.get('awake', 0) / 60)

    # ── 心率数据（补充 summary 中没有的字段）──
    hr_data = garmin_data.get('heartrate', {})
    if isinstance(hr_data, dict):
        if summary['resting_heart_rate'] is None:
            summary['resting_heart_rate'] = hr_data.get('restingHeartRate') or hr_data.get('minHeartRate')

    # ── HRV 数据 ──
    hrv_raw = garmin_data.get('hrv', {})
    if isinstance(hrv_raw, dict):
        hrv_s = hrv_raw.get('hrvSummary', {})
        if isinstance(hrv_s, dict):
            summary['hrv_weekly_avg'] = hrv_s.get('weeklyAvg')
            summary['hrv_last_night_avg'] = hrv_s.get('lastNightAvg')
            summary['hrv_last_night_5min_high'] = hrv_s.get('lastNight5MinHigh')
            summary['hrv_status'] = hrv_s.get('status')
            baseline = hrv_s.get('baseline', {})
            if isinstance(baseline, dict):
                summary['hrv_baseline_low'] = baseline.get('balancedLow')
                summary['hrv_baseline_high'] = baseline.get('balancedUpper')

    # ── SpO2 详细数据（lastSevenDaysAvgSpO2 仅在 spo2 命令中）──
    spo2_data = garmin_data.get('spo2', {})
    if isinstance(spo2_data, dict):
        # 以 spo2 命令数据优先（字段名 averageSpO2，大写 O）
        if spo2_data.get('averageSpO2') is not None:
            summary['avg_spo2'] = spo2_data['averageSpO2']
        if spo2_data.get('lowestSpO2') is not None:
            summary['lowest_spo2'] = spo2_data['lowestSpO2']
        if spo2_data.get('latestSpO2') is not None:
            summary['latest_spo2'] = spo2_data['latestSpO2']
        summary['seven_day_avg_spo2'] = spo2_data.get('lastSevenDaysAvgSpO2')

    # ── 压力详细数据（stress_count 来自 stressValuesArray 长度）──
    stress_data = garmin_data.get('stress', {})
    if isinstance(stress_data, dict):
        # stress 命令字段名 avgStressLevel（summary 中为 averageStressLevel）
        if stress_data.get('maxStressLevel') is not None:
            summary['max_stress_level'] = stress_data['maxStressLevel']
        if stress_data.get('avgStressLevel') is not None:
            summary['avg_stress_level'] = stress_data['avgStressLevel']
        stress_values = stress_data.get('stressValuesArray') or []
        if stress_values:
            summary['stress_count'] = len(stress_values)

    # ── VO2max ──
    max_metrics = garmin_data.get('max_metrics')
    if isinstance(max_metrics, list) and max_metrics:
        entry = max_metrics[0]
        summary['vo2max'] = entry.get('vo2MaxValue') or entry.get('mostRecentVO2Max')
    elif isinstance(max_metrics, dict):
        summary['vo2max'] = max_metrics.get('vo2MaxValue') or max_metrics.get('mostRecentVO2Max')

    # ── 总消耗 ──
    active = summary.get('active_calories') or 0
    if active:
        summary['total_calories_burned'] = active

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
    max_hr = fmt(garmin.get('max_heart_rate'), ' bpm')
    bmr_display = fmt(garmin.get('bmr_calories') or bmr, ' kcal')
    vo2max_display = fmt(garmin.get('vo2max'), ' mL/kg/min')
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
    total_burned_display = fmt(total_burned, ' kcal')
    total_intake_display = f"~{total_intake} kcal" if total_intake > 0 else '-'

    # 热量差
    if calorie_diff is not None:
        status = get_calorie_status(calorie_diff)
        diff_sign = '+' if calorie_diff > 0 else ''
        calorie_diff_display = f"{diff_sign}{calorie_diff} kcal（{status}）"
    else:
        calorie_diff_display = '-'

    # HRV 状态展示
    hrv_status_raw = garmin.get('hrv_status') or ''
    hrv_status_map = {
        'BALANCED': 'BALANCED ✅',
        'UNBALANCED': 'UNBALANCED ⚠️',
        'LOW': 'LOW ❗',
    }
    hrv_status_display = hrv_status_map.get(hrv_status_raw, hrv_status_raw) if hrv_status_raw else '-'

    # 活动时间格式化
    highly_active = format_minutes(
        round(garmin['highly_active_seconds'] / 60) if garmin.get('highly_active_seconds') else None
    )
    active_time = format_minutes(
        round(garmin['active_seconds'] / 60) if garmin.get('active_seconds') else None
    )
    sedentary_time = format_minutes(
        round(garmin['sedentary_seconds'] / 60) if garmin.get('sedentary_seconds') else None
    )

    # 消耗说明
    active_sum = garmin.get('active_calories') or 0
    consumption_note = f"*消耗 = 活动总消耗 = {active_sum} kcal" if active_sum else '*消耗 = 数据不可用'

    # SpO2 7天均值格式化（保留一位小数）
    seven_day_spo2 = garmin.get('seven_day_avg_spo2')
    seven_day_spo2_display = f"{seven_day_spo2:.1f}%" if seven_day_spo2 is not None else '-'

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
  - 最大心率: {max_hr}
  - BMR: {bmr_display}
  - 最大摄氧量: {vo2max_display}

## 😴 睡眠情况
  - 得分: {sleep_score}
  - 时长: {sleep_duration}
  - 阶段：深睡{sleep_deep} / 浅睡{sleep_light} / REM {sleep_rem} / 清醒{sleep_awake}

## ⚡ 身体能量
  - 充电值: {fmt(garmin.get('body_battery_charged'))}
  - 放电值: {fmt(garmin.get('body_battery_drained'))}
  - 最高值: {fmt(garmin.get('body_battery_highest'))}
  - 最低值: {fmt(garmin.get('body_battery_lowest'))}
  - 最近值: {fmt(garmin.get('body_battery_most_recent'))}
  - 起床时: {fmt(garmin.get('body_battery_at_wake'))}

## 💓 心率变异性（HRV）
  - 昨晚平均: {fmt(garmin.get('hrv_last_night_avg'), ' ms')}
  - 周平均: {fmt(garmin.get('hrv_weekly_avg'), ' ms')}
  - 5分钟最高: {fmt(garmin.get('hrv_last_night_5min_high'), ' ms')}
  - 状态: {hrv_status_display}
  - 基线范围: {fmt(garmin.get('hrv_baseline_low'))} - {fmt(garmin.get('hrv_baseline_high'))} ms

## 🔴 压力情况
  - 最大压力: {fmt(garmin.get('max_stress_level'))}
  - 平均压力: {fmt(garmin.get('avg_stress_level'))}
  - 数据点数: {fmt(garmin.get('stress_count'))}
  - 压力分布: 低 {fmt(garmin.get('low_stress_pct'), '%')} / 中 {fmt(garmin.get('medium_stress_pct'), '%')} / 高 {fmt(garmin.get('high_stress_pct'), '%')}

## 🩸 血氧及呼吸
  - 平均血氧: {fmt(garmin.get('avg_spo2'), '%')}
  - 最低血氧: {fmt(garmin.get('lowest_spo2'), '%')}
  - 最近血氧: {fmt(garmin.get('latest_spo2'), '%')}
  - 7天均值: {seven_day_spo2_display}
  - 平均呼吸率: {fmt(garmin.get('avg_respiration'), ' rpm')}
  - 最高呼吸率: {fmt(garmin.get('highest_respiration'), ' rpm')}
  - 最低呼吸率: {fmt(garmin.get('lowest_respiration'), ' rpm')}

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
#### 🏃 日常活动
  - 步数: {steps}
  - 距离: {distance}
  - 活动消耗: {active_cals}
  - 剧烈活动: {highly_active}
  - 中等活动: {active_time}
  - 久坐时间: {sedentary_time}
  - 爬升楼层: {fmt(garmin.get('floors_ascended'))} 层
  - 下降楼层: {fmt(garmin.get('floors_descended'))} 层

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
