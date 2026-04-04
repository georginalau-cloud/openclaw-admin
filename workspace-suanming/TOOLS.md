# 🔮 算命喵 Agent - TOOLS.md

## 工具配置手册

---

## 环境变量配置

所有 API Key 和配置项存储于 `~/.openclaw/.env`，格式如下：

```bash
# 飞书 Webhook（必填）
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your_webhook_token

# 黄历来源 URL（默认 188188.org，可覆盖）
HUANGLI_SOURCE_URL=https://www.188188.org

# 工作空间路径（可选，默认 ~/.openclaw/workspace-suanming）
WORKSPACE_PATH=~/.openclaw/workspace-suanming

# 媒体文件路径（飞书图片接收目录）
MEDIA_INBOUND_PATH=~/.openclaw/media/inbound
```

加载环境变量：

```python
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.openclaw/.env"))
```

---

## 1. 黄历数据抓取（188188.org）

### 脚本路径

```
scripts/fetch-huangli.py
```

> **TODO**: 此脚本待开发。以下为规划中的接口说明，实现后请更新此文档。

### 功能说明

从 188188.org 抓取当日黄历数据，包含：
- 农历日期
- 干支（年柱、月柱、日柱）
- 当日宜忌

### 使用方法

```bash
python3 ~/.openclaw/workspace-suanming/scripts/fetch-huangli.py --date 2026-04-04
```

### 返回格式

```json
{
  "success": true,
  "date": "2026-04-04",
  "lunar_date": "三月初七",
  "ganzhi": {
    "year": "丙午",
    "month": "壬辰",
    "day": "甲午"
  },
  "yi": ["祭祀", "出行", "开市"],
  "ji": ["动土", "安葬"]
}
```

---

## 2. 干支计算脚本

### 脚本路径

```
scripts/get_ganzhi.py
```

### 功能说明

本地计算指定日期的干支（年柱、月柱、日柱、时柱），无需网络请求。

### 使用方法

```bash
python3 ~/.openclaw/workspace-suanming/scripts/get_ganzhi.py --date 2026-04-04
```

### 返回格式

```json
{
  "success": true,
  "date": "2026-04-04",
  "year_gz": "丙午",
  "month_gz": "壬辰",
  "day_gz": "甲午",
  "hour_gz": "庚子"
}
```

---

## 3. 每日早运脚本

### 脚本路径

```
scripts/morning-fortune.sh
```

### 功能说明

每天早 8 点 Cron 触发，执行以下步骤：
1. 调用 `fetch-huangli.py` 获取当日黄历干支
2. 从 `USER.md` 读取用户八字
3. 基于子平法计算流年流月流日与原局的交互作用
4. 生成当日运势分析文本

### 环境变量传参

| 变量名 | 说明 |
|--------|------|
| `HUANGLI_DATA` | JSON 格式的黄历数据（由 core.js 传入） |
| `USER_INFO` | USER.md 的文本内容 |
| `FORTUNE_DATE` | 分析日期（YYYY-MM-DD） |

### 调用方式

```bash
HUANGLI_DATA='{"ganzhi":{"day":"甲午"}}' \
USER_INFO="$(cat ~/.openclaw/workspace-suanming/USER.md)" \
FORTUNE_DATE="2026-04-04" \
bash ~/.openclaw/workspace-suanming/scripts/morning-fortune.sh
```

---

## 4. 子平法分析规则

### 当前实现级别

- ✅ 干支计算（年柱、月柱、日柱）
- ✅ 流年流月流日与原局简单交互分析
- ⚠️ TODO: 寻找现成的子平法 skill，或开发 daily-huangli-analyzer

### 分析重点

- **主要关注**：流年流月流日与原局的交互作用（冲、合、刑、害）
- **不过分强调**：原局本身的格局（入门时已分析过）

### 参考典籍

- 梁湘润《子平法精粹》《八字论命系列》
- 倪海厦《人纪》（天纪命理篇）
- TODO: 古籍知识库在线化方案（ctext.org 或其他）

---

## 5. Skills 调用说明

### qveris（视频搜索）

搜索 B站/YouTube/港台玄学视频：

```bash
# 通过 OpenClaw skill 接口调用
# 参考 skills/qveris/SKILL.md 获取详细用法
```

### pdf-ocr（古籍 OCR）

识别本地古籍 PDF 扫描件：

```bash
python3 ~/.openclaw/workspace-suanming/skills/pdf-ocr/scripts/pdf_to_docx.py \
    --input /path/to/guzhi.pdf \
    --output /path/to/output.docx
```

### isolated-chrome（浏览器隔离）

访问黄历网站和知识库：

```bash
# 通过 OpenClaw skill 接口调用
# 参考 skills/isolated-chrome/SKILL.md 获取详细用法
```

---

## 6. 数据存储路径

```
~/.openclaw/workspace-suanming/
├── memory/
│   ├── USER.md                            # 用户基本信息（含八字）
│   ├── MEMORY.md                          # 用户长期记忆
│   ├── pending/
│   │   ├── YYYY-MM-DD-fortune.json       # 当日运势分析结果
│   │   ├── huangli-YYYY-MM-DD.json       # 黄历数据缓存
│   │   └── video-summary-xxx.md          # 视频总结（TODO）
│   └── reports/
│       └── YYYY-MM-DD-fortune.md         # 归档的运势报告
├── 玄学案例/
│   ├── 八字案例/                          # 用户提供的八字学习案例
│   ├── 紫薇案例/                          # 用户提供的紫薇斗数案例
│   ├── 六爻案例/                          # 用户提供的六爻案例
│   └── ...
└── scripts/
    ├── morning-fortune.sh                 # 每日早运脚本（已有）
    ├── get_ganzhi.py                      # 干支计算（已有）
    └── fetch-huangli.py                   # 从 188188.org 抓取黄历（待开发）
```

---

## 7. 知识库

### 古籍数据库

- **中国哲学书电子化计划** - https://ctext.org/zhs
  - 历代古籍原文检索，涵盖经史子集各部门
  - TODO: 古籍知识库在线化方案（ctext.org 存在验证限制，暂保留本地 PDF）

### 视频教程

- **倪海厦人纪系列** - https://www.bilibili.com/list/ml3329471754?oid=684300521&bvid=BV1AU4y127mw
  - 人纪系列（天纪已上传，地纪筹备中）

- **梁湘润命理系列** - https://www.youtube.com/results?search_query=梁湘润
  - 《梁湘润子平概论全集》(2011) - 核心教材系列
  - 八字十神专题
  - 各种命理分析案例

---

## TODOs

```
// TODO: 寻找现成的子平法 skill，或开发 daily-huangli-analyzer
// TODO: 古籍知识库在线化方案（ctext.org 或其他）
// TODO: 支持紫薇斗数、六爻、奇门遁甲等其他术数
// TODO: 视频总结 skill 集成（qveris + openai-whisper + summarize）
// TODO: 开发 fetch-huangli.py（从 188188.org 抓取黄历干支）
```
