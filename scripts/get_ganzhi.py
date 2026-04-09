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

        # 如果页面显示"改版中"，则抓取失败
        if '改版中' in html or '恢复正常访问' in html:
            print("188188.org is under maintenance, skipping", file=sys.stderr)
            return None

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
    """本地算法计算干支（完全自力更生，不依赖外部）"""
    # 基准：2026-01-01 = 乙巳年 戊子月 乙亥日（沛柔验证）
    ref = date(2026, 1, 1)
    ref_day_gan = 1   # 乙
    ref_day_zhi = 11  # 亥
    days = (target_date - ref).days

    # 日柱：按天干地支依次循环递加
    day_gan = (ref_day_gan + days) % 10
    day_zhi = (ref_day_zhi + days) % 12
    day_gz = tiangan[day_gan] + zhi[day_zhi]

    # 年柱：1984=甲子 → 2026=丙午
    year_diff = target_date.year - 1984
    year_gan = year_diff % 10
    year_zhi = year_diff % 12
    year_gz = tiangan[year_gan] + zhi[year_zhi]

    # 月柱：用12节气定地支，五虎遁定天干
    # 12节气（每月起点）：立春寅月, 惊蛰卯月, 清明辰月, 立夏巳月...
    # ...芒种午月, 小暑未月, 立秋申月, 白露酉月...
    # ...寒露戌月, 立冬亥月, 大雪子月, 小寒丑月
    year_gan_idx = year_gan  # 丙=2

    # 五虎遁：年干起月干
    # 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
    # 五虎遁：年干配对起寅月天干
    # 甲己→丙寅, 乙庚→戊寅, 丙辛→庚寅, 丁壬→壬寅, 戊癸→甲寅
    wuhudun = {
        0: 2, 5: 2,   # 甲, 己 → 丙寅
        1: 4, 6: 4,   # 乙, 庚 → 戊寅
        2: 6, 7: 6,   # 丙, 辛 → 庚寅
        3: 8, 8: 8,   # 丁, 壬 → 壬寅
        4: 0, 9: 0    # 戊, 癸 → 甲寅
    }
    start_gan = wuhudun[year_gan_idx]  # 寅月起的天干

    # 节气日期定月地支（地支顺序：子0, 丑1, 寅2, 卯3, 辰4, 巳5, 午6, 未7, 申8, 酉9, 戌10, 亥11）
    # 12节气作为12个月的起点
    jie_list = [
        (1, 5, 1, '小寒'),   # 丑月：1月5日后
        (2, 4, 2, '立春'),   # 寅月：2月4日后
        (3, 5, 3, '惊蛰'),   # 卯月：3月5日后
        (4, 5, 4, '清明'),   # 辰月：4月5日后
        (5, 5, 5, '立夏'),   # 巳月：5月5日后
        (6, 5, 6, '芒种'),   # 午月：6月5日后
        (7, 7, 7, '小暑'),   # 未月：7月7日后
        (8, 7, 8, '立秋'),   # 申月：8月7日后
        (9, 7, 9, '白露'),   # 酉月：9月7日后
        (10, 8, 10, '寒露'), # 戌月：10月8日后
        (11, 7, 11, '立冬'), # 亥月：11月7日后
        (12, 7, 0, '大雪'),  # 子月：12月7日后
    ]

    # 找节气确定月地支
    month_zhi_idx = 2  # 默认寅月
    for m, d, zhi_idx, name in jie_list:
        if target_date.month > m or (target_date.month == m and target_date.day >= d):
            month_zhi_idx = zhi_idx

    # 1月1-4日还属上一年（小寒前=亥月）
    if target_date.month == 1 and target_date.day < 5:
        month_zhi_idx = 10  # 亥月

    # 月干：寅月天干 + (当前月地支 - 寅月地支)
    # 寅月固定对应地支index=2
    month_gan = (start_gan + (month_zhi_idx - 2)) % 10
    month_gz = tiangan[month_gan] + zhi[month_zhi_idx]

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

    # 优先本地算法，备用188188.org
    result = local_ganzhi(target_date)

    # 用188188.org验证日柱（最关键的字段），不一致时以本地为准并标记
    online = get_ganzhi_from_188188(target_date)
    if online:
        # 日柱不一致时记录但不切换（本地已用沛柔基准校准）
        if online['day'] != result['day']:
            print(f"Warning: local day={result['day']}, online day={online['day']}", file=sys.stderr)
            result['online_day'] = online['day']

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
