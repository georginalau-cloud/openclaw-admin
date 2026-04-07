# Trending Now Memory - GuanJia

## Status
status: ongoing
version: 1.0.0
last: 2026-03-24
integration: pending

## Activation Preferences
- 当用户询问"今天有什么新闻"或"国际局势"时自动激活
- heartbeat 模式下每 2-3 小时检查一次
- 重要国际事件立即提醒

## Monitoring Scope
primary_topics:
- 国际政治外交
- 全球经济金融
- 重大自然灾害
- 地缘政治热点
exclude_topics:
- 娱乐新闻
- 体育赛事
- 商业广告
geography: global（特别关注中国、美国、欧洲、俄罗斯、中东）
language_scope: multilingual（中文为主，英文为辅）

## Source Priorities
x_priority: medium
community_sources: 微博热搜、知乎热榜
publisher_sources: 新华社、人民日报、BBC、Reuters
trend_tools: 百度指数、谷歌趋势

## Alert Policy
strictness: balanced
min_score_to_alert: 60
active_hours: 08:00-23:00
timezone: Asia/Shanghai

## Outcomes
- 待记录

## Notes
- 需要至少 2 个独立来源确认才发送提醒
- 重大事件（战争、危机）可放宽来源要求

---
*Updated: 2026-03-24*
