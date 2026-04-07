#!/bin/bash

# 沛柔ID验证脚本
# 确保所有发送给沛柔的消息都使用正确的ID

PEIROU_CORRECT_ID="ou_f9095feb1adeb3f3997725460bcdd87d"
LOG_FILE="/Users/georginalau/.openclaw/workspace-suanmingmiao/logs/id-verification.log"

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

echo "==========================================" >> "$LOG_FILE"
echo "沛柔ID验证检查: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

# 检查运势推送脚本
echo "检查运势推送脚本..." >> "$LOG_FILE"
MORNING_FORTUNE_ID=$(grep -o "ou_[a-f0-9]\{32\}" /Users/georginalau/.openclaw/workspace-suanmingmiao/scripts/morning-fortune.sh | head -1)

if [ "$MORNING_FORTUNE_ID" = "$PEIROU_CORRECT_ID" ]; then
    echo "✅ 运势推送脚本ID正确: $MORNING_FORTUNE_ID" >> "$LOG_FILE"
else
    echo "❌ 运势推送脚本ID错误! 找到: $MORNING_FORTUNE_ID, 应为: $PEIROU_CORRECT_ID" >> "$LOG_FILE"
fi

# 检查其他可能使用ID的脚本
echo "检查其他脚本..." >> "$LOG_FILE"
find /Users/georginalau/.openclaw/workspace-suanmingmiao -name "*.sh" -type f ! -name "verify-peirou-id.sh" -exec grep -l "ou_" {} \; 2>/dev/null | while read script; do
    SCRIPT_ID=$(grep -o "ou_[a-f0-9]\{32\}" "$script" | head -1)
    if [ -n "$SCRIPT_ID" ]; then
        if [ "$SCRIPT_ID" = "$PEIROU_CORRECT_ID" ]; then
            echo "✅ $script: ID正确 ($SCRIPT_ID)" >> "$LOG_FILE"
        else
            echo "⚠️  $script: 发现其他ID ($SCRIPT_ID)" >> "$LOG_FILE"
        fi
    fi
done

# 检查cron任务
echo "检查cron任务..." >> "$LOG_FILE"
crontab -l | grep -q "morning-fortune" && echo "✅ cron任务存在" >> "$LOG_FILE" || echo "❌ cron任务不存在" >> "$LOG_FILE"

echo "验证完成。" >> "$LOG_FILE"
echo "正确的沛柔ID: $PEIROU_CORRECT_ID" >> "$LOG_FILE"
echo "==========================================" >> "$LOG_FILE"

# 输出总结
echo "沛柔ID验证完成: $(date '+%Y-%m-%d %H:%M:%S')"
echo "正确ID: $PEIROU_CORRECT_ID"
echo "日志文件: $LOG_FILE"