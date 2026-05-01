# 八字精批分析系统

完整的八字命盘分析和五行运势预测工具。

## 功能特性

### 1. 八字排盘
- 真太阳时调整（基于城市经度）
- 干支推导
- 纳音五行
- 十神判断

### 2. 命盘分析
- 日主强弱判断
- 用神忌神分析
- 格局分类
- 特殊格局识别（魁罡格、从格等）

### 3. 大运分析
- 大运排序
- 大运干支推导
- 大运吉凶评估
- 流年预测

### 4. 五行分析
- 五行分布统计
- 五行强弱对比
- 调候用神建议
- 五运深度分析

### 5. 命理学参考
- 《穷通宝鉴》分析
- 《三命通会》参考
- 十二时辰解读
- 星宿吉凶评估

## 使用方式

### 直接调用
```bash
/opt/homebrew/bin/python3 bazi_with_five_yun.py \
  --year 1990 \
  --month 1 \
  --day 15 \
  --hour 8 \
  --gender 男 \
  --city 西安 \
  --level full
echo "✅ README.md 已创建" cat ~/.openclaw/workspace-suanming/skills/suanming-bazi-analyzer/README.md
 EOF

echo "✅ README.md 已创建" cat ~/.openclaw/workspace-suanming/skills/suanming-bazi-analyzer/README.md

### 调用链
bin/bazi（入口）
  └── src/bazi_chart.py（排盘整合）
        ├── src/cities_longitude.py（真太阳时）
        ├── src/yuanju.py（原局四柱）
        │     ├── src/jieqi.py（节气计算）
        │     └── lib/ganzhi_calculator.py（干支计算）
        └── src/dayun.py（大运展开）
              └── src/jieqi.py（节气计算）

  └── src/bazi_chart_year.py（流年盘）
  └── src/bazi_chart_month.py（流月盘）
  └── src/bazi_chart_day.py（流日盘）

  └── lib/ten_gods_analyzer.py（十神分析）
  └── lib/format_analyzer.py（格局用神）
        └── lib/yongshen_analyzer.py（用神引擎）
              └── lib/ganzhi_calculator.py
  └── lib/character_profiler.py（性格画像）
  └── lib/six_relations_analyzer.py（六亲关系）
  └── lib/wealth_career_analyzer.py（财富事业）
  └── lib/health_predictor.py（健康预警）
  └── lib/luck_cycle_analyzer.py（大运流年）
        └── lib/zhi_relations.py（地支关系引擎）
  └── lib/advice_generator.py（趋吉避凶）
  └── lib/wuyu_analyzer.py（妻财子禄寿）
        └── lib/zhi_relations.py
  └── lib/ancient_books_fetcher.py（古籍查询）
  └── lib/daily_fortune.py（日运黄历）
