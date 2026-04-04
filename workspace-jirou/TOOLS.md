# 🔧 肌肉 Agent - TOOLS.md

## 工具配置手册

---

## 环境变量配置

所有 API Key 和配置项存储于 `~/.openclaw/.env`，格式如下：

```bash
# Google Vision API
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here

# MiniMax API
MINIMAX_API_KEY=your_minimax_api_key_here
MINIMAX_GROUP_ID=your_minimax_group_id_here

# USDA FoodData Central API
# 申请地址：https://fdc.nal.usda.gov/api-guide.html
# 免费 key，每小时 1000 次请求
USDA_API_KEY=DEMO_KEY

# Garmin 账号（gccli 使用）
GARMIN_EMAIL=your_garmin_email@example.com
GARMIN_PASSWORD=your_garmin_password

# 媒体文件路径
MEDIA_INBOUND_PATH=~/.openclaw/media/inbound
WORKSPACE_PATH=~/.openclaw/workspace-jirou
```

加载环境变量：

```python
from dotenv import load_dotenv
load_dotenv(os.path.expanduser("~/.openclaw/.env"))
```

---

## 1. EasyOCR

### 安装状态

EasyOCR 已安装于 `~/.EasyOCR/`，支持中英文识别。

### 使用方法

```python
import easyocr

# 初始化（首次会下载模型，后续从缓存加载）
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False, model_storage_directory='~/.EasyOCR/')

# 识别图片
results = reader.readtext('/path/to/image.jpg')
# 返回格式：[(坐标, 文字, 置信度), ...]
```

### 配置建议

- 语言：`['ch_sim', 'en']`（中文简体 + 英文）
- GPU：默认 False（无 GPU 时）
- 模型路径：`~/.EasyOCR/`

---

## 2. Google Vision API

### 功能

- 图像标签识别（食物种类）
- 文字识别（OCR）
- 物体检测

### 配额

- 每月免费 1000 次请求（Label Detection）
- 超额后按量计费

### 使用方法

```python
from google.cloud import vision
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/service-account.json'
# 或使用 API Key
client = vision.ImageAnnotatorClient()

with open('/path/to/image.jpg', 'rb') as f:
    content = f.read()

image = vision.Image(content=content)
response = client.label_detection(image=image)
labels = response.label_annotations
```

### 注意事项

- 使用前检查月度配额：`memory/google_vision_usage.json`
- 超过 800 次时切换至 MiniMax

---

## 3. MiniMax M2.7

### 功能

- 多模态图像理解（食物识别）
- 文字生成

### API 端点

```
POST https://api.minimax.chat/v1/text/chatcompletion_v2
```

### 使用方法

```python
import requests
import base64

api_key = os.getenv('MINIMAX_API_KEY')
group_id = os.getenv('MINIMAX_GROUP_ID')

with open('/path/to/image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode()

payload = {
    "model": "abab6.5s-chat",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                {"type": "text", "text": "识别图片中的食物，列出每种食物的名称和估计重量（克）。"}
            ]
        }
    ]
}

response = requests.post(
    f"https://api.minimax.chat/v1/text/chatcompletion_v2?GroupId={group_id}",
    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    json=payload
)
```

---

## 4. USDA FoodData Central API

### 功能

查询食物营养成分（热量、蛋白质、碳水、脂肪等）

### API 端点

```
GET https://api.nal.usda.gov/fdc/v1/foods/search
```

### 参数

| 参数 | 类型 | 说明 |
|-----|-----|-----|
| query | string | 食物名称（建议英文） |
| api_key | string | API Key（DEMO_KEY 或申请的 key） |
| dataType | array | 数据类型（Foundation, SR Legacy, Survey (FNDDS)） |
| pageSize | int | 返回数量（默认 50） |

### 使用方法

```python
import requests

api_key = os.getenv('USDA_API_KEY', 'DEMO_KEY')
response = requests.get(
    'https://api.nal.usda.gov/fdc/v1/foods/search',
    params={
        'query': 'brown rice cooked',
        'api_key': api_key,
        'dataType': ['Foundation', 'SR Legacy'],
        'pageSize': 5
    }
)
data = response.json()
```

### 申请正式 Key

1. 访问 https://fdc.nal.usda.gov/api-guide.html
2. 点击「Get an API Key」
3. 填写表单获取免费 Key（每小时 1000 次）
4. 更新 `~/.openclaw/.env` 中的 `USDA_API_KEY`

---

## 5. Garmin Connect CLI（gccli）

### 安装状态

gccli 已配置，账号信息存于环境变量。

### 常用命令

```bash
# 获取今天的活动数据
gccli activities --date today

# 获取指定日期的活动
gccli activities --date 2024-01-15

# 获取睡眠数据
gccli sleep --date today

# 获取心率数据
gccli heartrate --date today

# 获取步数数据
gccli steps --date today
```

### Python 调用

```python
import subprocess
import json

def get_garmin_data(date_str):
    result = subprocess.run(
        ['gccli', 'activities', '--date', date_str, '--json'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None
```

---

## 6. Skills 调用接口

### ocr-scale（有品秤 OCR）

```bash
python3 ~/.openclaw/workspace-jirou/skills/ocr-scale/ocr_scale.py \
    --image ~/.openclaw/media/inbound/scale_morning.jpg
```

返回 JSON：

```json
{
  "success": true,
  "data": {
    "weight": 65.5,
    "body_fat": 18.2,
    "muscle_rate": 46.3,
    "visceral_fat": 7,
    "bmr": 1589,
    "water": 57.8,
    "protein": 18.5,
    "bone_mass": 2.8,
    "muscle_level": "标准"
  },
  "confidence": 0.92
}
```

### food-recognition（食物识别）

```bash
python3 ~/.openclaw/workspace-jirou/skills/food-recognition/food_recognition.py \
    --image ~/.openclaw/media/inbound/meal.jpg
```

返回 JSON：

```json
{
  "success": true,
  "items": [
    {"name": "米饭", "weight_g": 250, "calories": 290},
    {"name": "清蒸鱼", "weight_g": 200, "calories": 180}
  ],
  "total_calories": 470
}
```

### usda-lookup（USDA 查询）

```bash
python3 ~/.openclaw/workspace-jirou/skills/usda-lookup/usda_lookup.py \
    --food "brown rice" --weight 250
```

返回 JSON：

```json
{
  "success": true,
  "food_name": "Rice, brown, cooked",
  "weight_g": 250,
  "calories": 272,
  "protein_g": 5.5,
  "carbs_g": 56.8,
  "fat_g": 2.2
}
```

---

## 7. OpenClaw message 工具（飞书消息发送）

### 工作原理

飞书消息通过 OpenClaw 内置 `message` 工具发送，使用飞书官方 SDK 长连接（WebSocket）模式，无需在 Agent 代码里管理 WebSocket 连接或配置 Webhook URL。

### 消息发送流程

1. Agent 调用 `notify.js` 中的函数（`sendText` / `sendCard` / `sendReminder` / `sendConfirmation` / `sendError`）
2. `notify.js` 将消息保存到 `memory/pending/msg-<timestamp>-<type>.json`
3. OpenClaw cron 系统检测到 `memory/pending/` 中的消息文件
4. cron 系统通过 `message` 工具（WebSocket 长连接）将消息发送到飞书
5. 发送成功后消息文件被清理

### 消息文件格式

```json
{
  "type": "text",
  "content": "消息内容",
  "timestamp": "2024-01-15T08:00:00.000Z"
}
```

消息类型：
- `text` — 纯文本消息
- `card` — 飞书卡片消息（interactive 格式）
- `reminder` — 提醒消息
- `confirmation` — 操作确认消息
- `error` — 错误通知

### 日报发送流程

1. `scripts/daily-report-generator.py` 生成日报，保存到 `memory/pending/DailyReport-YYYY-MM-DD.md`
2. OpenClaw cron 在次日 07:58 检测到该文件
3. 通过 `message` 工具将日报内容发送到飞书

```bash
python3 ~/.openclaw/workspace-jirou/scripts/daily-report-generator.py \
    --date 2024-01-15
```

输出日报文件：`~/.openclaw/workspace-jirou/memory/reports/2024-01-15.md`
