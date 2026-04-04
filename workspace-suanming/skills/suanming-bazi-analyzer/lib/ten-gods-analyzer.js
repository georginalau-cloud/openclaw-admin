'use strict';

/**
 * ten-gods-analyzer.js - 十神分析
 *
 * 功能：
 *   1. 计算四柱各干支对日主的十神关系
 *   2. 判断日主强弱
 *   3. 确定用神和忌神
 *   4. 生成十神分布分析
 *
 * 理论依据：梁湘润《子平真诠》十神理论
 */

const { getTenGod, getBranchTenGod, STEM_ELEMENT, HIDDEN_STEMS } = require('./ganzhi-calculator');

// 十神分类：同我（比劫）、我生（食伤）、我克（财）、克我（官杀）、生我（印）
const TEN_GOD_CATEGORY = {
  比肩: 'biJie',   // 比肩劫财（帮身）
  劫财: 'biJie',
  食神: 'shiShang', // 食神伤官（泄身）
  伤官: 'shiShang',
  偏财: 'cai',     // 偏财正财（我克）
  正财: 'cai',
  七杀: 'guanSha', // 七杀正官（克我）
  正官: 'guanSha',
  偏印: 'yin',     // 偏印正印（生我）
  正印: 'yin',
};

// 月令旺衰表（天干在各月令的力量）
// 值：3=旺，2=相，1=休，0=囚，-1=死
const STEM_MONTHLY_STRENGTH = {
  甲: { 寅: 3, 卯: 3, 辰: 1, 巳: 0, 午: -1, 未: -1, 申: -1, 酉: -1, 戌: -1, 亥: 2, 子: 1, 丑: 0 },
  乙: { 寅: 3, 卯: 3, 辰: 1, 巳: 0, 午: -1, 未: -1, 申: -1, 酉: -1, 戌: -1, 亥: 2, 子: 1, 丑: 0 },
  丙: { 寅: 2, 卯: 1, 辰: 0, 巳: 3, 午: 3, 未: 1, 申: -1, 酉: -1, 戌: -1, 亥: -1, 子: -1, 丑: -1 },
  丁: { 寅: 2, 卯: 1, 辰: 0, 巳: 3, 午: 3, 未: 1, 申: -1, 酉: -1, 戌: -1, 亥: -1, 子: -1, 丑: -1 },
  戊: { 寅: 0, 卯: -1, 辰: 3, 巳: 2, 午: 2, 未: 3, 申: 1, 酉: 0, 戌: 3, 亥: -1, 子: -1, 丑: 3 },
  己: { 寅: 0, 卯: -1, 辰: 3, 巳: 2, 午: 2, 未: 3, 申: 1, 酉: 0, 戌: 3, 亥: -1, 子: -1, 丑: 3 },
  庚: { 寅: -1, 卯: -1, 辰: 1, 巳: -1, 午: -1, 未: 0, 申: 3, 酉: 3, 戌: 1, 亥: 0, 子: 1, 丑: 2 },
  辛: { 寅: -1, 卯: -1, 辰: 1, 巳: -1, 午: -1, 未: 0, 申: 3, 酉: 3, 戌: 1, 亥: 0, 子: 1, 丑: 2 },
  壬: { 寅: -1, 卯: -1, 辰: -1, 巳: -1, 午: -1, 未: -1, 申: 2, 酉: 1, 戌: 0, 亥: 3, 子: 3, 丑: 1 },
  癸: { 寅: -1, 卯: -1, 辰: -1, 巳: -1, 午: -1, 未: -1, 申: 2, 酉: 1, 戌: 0, 亥: 3, 子: 3, 丑: 1 },
};

/**
 * 计算四柱各位置对日主的十神
 * @param {object} pillars     - 四柱 { year, month, day, hour }
 * @param {object} hiddenStems - 藏干
 * @param {string} dayMaster   - 日主天干
 * @returns {object} 十神分布
 */
function analyzeTenGods(pillars, hiddenStems, dayMaster) {
  const result = {
    year: {
      stem:   getTenGod(dayMaster, pillars.year.stem),
      branch: getBranchTenGod(dayMaster, pillars.year.branch),
      hidden: (hiddenStems.year || []).map(s => ({ stem: s, tenGod: getTenGod(dayMaster, s) })),
    },
    month: {
      stem:   getTenGod(dayMaster, pillars.month.stem),
      branch: getBranchTenGod(dayMaster, pillars.month.branch),
      hidden: (hiddenStems.month || []).map(s => ({ stem: s, tenGod: getTenGod(dayMaster, s) })),
    },
    day: {
      stem:   '日主',
      branch: getBranchTenGod(dayMaster, pillars.day.branch),
      hidden: (hiddenStems.day || []).map(s => ({ stem: s, tenGod: getTenGod(dayMaster, s) })),
    },
    hour: {
      stem:   getTenGod(dayMaster, pillars.hour.stem),
      branch: getBranchTenGod(dayMaster, pillars.hour.branch),
      hidden: (hiddenStems.hour || []).map(s => ({ stem: s, tenGod: getTenGod(dayMaster, s) })),
    },
  };

  // 统计各十神数量
  const tenGodCount = {};
  const tenGodList  = [];

  function addTenGod(tg, position) {
    if (!tg || tg === '日主') return;
    tenGodCount[tg] = (tenGodCount[tg] || 0) + 1;
    tenGodList.push({ tenGod: tg, position });
  }

  for (const pos of ['year', 'month', 'day', 'hour']) {
    addTenGod(result[pos].stem, `${pos}干`);
    addTenGod(result[pos].branch, `${pos}支`);
    for (const h of result[pos].hidden) {
      addTenGod(h.tenGod, `${pos}支藏干(${h.stem})`);
    }
  }

  return { ...result, tenGodCount, tenGodList };
}

/**
 * 判断日主强弱
 * 综合考虑：月令旺衰、帮身力量、克泄力量
 * @param {object} pillars     - 四柱
 * @param {object} hiddenStems - 藏干
 * @param {string} dayMaster   - 日主天干
 * @param {object} elementCount - 五行统计
 * @returns {object} 日主强弱分析
 */
function analyzeDayMasterStrength(pillars, hiddenStems, dayMaster, elementCount) {
  const monthBranch = pillars.month.branch;
  const dayMasterElem = STEM_ELEMENT[dayMaster];

  // 月令旺衰
  const monthStrength = (STEM_MONTHLY_STRENGTH[dayMaster] || {})[monthBranch] || 0;
  const monthStatus = monthStrength >= 2 ? '当令' : (monthStrength >= 0 ? '休囚' : '死绝');

  // 帮身力量：比劫 + 印绶
  const helpElements = getHelpElements(dayMasterElem);
  let helpScore = 0;
  for (const elem of helpElements) {
    helpScore += (elementCount[elem] || 0);
  }

  // 克泄力量：食伤 + 财 + 官杀
  const weakenElements = getWeakenElements(dayMasterElem);
  let weakenScore = 0;
  for (const elem of weakenElements) {
    weakenScore += (elementCount[elem] || 0);
  }

  // 月令旺则加分
  const totalScore = helpScore + monthStrength - weakenScore;

  let strength;
  let strengthLabel;
  if (monthStrength >= 2 && totalScore >= 3) {
    strength = 'very_strong';
    strengthLabel = '身强（极旺）';
  } else if (totalScore >= 1) {
    strength = 'strong';
    strengthLabel = '身强';
  } else if (totalScore >= -1) {
    strength = 'balanced';
    strengthLabel = '中和';
  } else if (totalScore >= -3) {
    strength = 'weak';
    strengthLabel = '身弱';
  } else {
    strength = 'very_weak';
    strengthLabel = '身弱（极弱）';
  }

  return {
    monthStatus,
    monthStrength,
    helpScore,
    weakenScore,
    totalScore,
    strength,
    strengthLabel,
    isStrong: totalScore >= 0,
  };
}

/**
 * 获取帮助日主五行的五行列表（比劫同、印生）
 * @param {string} element - 日主五行
 * @returns {string[]}
 */
function getHelpElements(element) {
  const generatesMap = { 木: '水', 火: '木', 土: '火', 金: '土', 水: '金' };
  return [element, generatesMap[element]].filter(Boolean);
}

/**
 * 获取克泄日主五行的五行列表（食伤泄、财克、官杀攻）
 * @param {string} element - 日主五行
 * @returns {string[]}
 */
function getWeakenElements(element) {
  const generatedByMap = { 木: '火', 火: '土', 土: '金', 金: '水', 水: '木' };
  const controlledByMap = { 木: '金', 火: '水', 土: '木', 金: '火', 水: '土' };
  return [
    generatedByMap[element],  // 食伤（我生）
    controlledByMap[element], // 官杀（克我）
    controlledByMap[element], // 财（我克的反向）
  ].filter(Boolean);
}

/**
 * 确定用神和忌神
 * 基于日主强弱和月令，遵循《子平真诠》取用神原则
 * @param {object} strengthAnalysis - 日主强弱分析
 * @param {string} dayMasterElem    - 日主五行
 * @param {string} monthBranch      - 月支
 * @returns {object} 用神忌神分析
 */
function determineYongShen(strengthAnalysis, dayMasterElem, monthBranch) {
  const { isStrong, strength } = strengthAnalysis;
  const generatesMap  = { 木: '火', 火: '土', 土: '金', 金: '水', 水: '木' };
  const controlsMap   = { 木: '土', 火: '金', 土: '水', 金: '木', 水: '火' };
  const generatedByMap = { 木: '水', 火: '木', 土: '火', 金: '土', 水: '金' };
  const controlledByMap = { 木: '金', 火: '水', 土: '木', 金: '火', 水: '土' };

  let yongShen = [];  // 用神五行
  let jiShen  = [];   // 忌神五行
  let analysis = '';

  if (strength === 'very_strong' || strength === 'strong') {
    // 身强：用食伤泄秀、或财官耗制
    yongShen = [
      generatesMap[dayMasterElem],   // 食伤（我生之元素）
      controlsMap[dayMasterElem],    // 财（我克之元素）
      controlledByMap[dayMasterElem], // 官杀（克我之元素）
    ].filter((v, i, a) => a.indexOf(v) === i);
    jiShen = [
      dayMasterElem,                 // 比劫（同我）
      generatedByMap[dayMasterElem], // 印（生我）
    ].filter((v, i, a) => a.indexOf(v) === i);
    analysis = `日主${strength === 'very_strong' ? '极旺' : '偏强'}，宜用食伤泄秀或财官克制，忌比劫帮身和印绶生旺`;
  } else if (strength === 'very_weak' || strength === 'weak') {
    // 身弱：用比劫帮身、印绶生旺
    yongShen = [
      dayMasterElem,                 // 比劫（同我）
      generatedByMap[dayMasterElem], // 印（生我）
    ].filter((v, i, a) => a.indexOf(v) === i);
    jiShen = [
      generatesMap[dayMasterElem],   // 食伤（泄我）
      controlsMap[dayMasterElem],    // 财（我克，耗日主）
      controlledByMap[dayMasterElem], // 官杀（克我）
    ].filter((v, i, a) => a.indexOf(v) === i);
    analysis = `日主${strength === 'very_weak' ? '极弱' : '偏弱'}，宜用比劫帮身或印绶生旺，忌食伤财官克泄`;
  } else {
    // 中和：以月令取用，调候为先
    yongShen = [generatesMap[dayMasterElem], controlsMap[dayMasterElem]];
    jiShen   = [];
    analysis = '日主中和，以月令调候取用神，用神较为灵活';
  }

  // 用神对应的十神
  const yongShenTenGods = mapElementsToTenGods(dayMasterElem, yongShen, isStrong);
  const jiShenTenGods   = mapElementsToTenGods(dayMasterElem, jiShen, isStrong);

  return {
    yongShen,
    jiShen,
    yongShenTenGods,
    jiShenTenGods,
    analysis,
  };
}

/**
 * 将五行列表映射到十神名称
 * @param {string}   dayMasterElem - 日主五行
 * @param {string[]} elements      - 五行列表
 * @param {boolean}  isDayStrong   - 日主是否强
 * @returns {string[]}
 */
function mapElementsToTenGods(dayMasterElem, elements, isDayStrong) {
  const elemToTenGods = {
    same:        ['比肩', '劫财'],   // 同我
    generates:   ['食神', '伤官'],   // 我生
    controls:    ['偏财', '正财'],   // 我克
    controlled:  ['七杀', '正官'],   // 克我
    generatedBy: ['偏印', '正印'],   // 生我
  };

  const generatesMap   = { 木: '火', 火: '土', 土: '金', 金: '水', 水: '木' };
  const controlsMap    = { 木: '土', 火: '金', 土: '水', 金: '木', 水: '火' };
  const generatedByMap = { 木: '水', 火: '木', 土: '火', 金: '土', 水: '金' };
  const controlledByMap = { 木: '金', 火: '水', 土: '木', 金: '火', 水: '土' };

  const result = [];
  for (const elem of elements) {
    if (elem === dayMasterElem) result.push(...elemToTenGods.same);
    else if (generatesMap[dayMasterElem] === elem) result.push(...elemToTenGods.generates);
    else if (controlsMap[dayMasterElem] === elem) result.push(...elemToTenGods.controls);
    else if (controlledByMap[dayMasterElem] === elem) result.push(...elemToTenGods.controlled);
    else if (generatedByMap[dayMasterElem] === elem) result.push(...elemToTenGods.generatedBy);
  }
  return [...new Set(result)];
}

/**
 * 完整十神分析
 * @param {object} baziData - calcFourPillars 返回的数据
 * @returns {object} 完整十神分析结果
 */
function analyze(baziData) {
  const { pillars, hiddenStems, dayMaster, dayMasterElement, elementCount } = baziData;

  const tenGods = analyzeTenGods(pillars, hiddenStems, dayMaster);
  const strengthAnalysis = analyzeDayMasterStrength(pillars, hiddenStems, dayMaster, elementCount);
  const yongJiShen = determineYongShen(strengthAnalysis, dayMasterElement, pillars.month.branch);

  return {
    dayMaster,
    dayMasterElement,
    tenGods,
    strengthAnalysis,
    yongJiShen,
    summary: buildSummary(dayMaster, dayMasterElement, strengthAnalysis, yongJiShen, tenGods),
  };
}

function buildSummary(dayMaster, dayMasterElem, strengthAnalysis, yongJiShen, tenGods) {
  const lines = [];
  lines.push(`日主：${dayMaster}（${dayMasterElem}）`);
  lines.push(`日主强弱：${strengthAnalysis.strengthLabel}（月令${strengthAnalysis.monthStatus}，帮身力量${strengthAnalysis.helpScore}，克泄力量${strengthAnalysis.weakenScore}）`);
  lines.push(`用神：${yongJiShen.yongShenTenGods.join('、')}（五行：${yongJiShen.yongShen.join('、')}）`);
  lines.push(`忌神：${yongJiShen.jiShenTenGods.join('、')}（五行：${yongJiShen.jiShen.join('、')}）`);
  lines.push(`分析：${yongJiShen.analysis}`);

  // 十神分布概述
  const countStr = Object.entries(tenGods.tenGodCount)
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `${k}×${v}`)
    .join('、');
  if (countStr) lines.push(`十神分布：${countStr}`);

  return lines.join('\n');
}

module.exports = { analyze, analyzeTenGods, analyzeDayMasterStrength, determineYongShen };
