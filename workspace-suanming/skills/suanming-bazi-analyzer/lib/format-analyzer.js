'use strict';

/**
 * format-analyzer.js - 格局判断
 *
 * 功能：
 *   1. 确定命盘格局（正官格、七杀格、食神格、伤官格、正财格、偏财格、印格、建禄格）
 *   2. 判断从格（从儿格、从财格、从官格等）
 *   3. 判断格局成格与破格
 *   4. 评估格局层次（上格、中格、下格）
 *
 * 理论依据：梁湘润《子平真诠》格局理论
 */

const { HIDDEN_STEMS, getTenGod } = require('./ganzhi-calculator');

// 普通格局对应的十神
const REGULAR_FORMATS = {
  '正官格': '正官',
  '七杀格': '七杀',
  '食神格': '食神',
  '伤官格': '伤官',
  '正财格': '正财',
  '偏财格': '偏财',
  '正印格': '正印',
  '偏印格': '偏印',
};

// 特殊格局（月令为比劫时）
const SPECIAL_FORMATS = ['建禄格', '月刃格'];

// 月支特殊格局判断（建禄、月刃需月支与日干同五行）
const JIANLV_MONTHS = {
  甲: '寅', 乙: '卯',
  丙: '巳', 丁: '午',
  戊: '巳', 己: '午',
  庚: '申', 辛: '酉',
  壬: '亥', 癸: '子',
};

// 月刃（阳干帝旺月）
const YUEREN_MONTHS = {
  甲: '卯', 丙: '午', 戊: '午', 庚: '酉', 壬: '子',
};

// 格局喜忌配置
const FORMAT_PREFERENCE = {
  '正官格': {
    yi: ['财星生官', '印星护官'],
    ji: ['伤官见官', '七杀混官', '刑冲破害'],
    description: '正官格贵气高雅，喜财印相生，忌伤官合官、七杀混杂',
  },
  '七杀格': {
    yi: ['食神制杀', '印星化杀', '财印并美'],
    ji: ['无制无化', '正官混杂', '财旺生杀'],
    description: '七杀格威猛果决，须食神或印星制化，无制则凶猛难控',
  },
  '食神格': {
    yi: ['食神生财', '财星旺盛'],
    ji: ['偏印夺食', '枭神破局'],
    description: '食神格主福寿聪明，喜财星引通，最忌偏印夺食',
  },
  '伤官格': {
    yi: ['伤官佩印', '伤官生财', '伤官驾杀'],
    ji: ['伤官见官', '财印两旺并伤'],
    description: '伤官格才华横溢，视具体情况取用，伤官见官则凶，伤官佩印则贵',
  },
  '正财格': {
    yi: ['官星生旺', '食伤生财'],
    ji: ['比劫分财', '七杀相乘'],
    description: '正财格勤俭积财，喜官星护财，忌比劫争夺',
  },
  '偏财格': {
    yi: ['财旺生官', '食伤生财'],
    ji: ['比劫夺财', '七杀攻身'],
    description: '偏财格豪爽重义，财运亨通，忌比劫合伙分夺',
  },
  '正印格': {
    yi: ['官印相生', '印绶生身'],
    ji: ['财星破印', '食伤泄气过重'],
    description: '正印格学识高雅，官印相生则大贵，财星破印则损贵',
  },
  '偏印格': {
    yi: ['财星制枭', '官杀配合'],
    ji: ['食神被夺', '偏印孤立'],
    description: '偏印格聪颖机敏，财星制枭最吉，孤立则孤僻',
  },
  '建禄格': {
    yi: ['官杀制禄', '财官并见'],
    ji: ['比劫再旺', '无官无财'],
    description: '建禄格自立自强，靠自身能力发迹，喜官财耗制',
  },
  '月刃格': {
    yi: ['官杀制刃', '财官并见'],
    ji: ['无制乱刃', '刑冲帮刃'],
    description: '月刃格威猛刚烈，须官杀制化，无制则祸患',
  },
};

/**
 * 判断命盘格局
 * 以月令为主，取月支藏干（本气）的十神为格
 * @param {object} pillars   - 四柱
 * @param {string} dayMaster - 日主天干
 * @param {object} strengthAnalysis - 日主强弱分析
 * @returns {object} 格局分析
 */
function determineFormat(pillars, dayMaster, strengthAnalysis) {
  const monthBranch = pillars.month.branch;

  // 月令藏干（本气）
  const monthHidden = HIDDEN_STEMS[monthBranch] || [];
  const mainStem    = monthHidden[0]; // 本气

  if (!mainStem) {
    return { format: '未知格', description: '无法确定格局', isSpecial: false };
  }

  // 检查特殊格局（建禄、月刃）
  if (JIANLV_MONTHS[dayMaster] === monthBranch) {
    const format = '建禄格';
    return buildFormatResult(format, monthBranch, dayMaster, pillars, strengthAnalysis, false);
  }

  if (YUEREN_MONTHS[dayMaster] === monthBranch) {
    const format = '月刃格';
    return buildFormatResult(format, monthBranch, dayMaster, pillars, strengthAnalysis, false);
  }

  // 普通格局：月令本气对日主的十神
  const tenGod = getTenGod(dayMaster, mainStem);
  const formatName = findFormatByTenGod(tenGod);

  // 检查从格（日主极弱时）
  if (strengthAnalysis.strength === 'very_weak') {
    const congFormat = checkCongFormat(pillars, dayMaster, tenGod);
    if (congFormat) {
      return { format: congFormat.name, description: congFormat.description, isSpecial: true, congFormat: true, level: 'special', levelDescription: congFormat.description, yi: [], ji: [] };
    }
  }

  return buildFormatResult(formatName || `${tenGod}格`, monthBranch, dayMaster, pillars, strengthAnalysis, false);
}

/**
 * 通过十神名找格局名
 */
function findFormatByTenGod(tenGod) {
  for (const [fmt, tg] of Object.entries(REGULAR_FORMATS)) {
    if (tg === tenGod) return fmt;
  }
  return null;
}

/**
 * 检查从格
 * 从财格、从官格、从儿格（从食伤）
 * @param {object} pillars
 * @param {string} dayMaster
 * @param {string} monthTenGod - 月令十神
 * @returns {object|null}
 */
function checkCongFormat(pillars, dayMaster, monthTenGod) {
  if (monthTenGod === '偏财' || monthTenGod === '正财') {
    return { name: '从财格', description: '日主极弱，全局财星旺盛，从财而走，富而不贵，适合经商' };
  }
  if (monthTenGod === '七杀' || monthTenGod === '正官') {
    return { name: '从官格', description: '日主极弱，官杀极旺无制，从官杀而走，适合从政权威' };
  }
  if (monthTenGod === '食神' || monthTenGod === '伤官') {
    return { name: '从儿格', description: '日主极弱，食伤极旺无印，从食伤而走，才华横溢享受生活' };
  }
  return null;
}

/**
 * 构建格局结果对象
 */
function buildFormatResult(formatName, monthBranch, dayMaster, pillars, strengthAnalysis, isSpecial) {
  const preference = FORMAT_PREFERENCE[formatName] || {};

  // 简单判断格局是否成格
  const isFormed = checkFormatFormed(formatName, pillars, dayMaster);
  const level    = determineFormatLevel(formatName, isFormed, strengthAnalysis);

  return {
    format: formatName,
    monthBranch,
    isSpecial,
    isFormed,
    level,
    yi:   preference.yi   || [],
    ji:   preference.ji   || [],
    description: preference.description || `${formatName}，需结合全局综合分析`,
    levelDescription: getLevelDescription(level, formatName),
  };
}

/**
 * 判断格局是否成格（简化判断）
 * 成格：格局神在局中有力，且没有被破坏
 * @returns {boolean}
 */
function checkFormatFormed(formatName, pillars, dayMaster) {
  // 简化判断：检查主要忌神是否出现
  const jiTenGods = (FORMAT_PREFERENCE[formatName] || {}).ji || [];
  // 此处简化返回true，实际需逐一检查忌神是否出现在四柱
  return true;
}

/**
 * 评估格局层次（上、中、下格）
 * @param {string} formatName
 * @param {boolean} isFormed
 * @param {object} strengthAnalysis
 * @returns {string} 'high' | 'mid' | 'low'
 */
function determineFormatLevel(formatName, isFormed, strengthAnalysis) {
  if (!isFormed) return 'low';
  const isBalanced = strengthAnalysis.strength === 'balanced' || strengthAnalysis.strength === 'strong';
  if (isBalanced) return 'high';
  if (strengthAnalysis.strength === 'very_strong' || strengthAnalysis.strength === 'very_weak') return 'mid';
  return 'mid';
}

function getLevelDescription(level, formatName) {
  const descriptions = {
    high: `${formatName}成格，格局清纯，属上格，富贵可期`,
    mid:  `${formatName}成格，格局有瑕，属中格，可小富贵`,
    low:  `${formatName}有破格嫌疑，需谨慎，属下格，成就平平`,
  };
  return descriptions[level] || '';
}

/**
 * 完整格局分析
 * @param {object} baziData        - calcFourPillars 数据
 * @param {object} strengthAnalysis - 日主强弱分析
 * @returns {object} 格局分析结果
 */
function analyze(baziData, strengthAnalysis) {
  const { pillars, dayMaster } = baziData;
  const formatResult = determineFormat(pillars, dayMaster, strengthAnalysis);

  return {
    ...formatResult,
    summary: buildSummary(formatResult),
  };
}

function buildSummary(result) {
  const lines = [];
  lines.push(`命格：${result.format}${result.isSpecial ? '（特殊格）' : ''}`);
  lines.push(`格局层次：${result.levelDescription || result.level}`);
  lines.push(`描述：${result.description}`);
  if (result.yi && result.yi.length) lines.push(`喜：${result.yi.join('、')}`);
  if (result.ji && result.ji.length) lines.push(`忌：${result.ji.join('、')}`);
  return lines.join('\n');
}

module.exports = { analyze, determineFormat };
