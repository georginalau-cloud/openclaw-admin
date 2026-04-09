# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 干支计算（本地算法）

### 脚本位置
- `/Users/georginalau/.openclaw/workspace-suanming/scripts/get_ganzhi.py`

### 参照系（沛柔验证）
- **2026-01-01 = 乙巳年 戊子月 乙亥日**

### 算法原理
1. **日柱**：以参照系为基准，天干地支各自循环加天数
2. **年柱**：1984=甲子，2026=丙午，直接取模
3. **月柱**：
   - 用12节气定地支（节后换月）
   - 五虎遁定天干

### 12节气月地支表
| 节气 | 月份地支 |
|------|---------|
| 立春(2/4) | 寅月 |
| 惊蛰(3/5) | 卯月 |
| 清明(4/5) | 辰月 |
| 立夏(5/5) | 巳月 |
| 芒种(6/5) | 午月 |
| 小暑(7/7) | 未月 |
| 立秋(8/7) | 申月 |
| 白露(9/7) | 酉月 |
| 寒露(10/8) | 戌月 |
| 立冬(11/7) | 亥月 |
| 大雪(12/7) | 子月 |
| 小寒(1/5) | 丑月 |

### 五虎遁（年起月干）
- 甲己 → 丙寅
- 乙庚 → 戊寅
- 丙辛 → 庚寅
- 丁壬 → 壬寅
- 戊癸 → 甲寅

### 注意事项
- 1月1-4日（小寒前）仍属亥月
- 节气日期为近似值，每年可能有1天波动
- **完全自力更生，不依赖外部网站**

### 用法
```bash
python3 scripts/get_ganzhi.py [YYYY-MM-DD]
# 不带参数默认今天
```

---

## 知识库

### 古籍数据库

- **中国哲学书电子化计划** - https://ctext.org/zhs
  - 历代古籍原文检索，涵盖经史子集各部门

### 黄历数据源（备用）

- **188188.org：** https://www.188188.org/huangli/ （主站已改版，仅备用）
- **老黄历：** https://laohuangli.bmcx.com/
- **水墨先生：** https://m.smxs.com/hl/2026-4-9.html

### 视频教程

- **倪海厦人纪系列** - https://www.bilibili.com/list/ml3329471754?oid=684300521&bvid=BV1AU4y127mw
  - 人纪系列（天纪已上传，地纪筹备中）

- **梁湘润命理系列** - https://www.youtube.com/results?search_query=梁湘润
  - 《梁湘润子平概论全集》(2011) - 核心教材系列
  - 八字十神专题
  - 各种命理分析案例

Add whatever helps you do your job. This is your cheat sheet.
