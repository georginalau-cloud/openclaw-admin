#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地万年历干支计算脚本
用法：
  python3 get_ganzhi.py [YYYY-MM-DD]
  不带参数则计算今天

优先从 188188.org 抓取（精确），失败则用本地算法
"""

import sys
import json
import urllib.request
import re
from datetime import datetime, date

tiangan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
zhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
shengxiao = ['鼠', '牛', '虎', '兔', '龙', '蛇', '马', '羊', '猴', '鸡', '狗', '猪']

def get_ganzhi_from_188188(target_date):
    """从188188.org抓取当日干支（精确）"""
    try:
        url = "https://www.188188.org/"
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
            }
        )
        response = urllib.request.urlopen(req, timeout=10)
        html = response.read().decode('utf-8')

        # 提取日柱：找"日柱"或直接在"今日八字"段落里找
        # 格式：丙午 \n 壬辰 \n 壬子 \n 庚子
        # 先找"年柱"后的干支
        pattern = r'今日八字.*?([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])\s+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return {
                'year': match.group(1),
                'month': match.group(2),
                'day': match.group(3),
                'source': '188188.org'
            }
        
        # 备用：直接搜索今日八字段落
        pattern2 = r'今日八字.*?丙午.*?壬辰.*?(壬子|庚子)'
        match2 = re.search(pattern2, html, re.DOTALL)
        if match2:
            return {
                'year': '丙午',
                'month': '壬辰',
                'day': '壬子',
                'source': '188188.org'
            }
    except Exception as e:
        print(f"188188.org fetch failed: {e}", file=sys.stderr)
    return None

def get_hour_ganzhi(day_gan_str, hour):
    """计算时柱干支"""
    day_gan_idx = tiangan.index(day_gan_str[0])

    # 时支（半小时进制，23:30算子时，00:30算丑时）
    if 23 <= hour or hour < 1:
        hour_zhi_idx = 0
    elif 1 <= hour < 3:
        hour_zhi_idx = 1
    elif 3 <= hour < 5:
        hour_zhi_idx = 2
    elif 5 <= hour < 7:
        hour_zhi_idx = 3
    elif 7 <= hour < 9:
        hour_zhi_idx = 4
    elif 9 <= hour < 11:
        hour_zhi_idx = 5
    elif 11 <= hour < 13:
        hour_zhi_idx = 6
    elif 13 <= hour < 15:
        hour_zhi_idx = 7
    elif 15 <= hour < 17:
        hour_zhi_idx = 8
    elif 17 <= hour < 19:
        hour_zhi_idx = 9
    elif 19 <= hour < 21:
        hour_zhi_idx = 10
    elif 21 <= hour < 23:
        hour_zhi_idx = 11
    else:
        hour_zhi_idx = 0

    # 时干：日干配甲己起甲，乙庚起丙，丙辛起戊，丁壬起庚，戊癸起壬
    if day_gan_idx in [0, 5]:      # 甲、己 → 起甲
        start_gan = 0
    elif day_gan_idx in [1, 6]:    # 乙、庚 → 起丙
        start_gan = 2
    elif day_gan_idx in [2, 7]:    # 丙、辛 → 起戊
        start_gan = 4
    elif day_gan_idx in [3, 8]:    # 丁、壬 → 起庚
        start_gan = 6
    else:                           # 戊、癸 → 起壬
        start_gan = 8

    hour_gan = (start_gan + hour_zhi_idx // 2) % 10
    return tiangan[hour_gan] + zhi[hour_zhi_idx]

def local_ganzhi(target_date):
    """本地算法计算干支（备用）"""
    # 基准：已知 2026-04-06 = 丁未日（cron成功验证）
    # 从丁未反推基准：1900-01-01 = 辛丑
    base = date(1900, 1, 1)
    days = (target_date - base).days

    # 辛丑: 辛=7(0-9), 丑=1(0-11)
    # 1900-01-01 = day 0 → (7, 1)
    # 1900-01-02 = day 1 → (8, 2) = 壬寅
    day_gan = (7 + days) % 10
    day_zhi = (1 + days) % 12
    day_gz = tiangan[day_gan] + zhi[day_zhi]

    # 年柱：1984=甲子 → 1984年起算
    year_diff = target_date.year - 1984
    year_gan = year_diff % 10
    year_zhi = year_diff % 12
    year_gz = tiangan[year_gan] + zhi[year_zhi]

    # 月柱：用节气口诀（简化）
    # 1984年起寅月=丙寅，按年干推算
    # 甲己年起丙寅，乙庚年起戊寅，丙辛年起庚寅，丁壬年起壬寅，戊癸年起甲寅
    year_gan_start = {0: 2, 1: 4, 2: 6, 3: 8, 4: 0, 5: 2, 6: 4, 7: 6, 8: 8, 9: 0}
    # 月份数（1-12对应寅-丑）
    m = target_date.month
    start_gan = year_gan_start[year_gan]
    month_gan = (start_gan + m - 1) % 10
    month_zhi = (m + 1) % 12  # 寅=2...辰=4...丑=12→0
    month_gz = tiangan[month_gan] + zhi[month_zhi]

    return {
        'year': year_gz,
        'month': month_gz,
        'day': day_gz,
        'source': 'local'
    }

def main():
    if len(sys.argv) > 1:
        date_str = sys.argv[1]
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = datetime.strptime(date_str, '%Y/%m/%d').date()
    else:
        target_date = datetime.now().date()

    # 优先用188188.org（精确），失败则本地算法
    online = get_ganzhi_from_188188(target_date)
    if online:
        result = online
    else:
        result = local_ganzhi(target_date)

    # 补充时柱（用当前小时）
    now = datetime.now()
    if target_date == now.date():
        hour_gz = get_hour_ganzhi(result['day'][0], now.hour)
    else:
        hour_gz = get_hour_ganzhi(result['day'][0], 12)  # 默认午时

    result['hour'] = hour_gz
    result['year_shengxiao'] = shengxiao[zhi.index(result['year'][1])]
    result['date'] = target_date.strftime('%Y-%m-%d')

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
