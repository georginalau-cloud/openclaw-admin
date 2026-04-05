'use strict';

/**
 * routing.js - 消息路由模块
 *
 * 根据消息类型将入站消息路由到相应的处理逻辑：
 *   - agentTurn (cron 触发)  → core.handleAgentTurn
 *   - feishu (用户消息)      → core.handleFeishuMessage
 *
 * 保留 subagent 接口，未来可扩展 nutrition-analyzer、fitness-planner 等。
 */

const logger = console;

/**
 * 消息类型枚举
 */
const MessageType = {
  AGENT_TURN: 'agentTurn',   // cron 定时触发
  FEISHU: 'feishu',          // 飞书用户消息
  UNKNOWN: 'unknown',
};

/**
 * Subagent 注册表（当前为空，预留扩展接口）
 *
 * 未来可以注册 subagent，例如：
 *   subagents['nutrition-analyzer'] = require('../subagents/nutrition-analyzer');
 *   subagents['fitness-planner']    = require('../subagents/fitness-planner');
 */
const subagents = {};

/**
 * 识别消息类型
 * @param {object} message - 入站消息对象
 * @returns {string}       - MessageType 枚举值
 */
function detectMessageType(message) {
  if (!message || typeof message !== 'object') {
    return MessageType.UNKNOWN;
  }

  // cron 触发的 agentTurn 消息
  if (message.kind === 'agentTurn') {
    return MessageType.AGENT_TURN;
  }

  // 飞书消息（来自 Webhook，通常包含 feishu 字段或 event 字段）
  if (message.kind === 'feishu' || message.feishu || message.event) {
    return MessageType.FEISHU;
  }

  return MessageType.UNKNOWN;
}

/**
 * 从 agentTurn 消息中提取意图
 * @param {object} message - agentTurn 消息
 * @returns {string}       - 意图标识符
 */
function extractAgentTurnIntent(message) {
  const text = (message.message || '').toLowerCase();

  if (text.includes('早安') || text.includes('体重') && text.includes('早')) {
    return 'morning-greeting';
  }
  if (text.includes('早餐')) {
    return 'breakfast-reminder';
  }
  if (text.includes('午餐')) {
    return 'lunch-reminder';
  }
  if (text.includes('晚餐')) {
    return 'dinner-reminder';
  }
  if (text.includes('体重') && text.includes('晚')) {
    return 'evening-weight-reminder';
  }
  if (text.includes('最后') || text.includes('23:00') || text.includes('补录')) {
    return 'final-reminder';
  }
  if (text.includes('garmin') || text.includes('日报') && text.includes('生成')) {
    return 'daily-report-generation';
  }
  if (text.includes('清理') || text.includes('过程文件')) {
    return 'cleanup';
  }

  return 'generic-agent-turn';
}

/**
 * 路由消息到相应的处理函数
 * @param {object} message - 入站消息
 * @param {object} core    - core.js 模块引用（避免循环依赖，运行时传入）
 * @returns {Promise<object>} - 处理结果
 */
async function route(message, core) {
  const type = detectMessageType(message);
  logger.info(`[routing] 消息类型: ${type}`);

  switch (type) {
    case MessageType.AGENT_TURN: {
      const intent = extractAgentTurnIntent(message);
      logger.info(`[routing] agentTurn 意图: ${intent}`);
      return core.handleAgentTurn(intent, message);
    }

    case MessageType.FEISHU: {
      logger.info('[routing] 路由到飞书消息处理');
      return core.handleFeishuMessage(message);
    }

    case MessageType.UNKNOWN:
    default: {
      logger.warn('[routing] 未知消息类型，忽略:', JSON.stringify(message).slice(0, 200));
      return { success: false, reason: 'unknown-message-type' };
    }
  }
}

/**
 * 注册 subagent（预留接口，当前未使用）
 * @param {string}   name    - subagent 名称
 * @param {object}   handler - subagent 处理模块
 */
function registerSubagent(name, handler) {
  subagents[name] = handler;
  logger.info(`[routing] Subagent 已注册: ${name}`);
}

module.exports = { route, registerSubagent, detectMessageType, extractAgentTurnIntent, MessageType };
