name: bazi_detailed_analyzer

description: 八字精批分析。当用户请求八字分析、命盘分析、五行分析、运势预测、大运分析、流年预测、月运分析、日运分析、妻财子禄寿分析、结构化八字精批时，必须调用此技能。

---

# 八字精批分析技能

## ⚠️ 最重要的规则

**必须通过 `bin/bazi` 入口脚本调用**，禁止直接运行底层 Python 模块。

---

## 默认八字（主人命盘）

当用户没有指定具体八字时，默认使用以下命盘：

```
--year 1990 --month 1 --day 8 --hour 15 --minute 45 --gender female --city 西安
```

**适用场景：**
- 用户说"今天运势怎么样"→ 用默认八字跑日运
- 用户说"这个月运势"→ 用默认八字跑月运
- 用户说"帮我算算"但没给出生信息→ 用默认八字

**例外：**
- 用户明确提供了另一个人的出生信息→ 用那个人的八字
- 用户说"帮我看看XXX的八字"并提供信息→ 用提供的八字

---

## 触发条件

当用户说以下内容时，立即调用 exec 工具：

- 算八字 / 帮我算八字 / 精批八字
- 八字分析 / 八字精批
- 命盘分析 / 命盘
- 五行分析
- 运势预测 / 看运势
- 大运分析 / 流年预测
- 这个月运势 / 月运分析 / X月运势
- 今天运势 / 日运分析 / X日运势
- 妻财子禄寿分析
- 任何提供出生年月日时分并请求命理分析的情况

---

## 四种调用模式

### 模式一：完整精批（--mode full）

适用：用户首次算命，需要完整命盘分析。

```
python3 skills/suanming-bazi-analyzer/bin/bazi \
  --year <年> --month <月> --day <日> --hour <时> --minute <分> \
  --gender <male|female> --city <城市> --mode full
```

**示例：**
```
--year 1990 --month 1 --day 8 --hour 15 --minute 45 --gender female --city 西安 --mode full
```

---

### 模式二：月运分析（--mode monthly）

适用：用户询问某年某月的运势。

```
python3 skills/suanming-bazi-analyzer/bin/bazi \
  --year <出生年> --month <出生月> --day <出生日> --hour <出生时> --minute <出生分> \
  --gender <male|female> --city <城市> --mode monthly \
  --liuyear <流年，如2026> --liuyue-month <流月月序，1=寅月/正月…12=丑月/腊月>
```

**流月月序对照：**

| 月序 | 月支 | 对应节气 | 大约公历月份 |
|------|------|---------|------------|
| 1 | 寅月 | 立春～惊蛰 | 2月 |
| 2 | 卯月 | 惊蛰～清明 | 3月 |
| 3 | 辰月 | 清明～立夏 | 4月 |
| 4 | 巳月 | 立夏～芒种 | 5月 |
| 5 | 午月 | 芒种～小暑 | 6月 |
| 6 | 未月 | 小暑～立秋 | 7月 |
| 7 | 申月 | 立秋～白露 | 8月 |
| 8 | 酉月 | 白露～寒露 | 9月 |
| 9 | 戌月 | 寒露～立冬 | 10月 |
| 10 | 亥月 | 立冬～大雪 | 11月 |
| 11 | 子月 | 大雪～小寒 | 12月 |
| 12 | 丑月 | 小寒～立春 | 1月 |

> 也可以直接传干支：`--liuyue-gz 丙辰`（优先级高于 --liuyue-month）

**示例：** 查询 2026 年 4 月（辰月，月序 3）运势
```
--year 1990 --month 1 --day 8 --hour 15 --minute 45 --gender female --city 西安 \
--mode monthly --liuyear 2026 --liuyue-month 3
```

---

### 模式三：日运分析（--mode daily）

适用：用户询问某天的运势。

```
python3 skills/suanming-bazi-analyzer/bin/bazi \
  --year <出生年> --month <出生月> --day <出生日> --hour <出生时> --minute <出生分> \
  --gender <male|female> --city <城市> --mode daily \
  --liuyear <流年> --liuyue-month <流月月序> --liuri-date <YYYY-MM-DD>
```

> `--liuri-date` 不传时默认今天。
> `--liuyue-month` 不传时根据 `--liuri-date` 自动推算所在流月。

**示例：** 查询 2026-04-15 的日运
```
--year 1990 --month 1 --day 8 --hour 15 --minute 45 --gender female --city 西安 \
--mode daily --liuyear 2026 --liuyue-month 3 --liuri-date 2026-04-15
```

---

### 模式四：仅排盘（--mode quick）

适用：只需要四柱干支，不需要分析。

```
python3 skills/suanming-bazi-analyzer/bin/bazi \
  --year <年> --month <月> --day <日> --hour <时> --minute <分> \
  --gender <male|female> --city <城市> --mode quick
```

---

## 通用参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--year` | ✅ | 出生年（4位数字，如 1990） |
| `--month` | ✅ | 出生月（1-12） |
| `--day` | ✅ | 出生日（1-31） |
| `--hour` | ✅ | 出生小时（24小时制，如 15 表示下午3点） |
| `--minute` | ✅ | 出生分钟（0-59，用户没说就写 `--minute 0`） |
| `--gender` | ✅ | `male` 或 `female` |
| `--city` | ✅ | 出生城市（用于真太阳时校准，用户没说就写 `--city 北京`） |
| `--mode` | ✅ | `full` / `monthly` / `daily` / `quick` |
| `--liuyear` | monthly/daily | 流年公历年份（如 2026） |
| `--liuyue-month` | monthly/daily | 流月月序（1-12，见上表） |
| `--liuyue-gz` | monthly/daily | 流月干支（如 丙辰），优先级高于 --liuyue-month |
| `--liuri-date` | daily | 流日日期 YYYY-MM-DD，默认今天 |

---

## 输出处理流程（重要）

所有模式的输出 JSON 都包含 `prompt_for_llm` 字段：

```
{
  "prompt_for_llm": {
    "system_context":  命盘结构化数据（背景信息）
    "writing_prompt":  给 MiniMax 的写作指令
    "usage_note":      处理说明
  }
}
```

### OpenClaw 处理步骤（所有模式通用）

**第一步：执行脚本，获取 JSON 输出**

**第二步：将 `prompt_for_llm.writing_prompt` 作为用户消息，`prompt_for_llm.system_context` 作为背景数据，发给 MiniMax**

**第三步：将 MiniMax 生成的正文回复给用户**

> full 模式还有 `full_report` 字段（结构化原始报告），仅供调试，不直接发给用户。

---

## 分析层级说明

五运分析（妻财子禄寿）严格遵循层级结构，不可跳级：

```
原局（命局底色）
  └── 大运（10年背景）
        └── 流年（年度叠加）
              └── 流月（月度叠加）← monthly 模式到此层
                    └── 流日（日度叠加）← daily 模式到此层
```

- `full` 模式：原局 + 当前大运 + 当前流年（三层）
- `monthly` 模式：原局 + 大运 + 流年 + 指定流月（四层）
- `daily` 模式：原局 + 大运 + 流年 + 流月 + 指定流日（五层）

---

## 重要规则

- 必须通过 `bin/bazi` 入口，禁止直接调用 `lib/` 或 `src/` 里的文件
- 必须传 `--minute` 参数，分钟不能省略（用户没说就写 `--minute 0`）
- 必须传 `--city`，真太阳时计算需要（用户没说城市就写 `--city 北京` 作为默认）
- monthly/daily 模式必须传 `--liuyear`，不传则默认今年
- 脚本执行失败时，读取错误输出，分析原因；无法修复时告知用户并建议重试
