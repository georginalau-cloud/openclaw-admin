# 📊 健康日报 - 飞书消息卡片模板

## 卡片格式说明

此模板用于将日报内容发送至飞书机器人（Webhook）。

---

## 飞书 Webhook 消息卡片 JSON 格式

```json
{
  "msg_type": "interactive",
  "card": {
    "config": {
      "wide_screen_mode": true
    },
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "📊 {{DATE}} 健康日报"
      },
      "template": "blue"
    },
    "elements": [
      {
        "tag": "div",
        "fields": [
          {
            "is_short": true,
            "text": {
              "tag": "lark_md",
              "content": "**⚖️ 晨重**\n{{WEIGHT_MORNING}} kg"
            }
          },
          {
            "is_short": true,
            "text": {
              "tag": "lark_md",
              "content": "**⚖️ 晚重**\n{{WEIGHT_EVENING}} kg"
            }
          },
          {
            "is_short": true,
            "text": {
              "tag": "lark_md",
              "content": "**🫀 静息心率**\n{{RESTING_HR}} bpm"
            }
          },
          {
            "is_short": true,
            "text": {
              "tag": "lark_md",
              "content": "**💤 睡眠得分**\n{{SLEEP_SCORE}}"
            }
          }
        ]
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "fields": [
          {
            "is_short": true,
            "text": {
              "tag": "lark_md",
              "content": "**🔥 总摄入**\n~{{TOTAL_INTAKE}} kcal"
            }
          },
          {
            "is_short": true,
            "text": {
              "tag": "lark_md",
              "content": "**💪 总消耗**\n{{TOTAL_BURNED}} kcal"
            }
          },
          {
            "is_short": false,
            "text": {
              "tag": "lark_md",
              "content": "**📊 热量缺口**\n{{CALORIE_DIFF}} kcal（{{CALORIE_STATUS}}）"
            }
          }
        ]
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**🍽️ 餐食记录**\n🍳 早餐：{{BREAKFAST_SUMMARY}}\n🍱 午餐：{{LUNCH_SUMMARY}}\n🍜 晚餐：{{DINNER_SUMMARY}}"
        }
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**😴 睡眠**\n时长：{{SLEEP_DURATION}} | 深睡：{{SLEEP_DEEP}} | REM：{{SLEEP_REM}}\n\n**🏃 运动**\n步数：{{STEPS}} | 距离：{{DISTANCE}} | 活动消耗：{{ACTIVE_CALORIES}} kcal\n{{EXERCISE_SUMMARY}}"
        }
      },
      {
        "tag": "hr"
      },
      {
        "tag": "action",
        "actions": [
          {
            "tag": "button",
            "text": {
              "tag": "plain_text",
              "content": "✅ 保存日报"
            },
            "type": "primary",
            "value": {
              "action": "save_report",
              "date": "{{DATE_ISO}}"
            }
          },
          {
            "tag": "button",
            "text": {
              "tag": "plain_text",
              "content": "✏️ 修改数据"
            },
            "type": "default",
            "value": {
              "action": "edit_report",
              "date": "{{DATE_ISO}}"
            }
          }
        ]
      }
    ]
  }
}
```

---

## 变量说明

| 变量 | 来源 | 示例 |
|-----|-----|-----|
| `{{DATE}}` | 格式化日期 | `2024年1月15日 星期一` |
| `{{DATE_ISO}}` | ISO 日期 | `2024-01-15` |
| `{{WEIGHT_MORNING}}` | 有品秤（晨） | `65.5` |
| `{{WEIGHT_EVENING}}` | 有品秤（晚） | `66.2` |
| `{{RESTING_HR}}` | Garmin 心率 | `58` |
| `{{SLEEP_SCORE}}` | Garmin 睡眠 | `82` |
| `{{TOTAL_INTAKE}}` | 三餐热量合计 | `1850` |
| `{{TOTAL_BURNED}}` | Garmin 消耗 | `2200` |
| `{{CALORIE_DIFF}}` | 热量差 | `-350` |
| `{{CALORIE_STATUS}}` | 热量状态 | `健康减脂区间` |
| `{{BREAKFAST_SUMMARY}}` | 早餐摘要 | `燕麦粥 + 鸡蛋（420 kcal）` |
| `{{LUNCH_SUMMARY}}` | 午餐摘要 | `米饭 + 鸡胸肉 + 西兰花（650 kcal）` |
| `{{DINNER_SUMMARY}}` | 晚餐摘要 | `蒸鱼 + 青菜（380 kcal）` |
| `{{SLEEP_DURATION}}` | 睡眠时长 | `7h 32m` |
| `{{SLEEP_DEEP}}` | 深睡时长 | `1h 45m` |
| `{{SLEEP_REM}}` | REM 时长 | `1h 20m` |
| `{{STEPS}}` | 步数 | `8,542步` |
| `{{DISTANCE}}` | 距离 | `6.3 km` |
| `{{ACTIVE_CALORIES}}` | 活动消耗 | `420` |
| `{{EXERCISE_SUMMARY}}` | 运动摘要 | `🏋️ 力量训练 45min（280 kcal）` |

---

## Python 发送脚本示例

```python
import json
import os
import requests
from datetime import datetime

def send_daily_report_card(report_data: dict):
    """发送日报消息卡片到飞书"""
    webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("FEISHU_WEBHOOK_URL 未配置")

    # 填充模板变量
    card_content = {
        "msg_type": "interactive",
        "card": {
            # ... 使用上方 JSON 模板，替换变量
        }
    }

    response = requests.post(webhook_url, json=card_content, timeout=10)
    response.raise_for_status()
    return response.json()
```
