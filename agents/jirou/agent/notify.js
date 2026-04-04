'use strict';

/**
 * notify.js - 飞书消息发送模块
 *
 * 将消息保存到 memory/pending/ 目录，
 * 由 OpenClaw cron 系统通过内置 message 工具（WebSocket 长连接）自动发送到飞书。
 * Agent 代码无需管理 WebSocket 连接或 Webhook URL。
 */

const fs = require('fs');
const path = require('path');

const logger = console;

const WORKSPACE_PATH = process.env.WORKSPACE_PATH
  || path.join(process.env.HOME || '/root', '.openclaw', 'workspace-jirou');

const PENDING_DIR = path.join(WORKSPACE_PATH, 'memory', 'pending');

/**
 * 保存消息到 memory/pending/ 目录
 * OpenClaw cron 系统会检测该目录并通过 message 工具发送到飞书
 * @param {string} type    - 消息类型：text | card | reminder | confirmation | error
 * @param {*}      content - 消息内容
 */
function _savePendingMessage(type, content) {
  try {
    if (!fs.existsSync(PENDING_DIR)) {
      fs.mkdirSync(PENDING_DIR, { recursive: true });
    }
    const timestamp = new Date().toISOString();
    const safe = timestamp.replace(/[:.]/g, '-');
    const filename = `msg-${safe}-${type}.json`;
    const filePath = path.join(PENDING_DIR, filename);
    const payload = { type, content, timestamp };
    fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), 'utf8');
    logger.info(`[notify] 消息已保存: ${filePath}`);
  } catch (err) {
    logger.error('[notify] 保存消息失败:', err.message);
  }
}

/**
 * 发送纯文本消息到飞书
 * @param {string} text - 消息文本
 */
async function sendText(text) {
  _savePendingMessage('text', text);
}

/**
 * 发送飞书卡片消息
 * @param {object} card - 卡片内容（interactive 格式）
 */
async function sendCard(card) {
  _savePendingMessage('card', card);
}

/**
 * 发送用户提醒消息（文本）
 * @param {string} message - 提醒文本
 */
function sendReminder(message) {
  _savePendingMessage('reminder', message);
}

/**
 * 发送操作确认消息（文本）
 * @param {string} message - 确认文本
 */
function sendConfirmation(message) {
  _savePendingMessage('confirmation', message);
}

/**
 * 发送错误通知
 * @param {string} context - 错误发生的上下文
 * @param {Error}  err     - 错误对象
 */
function sendError(context, err) {
  const content = `⚠️ 肌肉喵遇到了一个问题\n\n上下文：${context}\n错误：${err && err.message ? err.message : String(err)}`;
  _savePendingMessage('error', content);
}

module.exports = { sendText, sendCard, sendReminder, sendConfirmation, sendError };
