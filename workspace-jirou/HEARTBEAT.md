# 💓 肌肉 Agent - HEARTBEAT.md

## 每日检查清单

---

## ☀️ 早上检查（08:05）

- [ ] 早晨体重提醒已发送
- [ ] `memory/pending/YYYY-MM-DD-morning-scale.json` 是否存在
- [ ] 如存在：OCR 识别结果是否合理（字段完整性 ≥ 50%）

---

## 🍳 早餐检查（10:05 / 10:35）

- [ ] 10:00 早餐提醒已发送
- [ ] `memory/pending/YYYY-MM-DD-breakfast.json` 是否存在
- [ ] 如未存在：10:30 二次提醒已发送
- [ ] 二次提醒后数据是否更新

---

## 🍱 午餐检查（12:35 / 13:05）

- [ ] 12:30 午餐提醒已发送
- [ ] `memory/pending/YYYY-MM-DD-lunch.json` 是否存在
- [ ] 如未存在：13:00 二次提醒已发送
- [ ] 二次提醒后数据是否更新

---

## 🍜 晚餐检查（19:35 / 20:05）

- [ ] 19:30 晚餐提醒已发送
- [ ] `memory/pending/YYYY-MM-DD-dinner.json` 是否存在
- [ ] 如未存在：20:00 二次提醒已发送
- [ ] 二次提醒后数据是否更新

---

## 🌙 晚间检查（22:05）

- [ ] 晚上体重提醒已发送
- [ ] `memory/pending/YYYY-MM-DD-evening-scale.json` 是否存在
- [ ] 如存在：OCR 识别结果是否合理

---

## 🔔 最后提醒检查（23:05）

- [ ] 23:00 最后提醒逻辑执行完毕
- [ ] 缺失数据列表已发送给用户

---

## 📊 日报生成检查（00:05 次日）

- [ ] `scripts/daily-report-generator.py` 执行完毕
- [ ] `memory/pending/DailyReport-YYYY-MM-DD.md` 文件已生成
- [ ] 日报包含所有可用数据
- [ ] 热量差计算正确

---

## 📨 日报发送检查（08:00 次日）

- [ ] `memory/pending/DailyReport-YYYY-MM-DD.md` 文件存在
- [ ] OpenClaw cron 已通过 `message` 工具将日报发送至飞书
- [ ] 飞书消息内容格式正确

---

## 🧹 清理检查（08:15）

- [ ] 前一天的所有 `memory/pending/` 文件已删除
- [ ] 只保留当天新生成的文件
- [ ] 报告清理结果

---

## 🔧 系统健康检查（每日）

### API 状态

| 服务 | 状态检查命令 | 预期结果 |
|-----|-----------|---------|
| Google Vision API | 检查 `.env` 中 `GOOGLE_VISION_API_KEY` | 非空 |
| MiniMax API | 检查 `.env` 中 `MINIMAX_API_KEY` | 非空 |
| USDA API | 检查 `.env` 中 `USDA_API_KEY` | 非空 |
| Garmin CLI | `gccli --version` | 版本号输出 |
| EasyOCR | Python `import easyocr` | 无报错 |

### 存储路径检查

```bash
# 检查目录结构
ls ~/.openclaw/workspace-jirou/memory/pending/
ls ~/.openclaw/workspace-jirou/memory/reports/
ls ~/.openclaw/media/inbound/
```

### 数据一致性检查

- 今天的 pending 数据文件格式是否为有效 JSON
- 日报是否引用了正确日期的数据

---

## ⚠️ 常见问题排查

### OCR 识别失败

**症状**：`ocr_scale.py` 返回空结果或报错

**排查步骤**：
1. 检查图片文件是否存在于 `~/.openclaw/media/inbound/`
2. 检查 EasyOCR 是否正常安装：`python3 -c "import easyocr; print('OK')"`
3. 检查图片格式是否支持（JPG/PNG/WEBP）
4. 手动测试：`python3 skills/ocr-scale/ocr_scale.py --image /path/to/image`

### USDA 查询无结果

**症状**：`usda_lookup.py` 返回空列表

**排查步骤**：
1. 检查网络连接
2. 检查 `USDA_API_KEY` 是否有效
3. 尝试英文食物名称
4. 降级使用内置热量参考表

### Garmin 数据获取失败

**症状**：`gccli` 命令报错或返回空数据

**排查步骤**：
1. 检查 Garmin 账号是否登录：`gccli profile`
2. 检查网络连接（需访问 Garmin Connect）
3. 尝试手动获取：`gccli activities --date YYYY-MM-DD`
4. 日报中 Garmin 数据留空，记录错误

### 飞书消息发送失败

**症状**：日报无法发送至飞书

**排查步骤**：
1. 检查 `memory/pending/DailyReport-YYYY-MM-DD.md` 是否存在
2. 确认 OpenClaw cron 系统的 `message` 工具配置是否正常
3. 检查 OpenClaw 日志中是否有发送错误记录

---

## 📈 监控指标

| 指标 | 目标值 | 警告阈值 |
|-----|-------|---------|
| OCR 识别成功率 | > 90% | < 70% |
| 三餐数据完整率 | > 80% | < 50% |
| 日报生成成功率 | > 95% | < 80% |
| USDA 查询响应时间 | < 3s | > 10s |
| 日报发送成功率 | > 99% | < 90% |

---

## 🗓️ 每周维护任务

- [ ] 清理 7 天前的 `memory/pending/` 文件
- [ ] 检查 Google Vision API 月度使用量（≤ 1000 次）
- [ ] 更新 MEMORY.md 中的周平均数据
- [ ] 备份 `memory/reports/` 目录
