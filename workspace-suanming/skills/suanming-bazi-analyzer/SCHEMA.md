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
# 📋 SCHEMA.md — 数据结构说明

## handle() 函数返回值结构

```typescript
interface BaziAnalysisResult {
  success:     boolean;         // 是否成功
  input:       InputParams;     // 输入参数（原样返回）
  generatedAt: string;          // ISO 时间戳
  fullReport:  string;          // 完整精批报告文本
  sections:    ReportSections;  // 各模块结构化数据
  baziData:    BaziData;        // 原始四柱数据
  error?:      string;          // 错误信息（success=false 时）
}
```

---

## InputParams

```typescript
interface InputParams {
  year:   number;  // 公历年份
  month:  number;  // 公历月份（1-12）
  day:    number;  // 公历日（1-31）
  hour:   number;  // 小时（0-23）
  gender: 'male' | 'female';
}
```

---

## BaziData（四柱基础数据）

```typescript
interface BaziData {
  pillars: {
    year:  Pillar;  // 年柱
    month: Pillar;  // 月柱
    day:   Pillar;  // 日柱
    hour:  Pillar;  // 时柱
  };
  hiddenStems: {
    year:  string[];  // 年支藏干
    month: string[];  // 月支藏干
    day:   string[];  // 日支藏干
    hour:  string[];  // 时支藏干
  };
  elementCount: {
    木: number; 火: number; 土: number; 金: number; 水: number;
  };
  dayMaster:        string;  // 日主天干（如 "甲"）
  dayMasterElement: string;  // 日主五行（如 "木"）
  dayMasterYinYang: string;  // 日主阴阳（"阳" | "阴"）
  luckCycleInfo: {
    isForward:       boolean;  // 是否顺行
    direction:       string;   // "顺行" | "逆行"
    approxStartAge:  number;   // 起运年龄（估算）
    note:            string;   // 说明文字
  };
  input:       InputParams;
  lunarMonth:  number;       // 近似农历月份（1-12）
}

interface Pillar {
  stem:   string;   // 天干（如 "甲"）
  branch: string;   // 地支（如 "子"）
  ganzhi: string;   // 干支组合（如 "甲子"）
}
```

---

## TenGodsAnalysis（十神分析）

```typescript
interface TenGodsAnalysis {
  dayMaster:        string;
  dayMasterElement: string;
  tenGods: {
    year:  TenGodPosition;
    month: TenGodPosition;
    day:   TenGodPosition;
    hour:  TenGodPosition;
    tenGodCount: Record<string, number>;  // 各十神数量
    tenGodList:  Array<{ tenGod: string; position: string }>;
  };
  strengthAnalysis: {
    monthStatus:    string;   // "当令" | "休囚" | "死绝"
    monthStrength:  number;   // 月令分值（-1~3）
    helpScore:      number;   // 帮身力量
    weakenScore:    number;   // 克泄力量
    totalScore:     number;   // 综合分值
    strength:       'very_strong' | 'strong' | 'balanced' | 'weak' | 'very_weak';
    strengthLabel:  string;   // 中文说明
    isStrong:       boolean;
  };
  yongJiShen: {
    yongShen:         string[];  // 用神五行
    jiShen:           string[];  // 忌神五行
    yongShenTenGods:  string[];  // 用神十神
    jiShenTenGods:    string[];  // 忌神十神
    analysis:         string;    // 分析文字
  };
  summary: string;  // 汇总文本
}

interface TenGodPosition {
  stem:   string;  // 天干十神（如 "正官"）
  branch: string;  // 地支十神
  hidden: Array<{ stem: string; tenGod: string }>;  // 藏干十神
}
```

---

## FormatAnalysis（格局分析）

```typescript
interface FormatAnalysis {
  format:           string;   // 格局名称（如 "正官格"）
  monthBranch:      string;   // 月支
  isSpecial:        boolean;  // 是否特殊格
  isFormed:         boolean;  // 是否成格
  level:            'high' | 'mid' | 'low';  // 格局层次
  yi:               string[];  // 格局喜忌（喜）
  ji:               string[];  // 格局喜忌（忌）
  description:      string;   // 格局描述
  levelDescription: string;   // 层次描述
  summary:          string;   // 汇总文本
}
```

---

## CharacterProfile（性格画像）

```typescript
interface CharacterProfile {
  dayMasterSummary:    string;    // 日主概述
  basePersonality:     string;    // 基础性格
  visiblePersonality:  string;    // 显性性格（别人眼中的你）
  hiddenPersonality:   string;    // 隐性性格（内心真实渴望）
  strengths:           string[];  // 核心优点（最多6个）
  weaknesses:          string[];  // 主要缺点（最多5个）
  talents:             string[];  // 天赋领域（最多5个）
  defects:             string[];  // 性格缺陷（最多4个）
  summary:             string;    // 汇总文本
}
```

---

## SixRelationsAnalysis（六亲关系）

```typescript
interface SixRelationsAnalysis {
  parents: {
    fatherBond:         string;  // 父缘描述
    motherBond:         string;  // 母缘描述
    ancestralBlessing:  string;  // 祖荫
    detail:             string;
  };
  marriage: {
    spouseFeatures:     string;  // 配偶特征
    stability:          string;  // 婚姻稳定性
    remarriageRisk:     string;  // 二婚风险
    compatibleElements: string;  // 婚配建议
    bestMarriageAge:    string;  // 最佳婚龄
    detail:             string;
  };
  children: {
    childBond:   string;  // 子女缘
    childCount:  string;  // 子女数量估计
    detail:      string;
  };
  siblings: { detail: string };
  laterLife: { quality: string; detail: string };
  summary:   string;
}
```

---

## WealthCareerAnalysis（财富事业）

```typescript
interface WealthCareerAnalysis {
  wealthLevel: {
    score:           number;  // 综合分值
    level:           'great_wealth' | 'moderate_wealth' | 'small_wealth' | 'modest';
    description:     string;  // 等级描述
    characteristics: string;  // 特征描述
  };
  wealthMethod: {
    primaryMethods: string[];  // 主要求财方式
    methods:        Array<{ type: string; desc: string }>;
    riskWarning:    string[];  // 财务风险提示
    summary:        string;
  };
  careerIndustries: {
    recommended: Array<{ element: string; industries: string[]; reason: string }>;
    avoid:       Array<{ element: string; industries: string[]; reason: string }>;
  };
  careerPeakValleys: {
    naturalPeak:     string;  // 自然旺盛期（季节）
    naturalValley:   string;  // 自然低谷期
    formatNote:      string;  // 格局事业说明
    generalPattern:  string;  // 整体规律
  };
  wealthAdvice: string[];
  summary:      string;
}
```

---

## HealthAnalysis（健康预警）

```typescript
interface HealthAnalysis {
  elementBalance: {
    analysis: Record<string, { count: number; ratio: string; status: string }>;
    weakest:  string;  // 最弱五行
    strongest: string; // 最强五行
    total:    number;
  };
  organRisks: Array<{
    element:  string;
    organs:   string[];
    risks:    string[];
    severity: 'high' | 'medium';
    note:     string;
  }>;
  primaryHealthFocus: string;
  ageHealthTips: Array<{ phase: string; focus: string }>;
  disasterYears: Array<{ type: string; trigger: string; note: string }>;
  avoidanceAdvice: string[];
  summary:         string;
}
```

---

## LuckCycleAnalysis（大运流年）

```typescript
interface LuckCycleAnalysis {
  luckCycleInfo: {
    isForward:      boolean;
    direction:      string;
    approxStartAge: number;
    note:           string;
  };
  luckCycles: Array<{
    index:        number;
    stem:         string;
    branch:       string;
    ganzhi:       string;
    startAge:     number;
    endAge:       number;
    startYear:    number;
    endYear:      number;
    stemTenGod:   string;
    branchTenGod: string;
    fortune:      '大吉' | '吉' | '平' | '凶' | '大凶';
    fortuneScore: number;  // 1-5
    analysis:     string;
  }>;
  currentLuckCycle: LuckCycle | { note: string; ganzhi: string; fortune: string };
  annualFortunes: Array<{
    year:         number;
    ganzhi:       string;
    stem:         string;
    branch:       string;
    stemTenGod:   string;
    branchTenGod: string;
    chong:        boolean;
    he:           boolean;
    xing:         boolean;
    fortune:      string;
    detail:       string;
  }>;
  turningPoints: Array<{
    type:  string;
    year?: number;
    age?:  number;
    desc:  string;
  }>;
  summary: string;
}
```

---

## AdviceAnalysis（趋吉避凶建议）

```typescript
interface AdviceAnalysis {
  luckyColors: {
    primary:   string[];  // 主色
    secondary: string[];  // 辅色
    avoid:     string[];  // 忌用色
    reason:    string;
  };
  luckyNumbers: {
    numbers: number[];
    reason:  string;
    advice:  string;
  };
  luckyDirections: {
    best:        string[];
    good:        string[];
    avoid:       string[];
    homeAdvice:  string;
    reason:      string;
  };
  compatibleZodiac: {
    compatible:         string[];
    compatibleBranches: string[];
    reason:             string;
    advice:             string;
  };
  generalAdvice: Array<{ category: string; content: string }>;
  summary:       string;
}
```

---

## 十神名称对照表

| 十神 | 英文Code | 关系 | 阴阳 |
|------|---------|------|------|
| 比肩 | biJian | 同我 | 同阴阳 |
| 劫财 | jieCAI | 同我 | 异阴阳 |
| 食神 | shiShen | 我生 | 同阴阳 |
| 伤官 | shangGuan | 我生 | 异阴阳 |
| 偏财 | pianCAI | 我克 | 异阴阳 |
| 正财 | zhengCAI | 我克 | 同阴阳 |
| 七杀 | qiSha | 克我 | 异阴阳 |
| 正官 | zhengGuan | 克我 | 同阴阳 |
| 偏印 | pianYin | 生我 | 异阴阳 |
| 正印 | zhengYin | 生我 | 同阴阳 |

## 格局名称对照

| 格局名 | 条件 | 特点 |
|--------|------|------|
| 正官格 | 月令本气为正官 | 仁义正直，官运亨通 |
| 七杀格 | 月令本气为七杀 | 威猛果断，须有制化 |
| 食神格 | 月令本气为食神 | 福寿聪明，衣食丰足 |
| 伤官格 | 月令本气为伤官 | 才华横溢，需配合适当 |
| 正财格 | 月令本气为正财 | 勤俭积财，婚姻美满 |
| 偏财格 | 月令本气为偏财 | 豪爽重义，财运亨通 |
| 正印格 | 月令本气为正印 | 学识高雅，官印相生 |
| 偏印格 | 月令本气为偏印 | 聪颖机敏，须财制枭 |
| 建禄格 | 月令与日干同五行（长生/临官） | 自立自强，靠自身发迹 |
| 月刃格 | 阳干逢月令帝旺 | 威猛刚烈，须官杀制化 |
