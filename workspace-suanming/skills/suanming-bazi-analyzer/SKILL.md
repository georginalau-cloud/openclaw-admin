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
完整的八字精批分析器，基于**子平法**经典理论，供算命喵 agent 在用户提及八字、运势、性格等内容时自动调用。

涵盖七大分析模块：
1. **命盘排布与格局** — 四柱干支、藏干、格局定位、用神忌神
2. **性格特质画像** — 显性/隐性性格、优缺点、天赋
3. **六亲关系** — 父母缘、婚姻感情、子女、晚年
4. **财富事业** — 财富等级、求财方式、行业方向
5. **健康预警** — 五行偏枯对应脏腑、灾厄年识别
6. **大运流年** — 8步大运分析、近5年流年预测
7. **趋吉避凶** — 开运色、吉祥数字、居住方位、合作属相

---

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `year` | integer | ✅ | 公历出生年份（如 1990） |
| `month` | integer | ✅ | 公历出生月份（1-12） |
| `day` | integer | ✅ | 公历出生日期（1-31） |
| `hour` | integer | ❌ | 公历出生小时（0-23，不知时辰可填12） |
| `gender` | string | ❌ | 性别：`male`（男）\| `female`（女） |

---

## 输出

成功时返回 JSON：

```json
{
  "success": true,
  "input": { "year": 1990, "month": 1, "day": 15, "hour": 14, "gender": "male" },
  "generatedAt": "2026-04-05T08:00:00.000Z",
  "fullReport": "═════════════\n🔮 八字精批报告...",
  "sections": {
    "pillarsDisplay": "四柱干支表格",
    "tenGodsAnalysis": { ... },
    "formatAnalysis": { ... },
    "characterProfile": { ... },
    "sixRelationsAnalysis": { ... },
    "wealthCareerAnalysis": { ... },
    "healthAnalysis": { ... },
    "luckCycleAnalysis": { ... },
    "adviceAnalysis": { ... }
  }
}
```

失败时返回：
```json
{
  "success": false,
  "error": "缺少必要参数：year, month, day"
}
```

---

## 使用示例

### 通过 Node.js 直接调用

```bash
# 分析指定生日（男命）
node handler.js --year 1990 --month 1 --day 15 --hour 14 --gender male

# 分析指定生日（女命）
node handler.js --date 1985-05-20 --hour 8 --gender female

# 不知时辰，默认午时
node handler.js --year 1992 --month 8 --day 8 --gender male
```

### 通过算命喵 Agent API 调用

```javascript
const { handle } = require('./skills/suanming-bazi-analyzer/handler');

// 精批分析
const report = await handle({
  year:   1990,
  month:  1,
  day:    15,
  hour:   14,
  gender: 'male',
}, {
  includeAncientBooks: true,  // 是否包含古籍引用（需网络）
  currentYear: 2026,           // 指定当前年份（默认系统年份）
});

if (report.success) {
  console.log(report.fullReport);  // 完整精批报告
  
  // 或访问各模块数据
  const { formatAnalysis, luckCycleAnalysis } = report.sections;
  console.log(formatAnalysis.format); // 如 "正官格"
}
```

### Agent 自动调用触发关键词

当用户消息包含以下关键词时，算命喵 agent 会自动调用此 skill：

> 八字、四柱、命盘、格局、用神、大运、流年、运势、性格分析、婚配、财运、事业运、健康运、子平、排盘、精批

---

## 古籍知识库

### 在线查询（优先）

- **ctext.org** — 中国哲学书电子化计划，查询《子平真诠》《三命通会》等原文
- 查询结果自动缓存到 `~/.openclaw/workspace-suanming/memory/knowledge-cache/`
- 缓存有效期 7 天

### 本地备选

- `data/classic-wisdom.json` — 存储经典著作关键段落摘录
- 在线查询失败时自动降级

---

## 分析模块说明

### 模块1：命盘排布与格局

基于公历生日精确计算四柱（年月日时天干地支），使用：
- **儒略日算法** 计算日柱
- **五虎遁年起月法** 计算月柱天干
- **五鼠遁日起时法** 计算时柱天干
- 简化节气法近似农历月份

格局判断依据《子平真诠》：以月令为主，取月支藏干本气的十神为格。

### 模块2：十神分析

十神：比肩、劫财、食神、伤官、偏财、正财、七杀、正官、偏印、正印

判断日主强弱：
- 月令旺衰（当令/休囚/死绝）
- 帮身力量（比劫+印绶）
- 克泄力量（食伤+财+官杀）

用神取法遵循《子平真诠》：
- 身强 → 用食伤泄秀、财官耗制
- 身弱 → 用印绶帮身、比劫扶持

### 模块6：大运流年

大运计算：
- 阳年男命/阴年女命 → 顺行
- 阴年男命/阳年女命 → 逆行
- 起运年龄约 3-8 岁（简化估算）

流年分析：识别与日支的冲合刑关系，结合用神忌神判断吉凶。

---

## 参考典籍

1. **梁湘润《子平真诠》** — 格局用神理论（最高优先级）
2. **《三命通会》** (万民英) — 六亲与干支五行
3. **《滴天髓》** (刘基) — 性情与日主强弱
4. **《渊海子平》** (徐升) — 特殊格局与六亲
5. **《穷通宝鉴》** (余春台) — 调候用神与行业五行

---

## 依赖

- Node.js ≥ 14.0.0
- 无第三方 npm 依赖（纯 Node.js 标准库）

---

## 文件结构

```
suanming-bazi-analyzer/
├── skill.json                   # Skill 定义与元数据
├── handler.js                   # 主入口（CLI + API）
├── lib/
│   ├── ganzhi-calculator.js    # 干支计算（四柱、藏干、五行）
│   ├── ten-gods-analyzer.js    # 十神分析（强弱、用忌神）
│   ├── format-analyzer.js      # 格局判断（正官格、建禄格等）
│   ├── character-profiler.js   # 性格画像（显性/隐性/天赋/缺陷）
│   ├── six-relations-analyzer.js # 六亲分析（父母、婚姻、子女）
│   ├── wealth-career-analyzer.js # 财富事业（等级、方式、行业）
│   ├── health-predictor.js     # 健康预警（脏腑、灾厄年）
│   ├── luck-cycle-analyzer.js  # 大运流年（8步大运、近5年流年）
│   ├── advice-generator.js     # 趋吉避凶（颜色、数字、方位）
│   └── ancient-books-fetcher.js # 古籍查询（ctext.org + 本地）
├── data/
│   ├── classic-wisdom.json     # 经典著作关键段落（本地备选）
│   ├── ten-gods-traits.json    # 十神性格特征库
│   ├── industries-mapping.json # 五行与行业对应表
│   └── feng-shui-data.json     # 方位、颜色、数字数据
├── SKILL.md                     # 使用文档（本文件）
└── SCHEMA.md                    # 数据结构说明
```

---

## 注意事项

1. **时辰精度** — 如不知确切出生时辰，时柱分析仅供参考，建议填12（午时）
2. **节气边界** — 月柱计算使用简化节气估算，出生在节气前后3天内的需人工核实
3. **大运起运** — 起运年龄为估算值（3-8岁），精确值需按节气日数计算
4. **古籍网络查询** — ctext.org 可能存在访问限制，失败时自动使用本地知识库
5. **参考性质** — 八字分析供参考，命运最终由个人行为决定
