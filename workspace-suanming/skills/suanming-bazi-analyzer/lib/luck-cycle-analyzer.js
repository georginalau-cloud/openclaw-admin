'use strict';

/**
 * luck-cycle-analyzer.js - 大运与流年分析
 *
 * 功能：
 *   1. 计算十年大运序列
 *   2. 分析每步大运的吉凶
 *   3. 流年运势（近3-5年）
 *   4. 岁运并临/刑冲克害识别
 *   5. 关键转折点预警
 *
 * 理论依据：《子平真诠》大运流年论、《滴天髓》
 */

const { HEAVENLY_STEMS, EARTHLY_BRANCHES, STEM_ELEMENT, BRANCH_ELEMENT, getTenGod, getBranchTenGod } = require('./ganzhi-calculator');

// 地支六冲
const BRANCH_CHONG = {
  子: '午', 午: '子', 丑: '未', 未: '丑',
  寅: '申', 申: '寅', 卯: '酉', 酉: '卯',
  辰: '戌', 戌: '辰', 巳: '亥', 亥: '巳',
};

// 地支六合
const BRANCH_HE = {
  子: '丑', 丑: '子', 寅: '亥', 亥: '寅',
  卯: '戌', 戌: '卯', 辰: '酉', 酉: '辰',
  巳: '申', 申: '巳', 午: '未', 未: '午',
};

// 地支三合（部分）
const BRANCH_SAN_HE_GROUPS = [
  ['申', '子', '辰'], // 水局
  ['亥', '卯', '未'], // 木局
  ['寅', '午', '戌'], // 火局
  ['巳', '酉', '丑'], // 金局
];

// 地支相刑（自刑和三刑简化）
const BRANCH_XING = {
  子: '卯', 卯: '子',
  寅: '巳', 巳: '申', 申: '寅',
  丑: '戌', 戌: '未', 未: '丑',
};

/**
 * 大运流年完整分析
 * @param {object} baziData        - 四柱数据
 * @param {object} tenGodsAnalysis - 十神分析
 * @param {object} formatAnalysis  - 格局分析
 * @param {number} currentYear     - 当前公历年份
 * @returns {object} 大运流年分析
 */
function analyze(baziData, tenGodsAnalysis, formatAnalysis, currentYear) {
  const { pillars, luckCycleInfo, dayMaster, input } = baziData;
  const { yongJiShen } = tenGodsAnalysis;

  // 生成大运序列
  const luckCycles = generateLuckCycles(pillars, luckCycleInfo, input.year, input.gender);

  // 大运吉凶分析
  const luckCycleAnalysis = analyzeLuckCycles(luckCycles, dayMaster, yongJiShen, tenGodsAnalysis.strengthAnalysis);

  // 当前所处大运
  const birthYear = input.year;
  const age = currentYear - birthYear;
  const currentLuckCycle = findCurrentLuckCycle(luckCycleAnalysis, age, luckCycleInfo.approxStartAge);

  // 流年分析（近5年）
  const annualFortunes = analyzeAnnualFortunes(currentYear, 5, dayMaster, pillars, yongJiShen, luckCycles);

  // 关键转折点
  const turningPoints = identifyTurningPoints(luckCycleAnalysis, annualFortunes);

  return {
    luckCycleInfo,
    luckCycles: luckCycleAnalysis,
    currentLuckCycle,
    annualFortunes,
    turningPoints,
    summary: buildSummary({ luckCycleInfo, currentLuckCycle, luckCycleAnalysis, annualFortunes, turningPoints }),
  };
}

/**
 * 生成大运干支序列（8步）
 * 顺行：月柱之后按天干地支顺序
 * 逆行：月柱之前按天干地支逆序
 */
function generateLuckCycles(pillars, luckCycleInfo, birthYear, gender) {
  const { isForward, approxStartAge } = luckCycleInfo;

  const monthStemIdx   = HEAVENLY_STEMS.indexOf(pillars.month.stem);
  const monthBranchIdx = EARTHLY_BRANCHES.indexOf(pillars.month.branch);

  const cycles = [];
  for (let i = 1; i <= 8; i++) {
    let stemIdx, branchIdx;
    if (isForward) {
      stemIdx   = (monthStemIdx   + i) % 10;
      branchIdx = (monthBranchIdx + i) % 12;
    } else {
      stemIdx   = ((monthStemIdx   - i) % 10 + 10) % 10;
      branchIdx = ((monthBranchIdx - i) % 12 + 12) % 12;
    }

    const startAge = approxStartAge + (i - 1) * 10;
    const startYear = birthYear + startAge;

    cycles.push({
      index: i,
      stem:   HEAVENLY_STEMS[stemIdx],
      branch: EARTHLY_BRANCHES[branchIdx],
      ganzhi: HEAVENLY_STEMS[stemIdx] + EARTHLY_BRANCHES[branchIdx],
      startAge,
      endAge: startAge + 9,
      startYear,
      endYear: startYear + 9,
    });
  }

  return cycles;
}

/**
 * 分析各步大运的吉凶
 */
function analyzeLuckCycles(luckCycles, dayMaster, yongJiShen, strengthAnalysis) {
  return luckCycles.map(cycle => {
    const stemTenGod   = getTenGod(dayMaster, cycle.stem);
    const branchTenGod = getBranchTenGod(dayMaster, cycle.branch);

    // 判断是否为用神运
    const isYongShenStem   = (yongJiShen.yongShenTenGods || []).includes(stemTenGod);
    const isYongShenBranch = (yongJiShen.yongShenTenGods || []).includes(branchTenGod);
    const isJiShenStem     = (yongJiShen.jiShenTenGods   || []).includes(stemTenGod);
    const isJiShenBranch   = (yongJiShen.jiShenTenGods   || []).includes(branchTenGod);

    let fortune, fortuneScore;
    if (isYongShenStem && isYongShenBranch) {
      fortune = '大吉'; fortuneScore = 5;
    } else if (isYongShenStem || isYongShenBranch) {
      fortune = '吉'; fortuneScore = 4;
    } else if (isJiShenStem && isJiShenBranch) {
      fortune = '大凶'; fortuneScore = 1;
    } else if (isJiShenStem || isJiShenBranch) {
      fortune = '凶'; fortuneScore = 2;
    } else {
      fortune = '平'; fortuneScore = 3;
    }

    const analysis = buildLuckCycleDesc(cycle, stemTenGod, branchTenGod, fortune, strengthAnalysis);

    return {
      ...cycle,
      stemTenGod,
      branchTenGod,
      fortune,
      fortuneScore,
      analysis,
    };
  });
}

function buildLuckCycleDesc(cycle, stemTenGod, branchTenGod, fortune, strengthAnalysis) {
  const fortuneDescs = {
    大吉: '用神得力，此步大运运势极佳，事业财运双旺，是人生重要腾飞期',
    吉:   '大运较顺，天时地利，事业稳步向上，财运有所提升',
    平:   '大运平稳，无大起大落，适合稳步积累，勤劳可得小成',
    凶:   '忌神临运，此步需谨慎，容易遇到挫折，宜守不宜攻',
    大凶: '忌神强旺，此步大运阻力极大，需特别谨慎，做好风险防范',
  };

  const desc = fortuneDescs[fortune] || '此步大运需综合分析';
  return `${cycle.startAge}-${cycle.endAge}岁（${cycle.startYear}-${cycle.endYear}）大运${cycle.ganzhi}：天干${stemTenGod}，地支${branchTenGod}。${desc}`;
}

/**
 * 找到当前所处的大运
 */
function findCurrentLuckCycle(luckCycleAnalysis, currentAge, startAge) {
  if (currentAge < startAge) {
    return { note: `尚未起运，约${startAge}岁开始走第一步大运`, ganzhi: '待起运', fortune: '平' };
  }

  for (const cycle of luckCycleAnalysis) {
    if (currentAge >= cycle.startAge && currentAge <= cycle.endAge) {
      return { ...cycle, currentAge };
    }
  }

  return luckCycleAnalysis[luckCycleAnalysis.length - 1] || { note: '大运数据不足', fortune: '平' };
}

/**
 * 流年运势分析（近N年）
 */
function analyzeAnnualFortunes(currentYear, years, dayMaster, pillars, yongJiShen, luckCycles) {
  const fortunes = [];

  for (let i = 0; i < years; i++) {
    const year = currentYear + i;
    const yearGanzhi = calcYearGanzhiFromYear(year);
    const yearStemTenGod   = getTenGod(dayMaster, yearGanzhi.stem);
    const yearBranchTenGod = getBranchTenGod(dayMaster, yearGanzhi.branch);

    // 与日支的关系（冲合刑）
    const dayBranch = pillars.day.branch;
    const chong  = BRANCH_CHONG[dayBranch] === yearGanzhi.branch;
    const he     = BRANCH_HE[dayBranch] === yearGanzhi.branch;
    const xing   = BRANCH_XING[dayBranch] === yearGanzhi.branch;

    // 与年支的关系
    const yearBranchChong = BRANCH_CHONG[pillars.year.branch] === yearGanzhi.branch;

    // 用神忌神判断
    const isYong = (yongJiShen.yongShenTenGods || []).includes(yearStemTenGod) ||
                   (yongJiShen.yongShenTenGods || []).includes(yearBranchTenGod);
    const isJi   = (yongJiShen.jiShenTenGods   || []).includes(yearStemTenGod) ||
                   (yongJiShen.jiShenTenGods   || []).includes(yearBranchTenGod);

    let fortune, detail;
    if (chong && isJi) {
      fortune = '凶'; detail = `流年${yearGanzhi.ganzhi}，与日支相冲且为忌神年，需特别注意健康、婚姻、事业变动`;
    } else if (isYong && he) {
      fortune = '大吉'; detail = `流年${yearGanzhi.ganzhi}，用神得力且与日支相合，是难得的顺遂之年`;
    } else if (isYong) {
      fortune = '吉'; detail = `流年${yearGanzhi.ganzhi}，用神当令，${yearStemTenGod}旺，有利于事业发展`;
    } else if (isJi) {
      fortune = '凶'; detail = `流年${yearGanzhi.ganzhi}，忌神临年，${yearStemTenGod}旺，需防挫折与损失`;
    } else if (chong) {
      fortune = '需注意'; detail = `流年${yearGanzhi.ganzhi}，冲动日支${dayBranch}，该年份变动较多，需谨慎`;
    } else if (he) {
      fortune = '平吉'; detail = `流年${yearGanzhi.ganzhi}，与日支相合，感情婚姻方面有喜事`;
    } else {
      fortune = '平'; detail = `流年${yearGanzhi.ganzhi}，运势平稳，适合稳步积累`;
    }

    fortunes.push({
      year,
      ganzhi: yearGanzhi.ganzhi,
      stem: yearGanzhi.stem,
      branch: yearGanzhi.branch,
      stemTenGod: yearStemTenGod,
      branchTenGod: yearBranchTenGod,
      chong,
      he,
      xing,
      fortune,
      detail,
    });
  }

  return fortunes;
}

/**
 * 公历年份转年柱干支（简化版，供大运流年使用）
 */
function calcYearGanzhiFromYear(year) {
  const base = 1984;
  const offset = ((year - base) % 60 + 60) % 60;
  const stem   = HEAVENLY_STEMS[offset % 10];
  const branch = EARTHLY_BRANCHES[offset % 12];
  return { stem, branch, ganzhi: stem + branch };
}

/**
 * 识别关键转折点
 */
function identifyTurningPoints(luckCycleAnalysis, annualFortunes) {
  const turningPoints = [];

  // 大运吉凶变化点
  for (let i = 1; i < luckCycleAnalysis.length; i++) {
    const prev = luckCycleAnalysis[i - 1];
    const curr = luckCycleAnalysis[i];
    const diff = curr.fortuneScore - prev.fortuneScore;

    if (diff >= 2) {
      turningPoints.push({
        type: '大运转机',
        year: curr.startYear,
        age:  curr.startAge,
        desc: `约${curr.startAge}岁进入${curr.ganzhi}大运，运势由${prev.fortune}转为${curr.fortune}，是人生向上的重要转折`,
      });
    } else if (diff <= -2) {
      turningPoints.push({
        type: '大运危机',
        year: curr.startYear,
        age:  curr.startAge,
        desc: `约${curr.startAge}岁进入${curr.ganzhi}大运，运势由${prev.fortune}降至${curr.fortune}，需提前做好准备`,
      });
    }
  }

  // 流年凶年预警
  for (const af of annualFortunes) {
    if (af.fortune === '凶' || af.fortune === '大凶') {
      turningPoints.push({
        type: '流年预警',
        year: af.year,
        desc: `${af.year}年（${af.ganzhi}年）${af.detail}`,
      });
    }
  }

  return turningPoints;
}

function buildSummary(data) {
  const { luckCycleInfo, currentLuckCycle, luckCycleAnalysis, annualFortunes, turningPoints } = data;
  const lines = [];

  lines.push(`【大运起运】${luckCycleInfo.note}`);

  // 当前大运
  if (currentLuckCycle && currentLuckCycle.ganzhi && currentLuckCycle.ganzhi !== '待起运') {
    lines.push(`【当前大运】${currentLuckCycle.ganzhi}运（${currentLuckCycle.fortune}），${currentLuckCycle.analysis || ''}`);
  } else {
    lines.push(`【当前大运】${currentLuckCycle ? currentLuckCycle.note : '待分析'}`);
  }

  // 大运概览
  lines.push('【大运概览（8步）】');
  for (const cycle of luckCycleAnalysis.slice(0, 8)) {
    lines.push(`  ${cycle.startAge}-${cycle.endAge}岁 ${cycle.ganzhi}（${cycle.fortune}）`);
  }

  // 近年流年
  lines.push('【近年流年】');
  for (const af of annualFortunes) {
    lines.push(`  ${af.year}年${af.ganzhi}：${af.fortune} — ${af.detail}`);
  }

  // 转折点
  if (turningPoints.length) {
    lines.push('【关键转折点】');
    for (const tp of turningPoints.slice(0, 3)) {
      lines.push(`  • ${tp.desc}`);
    }
  }

  return lines.join('\n');
}

module.exports = { analyze, generateLuckCycles, calcYearGanzhiFromYear };
