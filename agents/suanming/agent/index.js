'use strict';

/**
 * index.js - 算命喵 Agent 入口点
 *
 * 职责：
 *   1. 加载环境变量
 *   2. 初始化 agent 环境（目录结构等）
 *   3. 启动消息监听（stdin）
 *   4. 将收到的消息交给 routing.js 处理
 *   5. 处理未捕获异常和 graceful shutdown
 */

const path = require('path');
const fs   = require('fs');

// ---------------------------------------------------------------------------
// 加载环境变量
// ---------------------------------------------------------------------------
(function loadEnv() {
  const envPath = path.join(process.env.HOME || '/root', '.openclaw', '.env');
  if (!fs.existsSync(envPath)) {
    console.warn('[index] 未找到 .env 文件:', envPath);
    return;
  }
  const lines = fs.readFileSync(envPath, 'utf8').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx < 0) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const val = trimmed.slice(eqIdx + 1).trim();
    if (key && !process.env[key]) {
      process.env[key] = val;
    }
  }
  console.info('[index] 环境变量已加载');
})();

// ---------------------------------------------------------------------------
// 导入模块（在 .env 加载后）
// ---------------------------------------------------------------------------
const routing = require('./routing');
const core    = require('./core');
const notify  = require('./notify');

const logger = console;

// ---------------------------------------------------------------------------
// 初始化目录结构
// ---------------------------------------------------------------------------
function initDirectories() {
  const workspacePath = process.env.WORKSPACE_PATH
    || path.join(process.env.HOME || '/root', '.openclaw', 'workspace-suanming');

  const dirs = [
    path.join(workspacePath, 'memory', 'pending'),
    path.join(workspacePath, 'memory', 'reports'),
  ];

  for (const dir of dirs) {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      logger.info(`[index] 创建目录: ${dir}`);
    }
  }
}

// ---------------------------------------------------------------------------
// 消息处理
// ---------------------------------------------------------------------------

/**
 * 处理单条消息
 * @param {object} message - 解析后的消息对象
 */
async function processMessage(message) {
  logger.info('[index] 收到消息:', JSON.stringify(message).slice(0, 200));
  try {
    const result = await routing.route(message, core);
    logger.info('[index] 消息处理完成:', JSON.stringify(result).slice(0, 200));
    return result;
  } catch (err) {
    logger.error('[index] 消息处理异常:', err.message);
    notify.sendError('消息处理', err);
    return { success: false, error: err.message };
  }
}

// ---------------------------------------------------------------------------
// 消息监听：从 stdin 读取消息（JSON per line）
// ---------------------------------------------------------------------------
function startStdinListener() {
  logger.info('[index] 启动 stdin 消息监听...');

  let buffer = '';

  process.stdin.setEncoding('utf8');
  process.stdin.on('data', async (chunk) => {
    buffer += chunk;
    const lines = buffer.split('\n');
    buffer = lines.pop(); // 保留未完整的最后一行

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const message = JSON.parse(trimmed);
        await processMessage(message);
      } catch (err) {
        logger.warn('[index] 无法解析的消息行，跳过:', trimmed.slice(0, 100), err.message);
      }
    }
  });

  process.stdin.on('end', () => {
    // 处理最后一条消息（若有）
    if (buffer.trim()) {
      try {
        const message = JSON.parse(buffer.trim());
        processMessage(message).catch((err) => {
          logger.error('[index] 最后消息处理失败:', err.message);
        });
      } catch (err) {
        logger.warn('[index] 无法解析最后的消息，跳过', err.message);
      }
    }
    logger.info('[index] stdin 关闭');
  });
}

// ---------------------------------------------------------------------------
// Graceful Shutdown
// ---------------------------------------------------------------------------
function setupShutdownHandlers() {
  const shutdown = (signal) => {
    logger.info(`[index] 收到 ${signal}，开始 graceful shutdown...`);
    process.exit(0);
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT',  () => shutdown('SIGINT'));
}

// ---------------------------------------------------------------------------
// 未捕获异常处理
// ---------------------------------------------------------------------------
function setupErrorHandlers() {
  process.on('uncaughtException', (err) => {
    logger.error('[index] 未捕获异常:', err.message, err.stack);
    notify.sendError('未捕获异常', err);
    // 记录错误后继续运行
  });

  process.on('unhandledRejection', (reason) => {
    const err = reason instanceof Error ? reason : new Error(String(reason));
    logger.error('[index] 未处理的 Promise rejection:', err.message);
    notify.sendError('未处理的 Promise rejection', err);
    // 记录错误后继续运行
  });
}

// ---------------------------------------------------------------------------
// 主入口
// ---------------------------------------------------------------------------
async function main() {
  logger.info('[index] 算命喵 Agent 启动中...');

  try {
    initDirectories();
    setupErrorHandlers();
    setupShutdownHandlers();
    startStdinListener();
    logger.info('[index] 算命喵 Agent 已就绪 🔮');
  } catch (err) {
    logger.error('[index] Agent 启动失败:', err.message);
    process.exit(1);
  }
}

main();
