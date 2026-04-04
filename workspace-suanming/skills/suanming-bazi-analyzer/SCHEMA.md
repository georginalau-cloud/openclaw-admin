# SCHEMA.md - 八字精批 Skill 数据结构说明

## 输入参数

```
--year    int     出生年（公历，1800-2100）
--month   int     出生月（1-12）
--day     int     出生日（1-31）
--hour    int     出生时辰（0-23，子时=0/23，丑时=1-2，...）
--gender  string  male / female / unknown
--level   string  full / quick
--years   int...  流年预测年份列表（可选）
```

---

## 输出结构（JSON）

### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | bool | 是否成功 |
| `error` | string | 失败原因（仅 success=false 时有） |
| `birth_info` | object | 原始出生参数 |
| `gender` | string | 性别 |
| `level` | string | 分析层级 |
| `pillars` | object | 四柱干支 |
| `day_master` | string | 日主天干（如"癸"） |
| `day_master_element` | string | 日主五行 |
| `zodiac` | string | 生肖 |
| `format` | string | 格局名称 |
| `strength` | string | 日主旺衰（旺/中/弱） |
| `yong_shen` | string | 用神五行 |
| `ji_shen` | string[] | 忌神五行列表 |
| `dominant_ten_gods` | object[] | 主导十神排行（前5） |
| `character_summary` | string | 性格画像摘要 |
| `six_relations_summary` | string | 六亲分析摘要 |
| `wealth_summary` | string | 财富事业摘要 |
| `health_summary` | string | 健康预警摘要 |
| `luck_summary` | string | 大运流年摘要 |
| `advice_summary` | string | 趋吉避凶摘要 |
| `full_report` | string | 完整精批报告（7模块）|
| `generated_at` | string | 生成时间（ISO 8601） |

---

### pillars 对象

```json
{
  "year":  "庚午",
  "month": "丙子",
  "day":   "癸亥",
  "hour":  "甲辰"
}
```

---

### dominant_ten_gods 数组

```json
[
  { "ten_god": "正官", "weight": 6 },
  { "ten_god": "偏印", "weight": 4 },
  ...
]
```

---

### 失败输出

```json
{
  "success": false,
  "error": "输入参数错误：月份无效：13（应为1-12）"
}
```

---

## 时辰对照表

| 时辰 | 地支 | 时间范围 |
|------|------|---------|
| 子时 | 子 | 23:00 - 00:59 |
| 丑时 | 丑 | 01:00 - 02:59 |
| 寅时 | 寅 | 03:00 - 04:59 |
| 卯时 | 卯 | 05:00 - 06:59 |
| 辰时 | 辰 | 07:00 - 08:59 |
| 巳时 | 巳 | 09:00 - 10:59 |
| 午时 | 午 | 11:00 - 12:59 |
| 未时 | 未 | 13:00 - 14:59 |
| 申时 | 申 | 15:00 - 16:59 |
| 酉时 | 酉 | 17:00 - 18:59 |
| 戌时 | 戌 | 19:00 - 20:59 |
| 亥时 | 亥 | 21:00 - 22:59 |

---

## 五行行业与方位速查

| 五行 | 方位 | 颜色 | 代表行业 |
|------|------|------|---------|
| 木 | 东 | 绿/青 | 教育、医疗、法律、设计 |
| 火 | 南 | 红/橙 | 科技、媒体、餐饮、娱乐 |
| 土 | 中 | 黄/棕 | 房产、建筑、政府、金融 |
| 金 | 西 | 白/金 | 金融、军警、制造、外科 |
| 水 | 北 | 黑/深蓝 | 贸易、传媒、旅游、心理 |
