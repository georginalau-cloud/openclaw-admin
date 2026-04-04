'use strict';

/**
 * notify.js - 算命喵飞书消息发送模块
 *
 * 负责向飞书发送运势推送和分析结果。
 * 所有发送均为异步，错误被吞掉，不影响主流程。
 */

const https = require('https');
const http  = require('http');
const url   = require('url');

const logger = console;

/**
 * 发送飞书消息（底层实现）
 * @param {string} webhookUrl - 飞书 Webhook URL
 * @param {object} payload    - 消息 payload
 * @returns {Promise<void>}
 */
function _sendRaw(webhookUrl, payload) {
  return new Promise((resolve, reject) => {
    const parsed = url.parse(webhookUrl);
    const body   = JSON.stringify(payload);
    const options = {
      hostname: parsed.hostname,
      port: parsed.port || (parsed.protocol === 'https:' ? 443 : 80),
      path: parsed.path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const lib = parsed.protocol === 'https:' ? https : http;
    const req = lib.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
        } else {
          reject(new Error(`飞书 Webhook 返回 ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

/**
 * 发送纯文本消息到飞书
 * @param {string} text - 消息文本
 */
async function sendText(text) {
  const webhookUrl = process.env.FEISHU_WEBHOOK_URL;
  if (!webhookUrl) {
    logger.warn('[notify] FEISHU_WEBHOOK_URL 未配置，跳过发送');
    return;
  }

  const payload = {
    msg_type: 'text',
    content: { text },
  };

  try {
    await _sendRaw(webhookUrl, payload);
    logger.info('[notify] 飞书文本消息发送成功');
  } catch (err) {
    logger.error('[notify] 飞书文本消息发送失败:', err.message);
  }
}

/**
 * 发送飞书卡片消息
 * @param {object} card - 卡片内容（interactive 格式）
 */
async function sendCard(card) {
  const webhookUrl = process.env.FEISHU_WEBHOOK_URL;
  if (!webhookUrl) {
    logger.warn('[notify] FEISHU_WEBHOOK_URL 未配置，跳过发送');
    return;
  }

  const payload = {
    msg_type: 'interactive',
    card,
  };

  try {
    await _sendRaw(webhookUrl, payload);
    logger.info('[notify] 飞书卡片消息发送成功');
  } catch (err) {
    logger.error('[notify] 飞书卡片消息发送失败:', err.message);
  }
}

/**
 * 发送每日运势消息（使用 message tool）
 * @param {object} fortune_data - 运势数据（含 date, raw_output, huangli 等）
 */
function sendFortune(fortune_data) {
  const date   = fortune_data && fortune_data.date   ? fortune_data.date   : '今日';
  const output = fortune_data && fortune_data.raw_output ? fortune_data.raw_output : '运势分析暂无内容';

  const text = `🔮 ${date} 每日运势\n\n${output}\n\n——算命喵掐指推算 🐾`;
  sendText(text).catch(() => {});
}

/**
 * 发送分析结果消息
 * @param {string} analysis_result - 分析结果文本
 */
function sendAnalysis(analysis_result) {
  sendText(analysis_result).catch(() => {});
}

/**
 * 发送确认消息（询问用户意图等）
 * @param {string} message - 确认文本
 */
function sendConfirmation(message) {
  sendText(message).catch(() => {});
}

/**
 * 发送错误通知
 * @param {string} context - 错误发生的上下文
 * @param {Error}  err     - 错误对象
 */
function sendError(context, err) {
  const text = `⚠️ 算命喵遇到了一个问题\n\n上下文：${context}\n错误：${err && err.message ? err.message : String(err)}`;
  sendText(text).catch(() => {});
}

module.exports = { sendText, sendCard, sendFortune, sendAnalysis, sendConfirmation, sendError };
