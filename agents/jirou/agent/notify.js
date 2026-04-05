'use strict';

/**
 * notify.js - 飞书消息发送模块
 *
 * 负责将消息写入 memory/pending/ 目录，由 OpenClaw cron 系统通过 WebSocket 发送。
 * 所有发送均为同步写文件，错误被吞掉，不影响主流程。
 */

const fs     = require('fs');
const path   = require('path');
const crypto = require('crypto');

const logger = console;

// 工作空间路径
const WORKSPACE_PATH = process.env.WORKSPACE_PATH
  || path.join(process.env.HOME || '/root', '.openclaw', 'workspace-jirou');

const PENDING_DIR = path.join(WORKSPACE_PATH, 'memory', 'pending');

// 确保 pending 目录存在（模块加载时初始化一次）
try {
  fs.mkdirSync(PENDING_DIR, { recursive: true });
} catch (err) {
  console.error('[notify] 无法创建 pending 目录:', err.message);
}

/**
 * 生成消息文件名
 * @param {string} type - 消息类型
 * @returns {string}
 */
function _genFilename(type) {
  const ts  = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const rnd = crypto.randomBytes(3).toString('hex');
  return `msg-${ts}-${rnd}-${type}.json`;
}

/**
 * 将消息写入 memory/pending/ 目录
 * @param {string} type    - 消息类型 (text|card|reminder|confirmation|error)
 * @param {*}      content - 消息内容
 */
function _saveMessage(type, content) {
  try {
    const filename = _genFilename(type);
    const payload  = { type, content, timestamp: new Date().toISOString() };
    fs.writeFileSync(path.join(PENDING_DIR, filename), JSON.stringify(payload, null, 2), 'utf8');
    logger.info(`[notify] 消息已写入: ${filename}`);
  } catch (err) {
    logger.error('[notify] 写入消息失败:', err.message);
  }
}

/**
 * 发送纯文本消息到飞书
 * @param {string} text - 消息文本
 */
function sendText(text) {
  _saveMessage('text', text);
}

/**
 * 发送飞书卡片消息
 * @param {object} card - 卡片内容（interactive 格式）
 */
function sendCard(card) {
  _saveMessage('card', card);
}

/**
 * 发送用户提醒消息（文本）
 * @param {string} message - 提醒文本
 */
function sendReminder(message) {
  _saveMessage('reminder', message);
}

/**
 * 发送操作确认消息（文本）
 * @param {string} message - 确认文本
 */
function sendConfirmation(message) {
  _saveMessage('confirmation', message);
}

/**
 * 发送错误通知
 * @param {string} context - 错误发生的上下文
 * @param {Error}  err     - 错误对象
 */
function sendError(context, err) {
  const text = `⚠️ 肌肉喵遇到了一个问题\n\n上下文：${context}\n错误：${err && err.message ? err.message : String(err)}`;
  _saveMessage('error', text);
}

module.exports = { sendText, sendCard, sendReminder, sendConfirmation, sendError };
