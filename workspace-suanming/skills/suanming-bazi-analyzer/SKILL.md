# 🔮 Skill: suanming-bazi-analyzer

## 功能说明

基于《子平真诠》《滴天髓》《渊海子平》《三命通会》《穷通宝鉴》等经典命理著作，
提供全面的八字精批分析，包含 7 个核心分析模块。

---

## 目录结构

```
suanming-bazi-analyzer/
├── bazi_analyzer.py          # 主入口（CLI + 核心调度）
├── lib/
│   ├── ganzhi_calculator.py        # 干支四柱计算（万年历算法）
│   ├── ten_gods_analyzer.py        # 十神分析
│   ├── format_analyzer.py          # 格局判断 + 用神忌神
│   ├── character_profiler.py       # 性格深度画像
│   ├── six_relations_analyzer.py   # 六亲关系分析
│   ├── wealth_career_analyzer.py   # 财富事业分析
│   ├── health_predictor.py         # 健康预警
│   ├── luck_cycle_analyzer.py      # 大运流年预测
│   ├── advice_generator.py         # 趋吉避凶建议
│   └── ancient_books_fetcher.py    # 古籍查询（ctext.org + 本地备选）
├── data/
│   ├── classic-texts.json          # 《滴天髓》《渊海子平》等关键段落
│   ├── ten-gods-traits.json        # 十神性格库 + 日主性格库
│   ├── industries-mapping.json     # 五行行业对应
│   ├── feng-shui-data.json         # 开运色、数字、方位数据
│   └── format-definitions.json     # 格局定义与特征
├── SKILL.md                        # 本文档
└── SCHEMA.md                       # 输入输出结构说明
```

---

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--year` | int | ✅ | 公历出生年份 |
| `--month` | int | ✅ | 公历出生月（1-12） |
| `--day` | int | ✅ | 公历出生日（1-31） |
| `--hour` | int | | 出生时辰（0-23，默认0=子时） |
| `--gender` | string | | 性别：male / female / unknown（默认 unknown） |
| `--level` | string | | 分析深度：full（完整精批，默认）/ quick（快速） |
| `--years` | int... | | 指定流年年份（如 2025 2026），不指定则预测未来3年 |

---

## 使用方法

### 基础用法

```bash
python3 ~/.openclaw/workspace-suanming/skills/suanming-bazi-analyzer/bazi_analyzer.py \
    --year 1990 --month 1 --day 15 --hour 8 --gender male
```

### 指定流年

```bash
python3 bazi_analyzer.py \
    --year 1990 --month 1 --day 15 --hour 8 \
    --gender female --level full \
    --years 2025 2026 2027
```

### 快速分析

```bash
python3 bazi_analyzer.py --year 1985 --month 6 --day 20 --level quick
```

---

## 输出格式

JSON 输出到 stdout，结构如下：

```json
{
  "success": true,
  "pillars": {
    "year": "庚午",
    "month": "丙子",
    "day": "癸亥",
    "hour": "甲辰"
  },
  "day_master": "癸",
  "day_master_element": "水",
  "zodiac": "马",
  "format": "正官格",
  "strength": "中",
  "yong_shen": "金",
  "ji_shen": ["土", "火"],
  "dominant_ten_gods": [...],
  "character_summary": "...",
  "six_relations_summary": "...",
  "wealth_summary": "...",
  "health_summary": "...",
  "luck_summary": "...",
  "advice_summary": "...",
  "full_report": "完整精批报告文字（7个模块）",
  "generated_at": "2026-04-04T18:00:00"
}
```

---

## 7 个分析模块

### 【一】基础命盘排布与定格
- 年月日时四柱干支
- 地支藏干与十神关系
- 格局判断（正官格、偏财格、食神格等）
- 日主强弱、用神与忌神

### 【二】性格特质深度画像
- 显性性格（别人眼中的你）
- 隐性性格（内心真实渴望）
- 核心优势与性格盲点

### 【三】六亲关系与社会脉络
- 父母缘分与祖荫
- 婚姻感情（配偶特质、婚姻风险）
- 子女情况与晚年福气

### 【四】事业财运分析
- 财富等级（平稳 / 小康 / 中富 / 巨富）
- 求财方式（薪资 / 经商 / 才华变现）
- 五行行业推荐
- 事业高低点识别

### 【五】身体健康预警
- 五行分布与脏腑风险
- 体质倾向分析
- 具体健康建议

### 【六】大运与流年预测
- 十年大运方向与起运年龄
- 近3年流年详细预测（事业/财运/感情）
- 刑冲克害识别

### 【七】趋吉避凶建议
- 开运色推荐
- 吉祥数字
- 最佳居住/办公方位
- 合作伙伴属相建议
- 人生改运建议

---

## 古籍数据来源

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | ctext.org API | 《滴天髓》等有 URN 的典籍 |
| 2 | 本地 JSON 库 | 五本经典著作关键段落摘录 |

**古籍优先级**：梁湘润《子平真诠》> 《三命通会》> 《滴天髓》> 《渊海子平》> 《穷通宝鉴》

查询结果自动缓存 72 小时，路径：`~/.openclaw/workspace-suanming/memory/knowledge-cache/`

---

## 调用方式（算命 Agent）

算命 agent 在用户提及"精批"、"八字精批"、"详细分析"并提供出生日期时，
通过 `core.js` 的 `runPythonScript` 调用此 skill：

```javascript
const script = path.join(SKILLS_DIR, 'suanming-bazi-analyzer', 'bazi_analyzer.py');
const result = await runPythonScript(script, [
    '--year', '1990',
    '--month', '1',
    '--day', '15',
    '--hour', '8',
    '--gender', 'male',
    '--level', 'full',
]);
// result.full_report 即完整精批报告
```

---

## 注意事项

1. **算法精度**：节气采用近似日期，实际节气时间可能前后1天偏差。精准分析请人工核实立春日期。
2. **从格判断**：极端命局（从格）需由专业命理师确认，自动判断仅供参考。
3. **调候用神**：本版本使用通用用神法，完整调候分析（《穷通宝鉴》体系）需进一步开发。
4. **命运观**：八字分析为概率性参考，命运最终由个人选择决定。
