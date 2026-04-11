---
name: suanming-bazi-analyzer
description: 八字精批分析。当用户请求八字分析、命盘分析、五行分析、运势预测、大运分析、流年预测时，必须调用此技能。
---

# 八字精批分析技能

## ⚠️ 最重要的规则

**必须通过 `bin/bazi` 入口脚本调用，禁止直接运行底层 Python 脚本。**

调用的正确方式：
```
/opt/homebrew/bin/python3 /Users/georginalau/.openclaw/workspace-suanming/skills/suanming-bazi-analyzer/bin/bazi --year <年> --month <月> --day <日> --hour <时> --minute <分> --gender <male|female> --city <城市> --level full
```

注意：底层脚本是 `bazi_with_five_yun.py`，不要直接调用它，必须经过 `bin/bazi` 入口。

## 触发条件

当用户说以下内容时，立即调用 exec 工具：
- 算八字 / 帮我算八字 / 精批八字
- 八字分析 / 八字精批
- 命盘分析 / 命盘
- 五行分析
- 运势预测 / 看运势
- 大运分析 / 流年预测
- 任何提供出生年月日时分请求分析的情况

## 调用方法

使用 exec 工具，workdir 设为 `/Users/georginalau/.openclaw/workspace-suanming`：

```json
{
  "command": "/opt/homebrew/bin/python3 /Users/georginalau/.openclaw/workspace-suanming/skills/suanming-bazi-analyzer/bin/bazi --year <年> --month <月> --day <日> --hour <时> --minute <分> --gender <male|female> --city <城市> --level full",
  "workdir": "/Users/georginalau/.openclaw/workspace-suanming",
  "timeout": 120
}
```

## 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--year` | ✅ | 出生年（4位数字，如 1990） |
| `--month` | ✅ | 出生月（1-12） |
| `--day` | ✅ | 出生日（1-31） |
| `--hour` | ✅ | 出生小时（24小时制，如 15 表示下午3点） |
| `--minute` | ✅ | 出生分钟（0-59，必须写，用户说"15:45"就要写 `--minute 45`） |
| `--gender` | ✅ | male 或 female |
| `--city` | ✅ | 出生城市（用于真太阳时计算，如"西安""北京"） |
| `--level` | ✅ | 必须写 full |

## 调用示例

**用户说：** "1990年1月8日下午3点45分 女 西安"

```
--year 1990 --month 1 --day 8 --hour 15 --minute 45 --gender female --city 西安 --level full
```

**用户说：** "请帮我分析 1990年8月20日 早上10点 女命，出生地杭州"

```
--year 1990 --month 8 --day 20 --hour 10 --minute 0 --gender female --city 杭州 --level full
```

**用户说：** "帮我看看 1990年1月15日 男 西安 8点"

```
--year 1990 --month 1 --day 15 --hour 8 --minute 0 --gender male --city 西安 --level full
```

## 重要规则

1. **必须通过 `bin/bazi` 入口**，禁止直接调用 `bazi_with_five_yun.py`
2. **必须传 `--minute` 参数**，分钟不能省略
3. **必须传 `--city`**，真太阳时计算需要
4. 脚本输出为 JSON，直接将 `full_report` 内容返回给用户
5. 如果脚本执行失败，读取错误输出，分析原因并修复；无法修复时告知用户并建议重试
