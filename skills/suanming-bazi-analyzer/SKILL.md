---
name: suanming-bazi-analyzer
description: 八字精批分析 - 基于出生日期、时间、性别和地点，生成详细的八字命盘分析和五行运势预测
metadata:
  emoji: 🔮
  os: [darwin, linux]
  requires:
    bins: [python3]
---

# 八字精批 Skill

## 描述
提供详细的八字命盘分析和五行运势预测。基于用户提供的出生日期、时间、性别和地点，生成完���的八字精批报告。

## 用途
当用户要求进行以下操作时激活：
- 八字分析
- 八字精批
- 命盘分析
- 五行分析
- 运势预测
- 大运分析

## 命令
```bash
/opt/homebrew/bin/python3 bazi_with_five_yun.py \
  --year 1990 \
  --month 1 \
  --day 15 \
  --hour 8 \
  --gender 男 \
  --city 西安 \
  --level full
