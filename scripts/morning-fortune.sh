#!/bin/bash

# 算命喵 - 每日运势推送
# 沛柔八字: 己巳 丁丑 癸酉 己未
# 喜金水，忌土火

cd /Users/georginalau/.openclaw/workspace-suanmingmiao

LOG_FILE="/Users/georginalau/.openclaw/workspace-suanmingmiao/logs/morning-fortune.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

echo "==========================================" >> "$LOG_FILE"
echo "开始执行每日运势推送: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# 获取今日干支信息
TODAY_INFO=$(curl -s "https://www.188188.org/" | grep -o '今日八字[^<]*' | head -1 || echo "无法获取今日干支")

# 构建消息内容
MESSAGE="🐱🔮 算命喵每日运势推送

📅 今天是: $(date '+%Y年%m月%d日 %A')
$TODAY_INFO

📊 你的八字: 己巳 丁丑 癸酉 己未
✨ 喜用神: 金、水
🚫 忌神: 土、火

请根据以上信息，结合今日干支，为我分析今日运势，包括：
1. 今日干支与我的八字互动
2. 五行生克关系
3. 今日宜忌事项
4. 穿衣颜色建议
5. 健康注意事项
6. 一句话总结

请用清晰简洁的格式呈现，谢谢！"

echo "发送消息到飞书..." >> "$LOG_FILE"

# 使用openclaw agent命令发送消息（这会触发算命喵分析）
openclaw agent --agent suanming --channel feishu --message "$MESSAGE" --deliver --reply-account suanming --reply-to ou_f9095feb1adeb3f3997725460bcdd87d >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "每日运势已成功发送: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
    echo "成功: 每日运势已发送" >&2
else
    echo "错误: 发送失败，退出码: $EXIT_CODE" >> "$LOG_FILE"
    echo "尝试使用备用方法..." >> "$LOG_FILE"
    
    # 备用方法：直接发送简单消息
    openclaw message send --channel feishu --account suanming --target "ou_f9095feb1adeb3f3997725460bcdd87d" --message "🐱 早安！今天是$(date '+%Y年%m月%d日')，算命喵正在为你分析今日运势，请稍候..." >> "$LOG_FILE" 2>&1
    
    if [ $? -eq 0 ]; then
        echo "备用消息发送成功" >> "$LOG_FILE"
    else
        echo "备用消息也发送失败" >> "$LOG_FILE"
    fi
fi

echo "执行结束: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"
