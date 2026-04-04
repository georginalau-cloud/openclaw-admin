'use strict';

/**
 * core.js - 肌肉喵核心消息处理模块
 *
 * 职责：
 *   1. 接收来自 routing.js 的路由消息
 *   2. 调用 LLM (MiniMax/DeepSeek) 进行决策
 *   3. 根据决策调用相应 skill (food-recognition / usda-lookup / ocr-scale)
 *   4. 将数据保存到 memory/pending/YYYY-MM-DD-*.json
 *   5. 通过 notify.js 发送飞书消息
 *   6. 返回处理结果
 */

const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const https = require('https');

const notify = require('./notify');

const logger = console;

// 工作空间路径
const WORKSPACE_PATH = process.env.WORKSPACE_PATH
  || path.join(process.env.HOME || '/root', '.openclaw', 'workspace-jirou');

const PENDING_DIR = path.join(WORKSPACE_PATH, 'memory', 'pending');
const SKILLS_DIR  = path.join(WORKSPACE_PATH, 'skills');

// LLM 提示词模板
const FEISHU_INTENT_PROMPT_TEMPLATE =
  '用户发来了一条消息：「{text}」\n\n' +
  '请判断用户想做什么，输出一个 JSON 对象，格式：' +
  '{"intent": "scale|breakfast|lunch|dinner|other", "meal_type": "breakfast|lunch|dinner|null"}\n' +
  '只输出 JSON，不要其他内容。';

// ---------------------------------------------------------------------------
// 日期工具
// ---------------------------------------------------------------------------

function todayStr() {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD
}

function yesterdayStr() {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return d.toISOString().slice(0, 10);
}

// ---------------------------------------------------------------------------
// 持久化工具
// ---------------------------------------------------------------------------

/**
 * 将数据保存到 memory/pending/ 目录
 * @param {string} filename - 不含目录的文件名，例如 "2024-01-15-breakfast.json"
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
// LLM 调用
// ---------------------------------------------------------------------------

/**
 * 调用 MiniMax LLM 进行决策
 * @param {string} prompt
 * @returns {Promise<string>}
 */
async function callLLM(prompt) {
  const apiKey   = process.env.MINIMAX_API_KEY;
  const groupId  = process.env.MINIMAX_GROUP_ID;

  if (!apiKey || !groupId) {
    logger.warn('[core] MiniMax API Key 未配置，跳过 LLM 调用');
    return '';
  }

  const body = JSON.stringify({
    model: 'abab6.5s-chat',
    messages: [
      {
        role: 'system',
        content: '你是肌肉喵，一个专注于健身和营养管理的 AI 助手。请以简洁、友好的方式回复用户。',
      },
      { role: 'user', content: prompt },
    ],
  });

  return new Promise((resolve) => {
    const options = {
      hostname: 'api.minimax.chat',
      path: `/v1/text/chatcompletion_v2?GroupId=${groupId}`,
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices && parsed.choices[0]
            && parsed.choices[0].message && parsed.choices[0].message.content;
          resolve(content || '');
        } catch {
          resolve('');
        }
      });
    });

    req.on('error', (err) => {
      logger.error('[core] LLM 调用失败:', err.message);
      resolve('');
    });

    req.write(body);
    req.end();
  });
}

// ---------------------------------------------------------------------------
// Skill 调用
// ---------------------------------------------------------------------------

/**
 * 执行 Python skill 脚本
 * @param {string}   script - 脚本路径
 * @param {string[]} args   - 命令行参数
 * @returns {Promise<object>}
 */
function runPythonSkill(script, args) {
  return new Promise((resolve) => {
    execFile('python3', [script, ...args], { timeout: 60000 }, (err, stdout, stderr) => {
      if (err) {
        logger.error(`[core] skill 执行失败 (${script}):`, err.message);
        if (stderr) logger.error('[core] stderr:', stderr.slice(0, 500));
        resolve({ success: false, error: err.message });
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch {
        // 脚本可能输出非 JSON（例如日志），尝试提取最后一个 JSON 块
        const match = stdout.match(/\{[\s\S]*\}(?=[^}]*$)/);
        if (match) {
          try { resolve(JSON.parse(match[0])); return; } catch { /* ignore */ }
        }
        resolve({ success: false, raw: stdout.slice(0, 500) });
      }
    });
  });
}

/**
 * 调用食物识别 skill
 * @param {string} imagePath - 图片路径（可选）
 * @param {string} text      - 文字描述（可选）
 * @param {string} mealType  - breakfast | lunch | dinner
 */
async function callFoodRecognition(imagePath, text, mealType) {
  const script = path.join(SKILLS_DIR, 'food-recognition', 'food_recognition.py');
  const args = ['--meal-type', mealType];
  if (imagePath) args.push('--image', imagePath);
  if (text)      args.push('--text', text);
  return runPythonSkill(script, args);
}

/**
 * 调用 USDA 热量查询 skill
 * @param {string} food   - 食物名称
 * @param {number} weight - 重量（克）
 */
async function callUSDALookup(food, weight) {
  const script = path.join(SKILLS_DIR, 'usda-lookup', 'usda_lookup.py');
  const args = ['--food', food, '--weight', String(weight)];
  return runPythonSkill(script, args);
}

/**
 * 调用有品秤 OCR skill
 * @param {string} imagePath - 图片路径
 */
async function callOCRScale(imagePath) {
  const script = path.join(SKILLS_DIR, 'ocr-scale', 'ocr_scale.py');
  return runPythonSkill(script, ['--image', imagePath]);
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

  const today = todayStr();

  switch (intent) {
    case 'morning-greeting': {
      notify.sendReminder(
        '☀️ 早安！新的一天开始了～\n\n请发送有品秤的截图，开始记录今天的身体数据 💪\n\n（截图需包含：体重、体脂、肌肉率等完整数据页面）'
      );
      return { success: true, action: 'morning-greeting-sent' };
    }

    case 'breakfast-reminder': {
      if (!pendingExists(`${today}-breakfast.json`)) {
        notify.sendReminder(
          '🍳 早餐时间到！\n\n请发送早餐的照片，或直接描述吃了什么（例如：燕麦粥200g、鸡蛋2个）\n\n我来帮你计算热量 🔢'
        );
        return { success: true, action: 'breakfast-reminder-sent' };
      }
      return { success: true, action: 'breakfast-data-exists-skip' };
    }

    case 'lunch-reminder': {
      if (!pendingExists(`${today}-lunch.json`)) {
        notify.sendReminder(
          '🍱 午餐时间到！\n\n请发送午餐的照片，或描述今天午餐吃了什么～\n\n今天的饮食状况很重要，认真记录才能准确分析热量 📊'
        );
        return { success: true, action: 'lunch-reminder-sent' };
      }
      return { success: true, action: 'lunch-data-exists-skip' };
    }

    case 'dinner-reminder': {
      if (!pendingExists(`${today}-dinner.json`)) {
        notify.sendReminder(
          '🍜 晚餐时间到！\n\n请发送晚餐照片或描述今天晚上吃了什么 🥢\n\n晚餐通常是一天中最后一餐，认真记录有助于计算今日热量总结 ✨'
        );
        return { success: true, action: 'dinner-reminder-sent' };
      }
      return { success: true, action: 'dinner-data-exists-skip' };
    }

    case 'evening-weight-reminder': {
      notify.sendReminder(
        '🌙 睡前体重记录时间～\n\n请发送有品秤的截图，记录今天晚上的身体数据 📊\n\n（晚上数据与早上对比，可以观察一天的变化规律）'
      );
      return { success: true, action: 'evening-weight-reminder-sent' };
    }

    case 'final-reminder': {
      const missing = [];
      const checks = [
        { file: `${today}-morning-scale.json`, label: '早晨体重' },
        { file: `${today}-evening-scale.json`, label: '晚上体重' },
        { file: `${today}-breakfast.json`,     label: '早餐' },
        { file: `${today}-lunch.json`,          label: '午餐' },
        { file: `${today}-dinner.json`,         label: '晚餐' },
      ];
      for (const check of checks) {
        if (!pendingExists(check.file)) missing.push(check.label);
      }
      if (missing.length > 0) {
        notify.sendReminder(
          `🔔 今日数据最后提醒\n\n以下数据尚未记录：\n${missing.map(m => `• ${m}`).join('\n')}\n\n日报将在 23:59 自动生成，缺失数据将显示为「-」\n\n如需补录，请在此之前发送给我 🙏`
        );
      }
      return { success: true, action: 'final-reminder-sent', missing };
    }

    case 'daily-report-generation': {
      return _runDailyReport(today, message);
    }

    case 'cleanup': {
      return _runCleanup();
    }

    default: {
      // 通用 agentTurn：尝试通过 LLM 理解并响应
      logger.info('[core] 通用 agentTurn，调用 LLM');
      const reply = await callLLM(message.message || '');
      if (reply) notify.sendText(reply);
      return { success: true, action: 'generic-llm-reply', reply };
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
  const event  = message.event || message;
  const msgObj = event.message || {};
  const msgType = msgObj.message_type || msgObj.msg_type || 'text';

  let text = '';
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
  }

  const today = todayStr();

  // 尝试通过 LLM 理解用户意图
  const contextPrompt = FEISHU_INTENT_PROMPT_TEMPLATE.replace('{text}', text || '[图片]');

  let intent = 'other';
  let mealType = null;

  try {
    const llmReply = await callLLM(contextPrompt);
    const parsed = JSON.parse(llmReply);
    intent   = parsed.intent   || 'other';
    mealType = parsed.meal_type !== 'null' ? parsed.meal_type : null;
  } catch {
    // 回退：通过关键字判断
    const lower = text.toLowerCase();
    if (lower.includes('体重') || lower.includes('秤') || imagePath) {
      intent = 'scale';
    } else if (lower.includes('早餐') || lower.includes('早上')) {
      intent = 'breakfast'; mealType = 'breakfast';
    } else if (lower.includes('午餐') || lower.includes('中午')) {
      intent = 'lunch'; mealType = 'lunch';
    } else if (lower.includes('晚餐') || lower.includes('晚上')) {
      intent = 'dinner'; mealType = 'dinner';
    }
  }

  logger.info(`[core] 飞书消息意图: ${intent}, mealType: ${mealType}`);

  switch (intent) {
    case 'scale': {
      if (!imagePath) {
        notify.sendReminder('📸 请发送有品秤的截图，我来帮你识别数据～');
        return { success: true, action: 'scale-awaiting-image' };
      }
      const result = await callOCRScale(imagePath);
      if (result.success) {
        const timeOfDay = new Date().getHours() < 15 ? 'morning' : 'evening';
        savePending(`${today}-${timeOfDay}-scale.json`, { date: today, timeOfDay, ...result });
        notify.sendConfirmation(
          `✅ 体重数据已记录！\n\n体重：${result.data && result.data.weight ? result.data.weight + ' kg' : '-'}\n体脂：${result.data && result.data.body_fat ? result.data.body_fat + '%' : '-'}\n肌肉率：${result.data && result.data.muscle_rate ? result.data.muscle_rate + '%' : '-'}\n\n数据已保存，加油！💪`
        );
      } else {
        notify.sendReminder('😅 OCR 识别失败，请重新发送更清晰的截图，或手动输入数据。');
      }
      return { success: result.success, action: 'scale-processed', result };
    }

    case 'breakfast':
    case 'lunch':
    case 'dinner': {
      const meal = mealType || intent;
      const mealLabels = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐' };
      const label = mealLabels[meal] || meal;

      let result;
      if (imagePath) {
        result = await callFoodRecognition(imagePath, null, meal);
      } else if (text) {
        result = await callFoodRecognition(null, text, meal);
      } else {
        notify.sendReminder(`🍽️ 请告诉我${label}吃了什么～可以发照片或文字描述。`);
        return { success: true, action: `${meal}-awaiting-input` };
      }

      if (result.success) {
        savePending(`${today}-${meal}.json`, { date: today, meal, ...result });
        const itemsList = (result.items || []).map(item =>
          `• ${item.name}${item.weight_g ? ` (${item.weight_g}g)` : ''}: ${item.calories || '-'} kcal`
        ).join('\n');
        notify.sendConfirmation(
          `✅ ${label}数据已记录！\n\n${itemsList || '数据已保存'}\n\n合计热量：${result.total_calories || '-'} kcal 🔢\n\n还有遗漏的食物吗？直接告诉我 😊`
        );
      } else {
        notify.sendReminder(`😅 食物识别遇到了问题，请重试或手动描述${label}内容。`);
      }
      return { success: result.success, action: `${meal}-processed`, result };
    }

    default: {
      // 通用回复
      const reply = await callLLM(text || '你好');
      if (reply) notify.sendText(reply);
      return { success: true, action: 'generic-feishu-reply', reply };
    }
  }
}

// ---------------------------------------------------------------------------
// 内部辅助方法
// ---------------------------------------------------------------------------

async function _runDailyReport(today, message) {
  logger.info('[core] 开始生成日报');
  const script = path.join(WORKSPACE_PATH, 'scripts', 'daily-report-generator.py');

  const result = await runPythonSkill(script, ['--date', today]);
  if (result && result.success !== false) {
    logger.info('[core] 日报生成成功');
    return { success: true, action: 'daily-report-generated', date: today };
  }

  logger.error('[core] 日报生成失败');
  notify.sendError('日报生成', new Error(result && result.error ? result.error : '未知错误'));
  return { success: false, action: 'daily-report-failed' };
}

async function _runCleanup() {
  const yesterday = yesterdayStr();
  const patterns = [
    `${yesterday}-morning-scale.json`,
    `${yesterday}-evening-scale.json`,
    `${yesterday}-breakfast.json`,
    `${yesterday}-lunch.json`,
    `${yesterday}-dinner.json`,
    `Garmin-${yesterday}.json`,
    `DailyReport-${yesterday}.md`,
  ];

  const deleted = [];
  for (const filename of patterns) {
    const filePath = path.join(PENDING_DIR, filename);
    if (fs.existsSync(filePath)) {
      try {
        fs.unlinkSync(filePath);
        deleted.push(filename);
        logger.info(`[core] 已删除: ${filePath}`);
      } catch (err) {
        logger.error(`[core] 删除失败 (${filePath}):`, err.message);
      }
    }
  }

  logger.info(`[core] 清理完成，删除了 ${deleted.length} 个文件`);
  return { success: true, action: 'cleanup-done', deleted };
}

module.exports = {
  handleAgentTurn,
  handleFeishuMessage,
  callFoodRecognition,
  callUSDALookup,
  callOCRScale,
  callLLM,
  savePending,
  pendingExists,
  todayStr,
  yesterdayStr,
};
