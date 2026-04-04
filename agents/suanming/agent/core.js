'use strict';

/**
 * core.js - 算命喵核心消息处理模块
 *
 * 职责：
 *   1. 接收来自 routing.js 的路由消息
 *   2. 处理 Cron 触发（daily-fortune）和飞书消息（fortune-query / image-analysis / video-analysis）
 *   3. 调用 morning-fortune.sh 执行每日运势分析
 *   4. 通过 fetch-huangli.py 获取当日黄历干支（188188.org）
 *   5. 从 USER.md 读取用户八字
 *   6. 将分析结果保存到 memory/pending/YYYY-MM-DD-fortune.json
 *   7. 通过 notify.js 发送飞书消息
 */

const fs   = require('fs');
const path = require('path');
const { execFile, spawn } = require('child_process');

const notify = require('./notify');

const logger = console;

// 工作空间路径
const WORKSPACE_PATH = process.env.WORKSPACE_PATH
  || path.join(process.env.HOME || '/root', '.openclaw', 'workspace-suanming');

const PENDING_DIR  = path.join(WORKSPACE_PATH, 'memory', 'pending');
const REPORTS_DIR  = path.join(WORKSPACE_PATH, 'memory', 'reports');
const SCRIPTS_DIR  = path.join(WORKSPACE_PATH, 'scripts');
const SKILLS_DIR   = path.join(WORKSPACE_PATH, 'skills');

// ---------------------------------------------------------------------------
// 日期工具
// ---------------------------------------------------------------------------

function todayStr() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD
}

// ---------------------------------------------------------------------------
// 持久化工具
// ---------------------------------------------------------------------------

/**
 * 将数据保存到 memory/pending/ 目录
 * @param {string} filename - 不含目录的文件名，例如 "2024-01-15-fortune.json"
 * @param {object} data
 */
function savePending(filename, data) {
  try {
    if (!fs.existsSync(PENDING_DIR)) {
      fs.mkdirSync(PENDING_DIR, { recursive: true });
    }
    const filePath = path.join(PENDING_DIR, filename);
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf8');
    logger.info(`[core] 已保存: ${filePath}`);
  } catch (err) {
    logger.error('[core] 保存数据失败:', err.message);
    throw err;
  }
}

/**
 * 检查 pending 文件是否存在
 * @param {string} filename
 */
function pendingExists(filename) {
  return fs.existsSync(path.join(PENDING_DIR, filename));
}

// ---------------------------------------------------------------------------
// 用户信息读取
// ---------------------------------------------------------------------------

/**
 * 从 USER.md 读取用户八字等基本信息
 * @returns {string} USER.md 内容，读取失败返回空字符串
 */
function readUserInfo() {
  const userMdPath = path.join(WORKSPACE_PATH, 'USER.md');
  try {
    if (fs.existsSync(userMdPath)) {
      return fs.readFileSync(userMdPath, 'utf8');
    }
    logger.warn('[core] USER.md 未找到:', userMdPath);
    return '';
  } catch (err) {
    logger.error('[core] 读取 USER.md 失败:', err.message);
    return '';
  }
}

// ---------------------------------------------------------------------------
// 脚本调用
// ---------------------------------------------------------------------------

/**
 * 执行 Shell 脚本
 * @param {string}   scriptPath - 脚本路径
 * @param {string[]} args       - 命令行参数
 * @param {object}   env        - 附加环境变量（可选）
 * @returns {Promise<{success: boolean, stdout: string, stderr: string}>}
 */
function runShellScript(scriptPath, args = [], env = {}) {
  return new Promise((resolve) => {
    execFile('bash', [scriptPath, ...args], {
      timeout: 120000,
      env: { ...process.env, ...env },
    }, (err, stdout, stderr) => {
      if (err) {
        logger.error(`[core] 脚本执行失败 (${scriptPath}):`, err.message);
        if (stderr) logger.error('[core] stderr:', stderr.slice(0, 500));
        resolve({ success: false, error: err.message, stdout, stderr });
        return;
      }
      resolve({ success: true, stdout, stderr });
    });
  });
}

/**
 * 执行 Python 脚本
 * @param {string}   scriptPath - 脚本路径
 * @param {string[]} args       - 命令行参数
 * @returns {Promise<object>}
 */
function runPythonScript(scriptPath, args = []) {
  return new Promise((resolve) => {
    execFile('python3', [scriptPath, ...args], { timeout: 60000 }, (err, stdout, stderr) => {
      if (err) {
        logger.error(`[core] Python 脚本执行失败 (${scriptPath}):`, err.message);
        if (stderr) logger.error('[core] stderr:', stderr.slice(0, 500));
        resolve({ success: false, error: err.message });
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (parseErr) {
        // 脚本可能输出非 JSON，尝试提取最后一个 JSON 块
        logger.warn(`[core] 脚本输出非 JSON (${scriptPath}):`, parseErr.message);
        const match = stdout.match(/\{[\s\S]*\}(?=[^}]*$)/);
        if (match) {
          try { resolve(JSON.parse(match[0])); return; } catch { /* ignore */ }
        }
        resolve({ success: true, raw: stdout.trim() });
      }
    });
  });
}

/**
 * 获取当日黄历干支数据（从 188188.org）
 * @param {string} dateStr - YYYY-MM-DD
 * @returns {Promise<object>} 黄历数据
 */
async function fetchHuangli(dateStr) {
  const scriptPath = path.join(SCRIPTS_DIR, 'fetch-huangli.py');
  if (!fs.existsSync(scriptPath)) {
    logger.warn('[core] fetch-huangli.py 未找到，跳过黄历抓取');
    return { success: false, reason: 'script-not-found' };
  }
  return runPythonScript(scriptPath, ['--date', dateStr]);
}

// ---------------------------------------------------------------------------
// 消息处理逻辑
// ---------------------------------------------------------------------------

/**
 * 处理 cron 触发的 agentTurn 消息
 * @param {string} intent  - routing.js 提取的意图
 * @param {object} message - 原始消息
 */
async function handleAgentTurn(intent, message) {
  logger.info(`[core] 处理 agentTurn: ${intent}`);

  switch (intent) {
    case 'daily-fortune':
      return _runDailyFortune();

    case 'fortune-query':
      return _runFortuneQuery(message.content || message.message || '');

    case 'bazi-analysis':
      return _runBaziAnalysis(message.content || message.message || '');

    case 'image-analysis':
      return _runImageAnalysis(null);

    case 'video-analysis':
      return _runVideoAnalysis(message.content || message.message || '');

    default: {
      logger.info('[core] 通用 agentTurn，忽略');
      return { success: true, action: 'generic-agent-turn-ignored' };
    }
  }
}

/**
 * 处理来自飞书的用户消息
 * @param {object} message - 飞书消息（含 event 或 feishu 字段）
 */
async function handleFeishuMessage(message) {
  logger.info('[core] 处理飞书用户消息');

  // 提取消息内容
  const event   = message.event || message;
  const msgObj  = event.message || {};
  const msgType = msgObj.message_type || msgObj.msg_type || 'text';

  let text      = '';
  let imagePath = null;

  if (msgType === 'text') {
    try {
      const content = JSON.parse(msgObj.content || '{}');
      text = content.text || '';
    } catch {
      text = msgObj.content || '';
    }
  } else if (msgType === 'image') {
    // 图片消息：路径由 inbound 目录管理
    const inboundDir = process.env.MEDIA_INBOUND_PATH
      || path.join(process.env.HOME || '/root', '.openclaw', 'media', 'inbound');
    imagePath = path.join(inboundDir, 'latest.jpg');
  } else if (msgType === 'media') {
    // 视频/文件消息
    const fileKey = msgObj.file_key || '';
    return _runVideoAnalysis(text || fileKey);
  }

  // 通过关键字识别意图
  const lower = text.toLowerCase();
  let intent  = 'other';

  if (imagePath || lower.includes('图片') || lower.includes('古籍') || lower.includes('命理') || lower.includes('看看这个')) {
    intent = 'image-analysis';
  } else if (lower.includes('http') || lower.includes('bilibili') || lower.includes('youtube') || lower.includes('视频')) {
    intent = 'video-analysis';
  } else if ((lower.includes('精批') || lower.includes('八字精批') || lower.includes('详细分析') || lower.includes('详批')) &&
             _hasBirthDate(text)) {
    intent = 'bazi-analysis';
  } else if (lower.includes('运气') || lower.includes('运势') || lower.includes('今天') || lower.includes('八字') || lower.includes('流年') || lower.includes('掐指')) {
    intent = 'fortune-query';
  }

  logger.info(`[core] 飞书消息意图: ${intent}`);

  switch (intent) {
    case 'fortune-query':
      return _runFortuneQuery(text);

    case 'bazi-analysis':
      return _runBaziAnalysis(text);

    case 'image-analysis':
      return _runImageAnalysis(imagePath);

    case 'video-analysis':
      return _runVideoAnalysis(text);

    default: {
      // 通用回复
      notify.sendText('本喵掐指一算...请问您想了解运势、分析古籍，还是解读视频？🔮');
      return { success: true, action: 'generic-feishu-reply' };
    }
  }
}

// ---------------------------------------------------------------------------
// 内部处理逻辑
// ---------------------------------------------------------------------------

/**
 * 执行每日运势推送（Cron 早 8 点触发）
 */
async function _runDailyFortune() {
  const today = todayStr();
  logger.info(`[core] 开始生成每日运势: ${today}`);

  const fortuneFile = `${today}-fortune.json`;

  // 1. 获取当日黄历干支
  let huangli = {};
  try {
    const huangliResult = await fetchHuangli(today);
    if (huangliResult && huangliResult.success !== false) {
      huangli = huangliResult;
      // 缓存黄历数据
      savePending(`huangli-${today}.json`, { date: today, ...huangli });
      logger.info('[core] 黄历数据获取成功');
    } else {
      logger.warn('[core] 黄历数据获取失败，使用空数据继续');
    }
  } catch (err) {
    logger.error('[core] 获取黄历数据异常:', err.message);
    notify.sendError('获取黄历数据', err);
  }

  // 2. 读取用户八字
  const userInfo = readUserInfo();
  if (!userInfo) {
    logger.warn('[core] 未能读取用户信息（USER.md），运势分析可能不完整');
  }

  // 3. 执行 morning-fortune.sh 生成运势分析
  const scriptPath = path.join(SCRIPTS_DIR, 'morning-fortune.sh');
  let fortuneResult = null;
  try {
    const scriptResult = await runShellScript(scriptPath, [], {
      HUANGLI_DATA: JSON.stringify(huangli),
      USER_INFO: userInfo,
      FORTUNE_DATE: today,
    });

    if (scriptResult.success) {
      fortuneResult = {
        date: today,
        huangli,
        raw_output: scriptResult.stdout,
        generated_at: new Date().toISOString(),
      };
      logger.info('[core] morning-fortune.sh 执行成功');
    } else {
      logger.error('[core] morning-fortune.sh 执行失败:', scriptResult.error);
      notify.sendError('morning-fortune.sh', new Error(scriptResult.error || '脚本执行失败'));
    }
  } catch (err) {
    logger.error('[core] 执行 morning-fortune.sh 异常:', err.message);
    notify.sendError('morning-fortune.sh', err);
  }

  // 4. 保存运势结果到 pending
  if (fortuneResult) {
    try {
      savePending(fortuneFile, fortuneResult);
    } catch (err) {
      logger.error('[core] 保存运势数据失败:', err.message);
      notify.sendError('保存运势数据', err);
    }

    // 5. 发送运势到飞书
    notify.sendFortune(fortuneResult);
    return { success: true, action: 'daily-fortune-sent', date: today };
  }

  // 脚本失败时发送降级提示
  notify.sendText(`🔮 ${today} 今日运势分析暂时无法生成，请稍后再试。`);
  return { success: false, action: 'daily-fortune-failed', date: today };
}

/**
 * 处理用户运势查询（飞书消息或 agentTurn）
 * 结合流年流月流日与原局作用进行分析
 * @param {string} text - 用户消息文本
 */
async function _runFortuneQuery(text) {
  const today    = todayStr();
  const userInfo = readUserInfo();

  // 检查今天是否已有运势缓存
  const fortuneFile = `${today}-fortune.json`;
  let cachedFortune = null;
  if (pendingExists(fortuneFile)) {
    try {
      cachedFortune = JSON.parse(
        fs.readFileSync(path.join(PENDING_DIR, fortuneFile), 'utf8')
      );
    } catch (err) {
      logger.warn('[core] 读取运势缓存失败:', err.message);
    }
    notify.sendAnalysis(
      `🔮 本喵掐指一算...\n\n` +
      `根据今日（${today}）运势分析：\n\n` +
      `${cachedFortune.raw_output}\n\n` +
      `（基于流年流月流日与原局交互分析）`
    );
    return { success: true, action: 'fortune-query-from-cache', date: today };
  }

  // TODO: 寻找现成的子平法 skill，或开发 daily-huangli-analyzer
  // 目前回退到调用 morning-fortune.sh 补充生成
  logger.info('[core] 运势缓存未找到，尝试实时生成');

  let huangli = {};
  try {
    const hr = await fetchHuangli(today);
    if (hr && hr.success !== false) huangli = hr;
  } catch { /* ignore */ }

  const scriptPath = path.join(SCRIPTS_DIR, 'morning-fortune.sh');
  let output = '';
  try {
    const result = await runShellScript(scriptPath, [], {
      HUANGLI_DATA: JSON.stringify(huangli),
      USER_INFO: userInfo,
      FORTUNE_DATE: today,
    });
    output = result.stdout || '';
  } catch (err) {
    logger.error('[core] 运势查询脚本失败:', err.message);
    notify.sendError('运势查询', err);
  }

  if (output) {
    notify.sendAnalysis(
      `🔮 本喵掐指一算...\n\n` +
      `${output}\n\n` +
      `（基于子平法，结合流年流月流日与原局交互分析）`
    );
    // 缓存结果
    savePending(fortuneFile, {
      date: today,
      huangli,
      raw_output: output,
      generated_at: new Date().toISOString(),
    });
  } else {
    notify.sendText('🔮 本喵今日运势推算遇到障碍，请稍后再试或明日见 🙏');
  }

  return { success: !!output, action: 'fortune-query-processed', date: today };
}

/**
 * 处理图片分析（古籍、命理图等）
 * @param {string|null} imagePath - 图片路径
 */
async function _runImageAnalysis(imagePath) {
  // 询问用户是否需要分析/解读
  notify.sendConfirmation(
    '🔮 收到图片！\n\n本喵看到您发来了一张图片，请问您是需要：\n\n' +
    '1️⃣ 分析命理内容（八字、紫薇斗数等）\n' +
    '2️⃣ 解读古籍内容（典籍、批注等）\n' +
    '3️⃣ 其他解读需求\n\n' +
    '请回复序号或说明您的需求 😊'
  );
  return { success: true, action: 'image-analysis-confirmation-sent', imagePath };
}

/**
 * 检查文本中是否含有出生日期信息
 * 匹配格式：4位年份 + 月/日数字（如"1990年1月15日"、"1990/01/15"、"1990-01-15"）
 * @param {string} text
 * @returns {boolean}
 */
function _hasBirthDate(text) {
  // 匹配 "1990年1月15日" / "1990/01/15" / "1990-01-15" 等（均要求4位年份）
  const patterns = [
    /\d{4}[年\/\-\.]\d{1,2}[月\/\-\.]\d{1,2}/,
    /\d{4}年\d{1,2}月\d{1,2}日/,
  ];
  return patterns.some(p => p.test(text));
}

/**
 * 从文本中提取出生参数
 * @param {string} text - 用户消息文本
 * @returns {{ year, month, day, hour, gender } | null}
 */
function _extractBirthParams(text) {
  // 尝试匹配 YYYY年M月D日 H时
  const fullMatch = text.match(/(\d{4})[年\/\-\.](\d{1,2})[月\/\-\.](\d{1,2})[日号]?\s*(?:(\d{1,2})[时点:：])?/);
  if (!fullMatch) return null;

  const year  = parseInt(fullMatch[1], 10);
  const month = parseInt(fullMatch[2], 10);
  const day   = parseInt(fullMatch[3], 10);
  const hour  = fullMatch[4] ? parseInt(fullMatch[4], 10) : 0;

  // 尝试识别性别关键词
  let gender = 'unknown';
  if (/男命|男性|先生|男/.test(text)) gender = 'male';
  else if (/女命|女性|女士|女/.test(text)) gender = 'female';

  return { year, month, day, hour, gender };
}

/**
 * 执行八字精批分析，调用 suanming-bazi-analyzer skill
 * @param {string} text - 用户消息文本（含出生日期）
 */
async function _runBaziAnalysis(text) {
  const params = _extractBirthParams(text);

  if (!params) {
    notify.sendText(
      '🔮 本喵需要您的出生日期才能进行八字精批！\n\n' +
      '请提供格式如：\n' +
      '「1990年1月15日 8时 男命，帮我精批八字」'
    );
    return { success: false, action: 'bazi-analysis-missing-params' };
  }

  const { year, month, day, hour, gender } = params;
  logger.info(`[core] 八字精批: ${year}年${month}月${day}日${hour}时 ${gender}`);

  notify.sendText('🔮 正在为您起盘精批，稍候片刻...');

  const scriptPath = path.join(SKILLS_DIR, 'suanming-bazi-analyzer', 'bazi_analyzer.py');

  if (!fs.existsSync(scriptPath)) {
    logger.error('[core] 八字精批 skill 未找到:', scriptPath);
    notify.sendText('🔮 八字精批 skill 暂未就绪，请联系管理员配置 🙏');
    return { success: false, action: 'bazi-skill-not-found' };
  }

  const args = [
    '--year', String(year),
    '--month', String(month),
    '--day', String(day),
    '--hour', String(hour),
    '--gender', gender,
    '--level', 'full',
  ];

  const result = await runPythonScript(scriptPath, args);

  if (result && result.success && result.full_report) {
    notify.sendAnalysis(result.full_report);

    // 保存精批结果
    const today = todayStr();
    savePending(`bazi-${year}${month}${day}-${today}.json`, {
      birth: { year, month, day, hour, gender },
      result,
      generated_at: new Date().toISOString(),
    });

    return { success: true, action: 'bazi-analysis-sent', birth: { year, month, day, hour, gender } };
  }

  const errorMsg = result && result.error ? result.error : '分析失败，请检查日期是否正确';
  notify.sendText(`🔮 八字精批遇到问题：${errorMsg}\n请确认出生日期格式正确后重试。`);
  return { success: false, action: 'bazi-analysis-failed', error: errorMsg };
}

/**
 * 处理视频链接分析（B站、YouTube 等）
 * @param {string} text - 包含视频链接的文本
 */
async function _runVideoAnalysis(text) {
  // TODO: 视频总结 skill 集成（qveris + openai-whisper + summarize）
  notify.sendConfirmation(
    '🎬 收到视频链接！\n\n本喵看到您发来了视频内容，请问您是需要：\n\n' +
    '1️⃣ 学习视频中的玄学知识（提取要点）\n' +
    '2️⃣ 分析视频中的命理内容\n' +
    '3️⃣ 解读视频讲解的术数技法\n\n' +
    '请回复序号或说明您的需求 🔮'
  );
  return { success: true, action: 'video-analysis-confirmation-sent', text };
}

module.exports = {
  handleAgentTurn,
  handleFeishuMessage,
  fetchHuangli,
  readUserInfo,
  savePending,
  pendingExists,
  todayStr,
  // 导出内部方法供测试
  _runDailyFortune,
  _runFortuneQuery,
  _runBaziAnalysis,
  _runImageAnalysis,
  _runVideoAnalysis,
  _hasBirthDate,
  _extractBirthParams,
};
