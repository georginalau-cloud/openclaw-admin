#!/bin/bash

# 算命喵 - 每日运势推送
# 沛柔八字: 己巳 丁丑 癸酉 己未
# 喜金水，忌土火

cd /Users/georginalau/.openclaw/workspace-suanmingmiao

# 调用算命喵生成并发送每日运势
openclaw agent --agent suanming --channel feishu --deliver --reply-to ou_f9095feb1adeb3f3997725460bcdd87d -m "请根据我的八字喜忌（喜金、水，忌土、火）分析今天的运势。

我的八字：己巳 丁丑 癸酉 己未

请按以下框架生成运势推送：

1. 今日干支（流年流月流日）
2. 五行格局分析（只分析流年流月流日的五行关系，无需分析我的原局）
3. 当日喜忌（结合流年流月流日判断对我是否有利）
4. 穿衣颜色建议（根据五行喜忌推荐）
5. 注意事项
6. 今日宜忌

用表格清晰呈现，保持简洁。" --timeout 120

echo "$(date '+%Y-%m-%d %H:%M:%S'): 每日运势已发送"
