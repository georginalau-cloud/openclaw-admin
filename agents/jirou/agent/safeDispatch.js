'use strict';

/**
 * safeDispatch.js - 安全调度工具模块
 *
 * 提供带错误处理的异步函数执行包装，确保任何调度操作
 * 的失败不会导致整个 Agent 崩溃。
 */

const logger = console;

/**
 * 安全执行异步函数，捕获所有异常并记录日志
 * @param {string}   label   - 操作名称（用于日志）
 * @param {Function} fn      - 要执行的异步函数
 * @param {*}        fallback - 失败时的返回值（默认 null）
 * @returns {Promise<*>}     - 执行结果或 fallback
 */
async function safeRun(label, fn, fallback = null) {
  try {
    return await fn();
  } catch (err) {
    logger.error(`[safeDispatch] ${label} 执行失败:`, err.message);
    return fallback;
  }
}

/**
 * 安全执行并返回标准结果对象
 * @param {string}   label - 操作名称
 * @param {Function} fn    - 要执行的异步函数
 * @returns {Promise<{success: boolean, result?: *, error?: string}>}
 */
async function dispatch(label, fn) {
  try {
    const result = await fn();
    return { success: true, result };
  } catch (err) {
    logger.error(`[safeDispatch] dispatch(${label}) 失败:`, err.message);
    return { success: false, error: err.message };
  }
}

/**
 * 批量安全执行多个操作（并行）
 * @param {Array<{label: string, fn: Function}>} tasks
 * @returns {Promise<Array<*>>}
 */
async function dispatchAll(tasks) {
  return Promise.all(
    tasks.map(({ label, fn }) => safeRun(label, fn))
  );
}

module.exports = { safeRun, dispatch, dispatchAll };
