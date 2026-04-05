'use strict';

/**
 * ganzhi-calculator.js - 干支计算工具
 *
 * 功能：
 *   1. 根据公历生日（年月日时）计算四柱（年月日时天干地支）
 *   2. 计算五行属性
 *   3. 计算藏干（地支中藏的天干）
 *   4. 计算日主（日天干）
 *   5. 计算大运起运方向
 *
 * 算法来源：《三命通会》《渊海子平》干支历法推算
 */

// 天干序列（甲=0）
const HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];

// 地支序列（子=0）
const EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

// 天干五行
const STEM_ELEMENT = {
  甲: '木', 乙: '木',
  丙: '火', 丁: '火',
  戊: '土', 己: '土',
  庚: '金', 辛: '金',
  壬: '水', 癸: '水',
};

// 天干阴阳（阳=true）
const STEM_YIN_YANG = {
  甲: '阳', 乙: '阴',
  丙: '阳', 丁: '阴',
  戊: '阳', 己: '阴',
  庚: '阳', 辛: '阴',
  壬: '阳', 癸: '阴',
};

// 地支五行
const BRANCH_ELEMENT = {
  子: '水', 丑: '土',
  寅: '木', 卯: '木',
  辰: '土', 巳: '火',
  午: '火', 未: '土',
  申: '金', 酉: '金',
  戌: '土', 亥: '水',
};

// 地支藏干（本气、中气、余气）
const HIDDEN_STEMS = {
  子: ['癸'],
  丑: ['己', '癸', '辛'],
  寅: ['甲', '丙', '戊'],
  卯: ['乙'],
  辰: ['戊', '乙', '癸'],
  巳: ['丙', '庚', '戊'],
  午: ['丁', '己'],
  未: ['己', '丁', '乙'],
  申: ['庚', '壬', '戊'],
  酉: ['辛'],
  戌: ['戊', '辛', '丁'],
  亥: ['壬', '甲'],
};

// 地支对应的月份（寅月=农历正月=1）
const BRANCH_MONTH = {
  寅: 1, 卯: 2, 辰: 3, 巳: 4, 午: 5, 未: 6,
  申: 7, 酉: 8, 戌: 9, 亥: 10, 子: 11, 丑: 12,
};

// 月支序列（按月令顺序，寅月起）
const MONTH_BRANCHES = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑'];

// 时支与时辰映射（时支对应小时范围）
const HOUR_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

// 十二长生（天干在各地支上的十二运）
const TWELVE_GROWTH_STAGES = ['长生', '沐浴', '冠带', '临官', '帝旺', '衰', '病', '死', '墓', '绝', '胎', '养'];

// 阳干起长生表（各阳干在哪个地支起长生）
const YANG_STEM_BIRTH_BRANCH = {
  甲: '亥', 丙: '寅', 戊: '寅', 庚: '巳', 壬: '申',
};

// 阴干起长生（与同五行阳干相反）
const YIN_STEM_BIRTH_BRANCH = {
  乙: '午', 丁: '酉', 己: '酉', 辛: '子', 癸: '卯',
};

/**
 * 计算年柱干支
 * 公历年份转年干支（以立春为界，实际使用中通常简化按1月1日）
 * 甲子年起点：1864年（或以60年为循环）
 * @param {number} year - 公历年份
 * @returns {{ stem: string, branch: string }}
 */
function calcYearGanzhi(year) {
  // 以1984年（甲子年）为基准
  const base = 1984;
  const offset = ((year - base) % 60 + 60) % 60;
  const stem   = HEAVENLY_STEMS[offset % 10];
  const branch = EARTHLY_BRANCHES[offset % 12];
  return { stem, branch };
}

/**
 * 计算月柱干支
 * 月支固定：寅月（正月）= 索引0，按顺序排列
 * 月干由年干推算：五虎遁年起月法
 *
 * 五虎遁年起月法：
 *   甲己年：正月（寅月）起丙寅
 *   乙庚年：正月（寅月）起戊寅
 *   丙辛年：正月（寅月）起庚寅
 *   丁壬年：正月（寅月）起壬寅
 *   戊癸年：正月（寅月）起甲寅
 *
 * @param {number} month   - 农历月份（1-12，正月=1）
 * @param {string} yearStem - 年干
 * @returns {{ stem: string, branch: string }}
 */
function calcMonthGanzhi(month, yearStem) {
  // 月支（寅月=正月=1，故月支索引 = month - 1，但从寅开始）
  const branchIndex = (month - 1) % 12;
  const branch = MONTH_BRANCHES[branchIndex];

  // 五虎遁年起月法 - 寅月（正月）起的天干索引
  const startStemMap = { 甲: 2, 己: 2, 乙: 4, 庚: 4, 丙: 6, 辛: 6, 丁: 8, 壬: 8, 戊: 0, 癸: 0 };
  const startStemIndex = startStemMap[yearStem] || 0;
  const stemIndex = (startStemIndex + branchIndex) % 10;
  const stem = HEAVENLY_STEMS[stemIndex];

  return { stem, branch };
}

/**
 * 计算日柱干支
 * 使用公历日期推算干支，基准日：2000年1月1日（甲午日）
 * @param {number} year  - 公历年份
 * @param {number} month - 公历月份（1-12）
 * @param {number} day   - 公历日
 * @returns {{ stem: string, branch: string }}
 */
function calcDayGanzhi(year, month, day) {
  // 简化公式：以儒略日计算
  const julianDay = toJulianDay(year, month, day);
  // 基准：2000年1月1日 JD=2451545，甲午日（干=甲=0，支=午=6）
  const baseJD  = 2451545;
  const baseStem   = 0; // 甲
  const baseBranch = 6; // 午
  const diff = julianDay - baseJD;
  const stemIndex   = ((baseStem   + diff) % 10 + 10) % 10;
  const branchIndex = ((baseBranch + diff) % 12 + 12) % 12;
  return {
    stem:   HEAVENLY_STEMS[stemIndex],
    branch: EARTHLY_BRANCHES[branchIndex],
  };
}

/**
 * 公历转儒略日
 * @param {number} year
 * @param {number} month
 * @param {number} day
 * @returns {number} 儒略日
 */
function toJulianDay(year, month, day) {
  const a = Math.floor((14 - month) / 12);
  const y = year + 4800 - a;
  const m = month + 12 * a - 3;
  return day + Math.floor((153 * m + 2) / 5) + 365 * y
    + Math.floor(y / 4) - Math.floor(y / 100) + Math.floor(y / 400) - 32045;
}

/**
 * 计算时柱干支
 * 时支：子时=23-1点，丑时=1-3点，以此类推（每2小时一个时辰）
 * 时干由日干推算：五鼠遁日起时法
 *
 * 五鼠遁日起时法：
 *   甲己日：子时起甲子
 *   乙庚日：子时起丙子
 *   丙辛日：子时起戊子
 *   丁壬日：子时起庚子
 *   戊癸日：子时起壬子
 *
 * @param {number} hour   - 小时（0-23）
 * @param {string} dayStem - 日干
 * @returns {{ stem: string, branch: string }}
 */
function calcHourGanzhi(hour, dayStem) {
  // 时支：子时从23点开始（或0点）
  let branchIndex;
  if (hour === 23) {
    branchIndex = 0; // 子时
  } else {
    branchIndex = Math.floor((hour + 1) / 2) % 12;
  }
  const branch = HOUR_BRANCHES[branchIndex];

  // 五鼠遁日起时法 - 子时起的天干索引
  const startStemMap = { 甲: 0, 己: 0, 乙: 2, 庚: 2, 丙: 4, 辛: 4, 丁: 6, 壬: 6, 戊: 8, 癸: 8 };
  const startStemIndex = startStemMap[dayStem] || 0;
  const stemIndex = (startStemIndex + branchIndex) % 10;
  const stem = HEAVENLY_STEMS[stemIndex];

  return { stem, branch };
}

/**
 * 公历转大约农历月份（简化计算，用于月柱推算）
 * 注意：精确计算需要节气表，此处用近似方法
 * @param {number} year
 * @param {number} month - 公历月份
 * @param {number} day
 * @returns {number} 大约农历月份（1-12）
 */
function approxLunarMonth(year, month, day) {
  // 简化：以节气划分，每月约在公历月份-1处有节
  // 节气大约在公历每月4-6日前后
  // 此处使用简化算法：公历月份基本对应农历月份加1
  // 寅月（正月）约对应公历2月4日后
  const solarTermApprox = [
    { month: 2,  day: 4,  lunarMonth: 1  }, // 立春 寅月
    { month: 3,  day: 6,  lunarMonth: 2  }, // 惊蛰 卯月
    { month: 4,  day: 5,  lunarMonth: 3  }, // 清明 辰月
    { month: 5,  day: 6,  lunarMonth: 4  }, // 立夏 巳月
    { month: 6,  day: 6,  lunarMonth: 5  }, // 芒种 午月
    { month: 7,  day: 7,  lunarMonth: 6  }, // 小暑 未月
    { month: 8,  day: 7,  lunarMonth: 7  }, // 立秋 申月
    { month: 9,  day: 8,  lunarMonth: 8  }, // 白露 酉月
    { month: 10, day: 8,  lunarMonth: 9  }, // 寒露 戌月
    { month: 11, day: 7,  lunarMonth: 10 }, // 立冬 亥月
    { month: 12, day: 7,  lunarMonth: 11 }, // 大雪 子月
    { month: 1,  day: 6,  lunarMonth: 12 }, // 小寒 丑月
  ];

  // 找到当前公历月日所属的月令
  let lunarMonth = 12; // 默认丑月
  for (const term of solarTermApprox) {
    if (month > term.month || (month === term.month && day >= term.day)) {
      lunarMonth = term.lunarMonth;
    }
  }
  return lunarMonth;
}

/**
 * 计算完整四柱
 * @param {object} params
 * @param {number} params.year   - 公历年
 * @param {number} params.month  - 公历月
 * @param {number} params.day    - 公历日
 * @param {number} params.hour   - 小时（0-23）
 * @param {string} params.gender - 性别 ('male' | 'female')
 * @returns {object} 四柱完整数据
 */
function calcFourPillars({ year, month, day, hour, gender }) {
  const lunarMonth = approxLunarMonth(year, month, day);

  const yearGZ  = calcYearGanzhi(year);
  const monthGZ = calcMonthGanzhi(lunarMonth, yearGZ.stem);
  const dayGZ   = calcDayGanzhi(year, month, day);
  const hourGZ  = calcHourGanzhi(hour, dayGZ.stem);

  const pillars = {
    year:  { stem: yearGZ.stem,  branch: yearGZ.branch,  ganzhi: yearGZ.stem  + yearGZ.branch  },
    month: { stem: monthGZ.stem, branch: monthGZ.branch, ganzhi: monthGZ.stem + monthGZ.branch },
    day:   { stem: dayGZ.stem,   branch: dayGZ.branch,   ganzhi: dayGZ.stem   + dayGZ.branch   },
    hour:  { stem: hourGZ.stem,  branch: hourGZ.branch,  ganzhi: hourGZ.stem  + hourGZ.branch  },
  };

  // 藏干
  const hiddenStems = {
    year:  HIDDEN_STEMS[yearGZ.branch]  || [],
    month: HIDDEN_STEMS[monthGZ.branch] || [],
    day:   HIDDEN_STEMS[dayGZ.branch]   || [],
    hour:  HIDDEN_STEMS[hourGZ.branch]  || [],
  };

  // 五行统计（天干 + 藏干）
  const elementCount = calcElementCount(pillars, hiddenStems);

  // 日主（日柱天干）
  const dayMaster = dayGZ.stem;
  const dayMasterElement = STEM_ELEMENT[dayMaster];
  const dayMasterYinYang = STEM_YIN_YANG[dayMaster];

  // 大运起运年龄与方向
  const luckCycleInfo = calcLuckCycleStart(pillars, year, month, day, gender);

  return {
    pillars,
    hiddenStems,
    elementCount,
    dayMaster,
    dayMasterElement,
    dayMasterYinYang,
    luckCycleInfo,
    input: { year, month, day, hour, gender },
    lunarMonth,
  };
}

/**
 * 统计各五行力量
 * @param {object} pillars     - 四柱
 * @param {object} hiddenStems - 藏干
 * @returns {object} 五行计数 { 木: n, 火: n, 土: n, 金: n, 水: n }
 */
function calcElementCount(pillars, hiddenStems) {
  const count = { 木: 0, 火: 0, 土: 0, 金: 0, 水: 0 };

  const allStems = [
    pillars.year.stem, pillars.month.stem, pillars.day.stem, pillars.hour.stem,
    pillars.year.branch, pillars.month.branch, pillars.day.branch, pillars.hour.branch,
  ];

  for (const s of allStems) {
    const elem = STEM_ELEMENT[s] || BRANCH_ELEMENT[s];
    if (elem && count[elem] !== undefined) count[elem]++;
  }

  // 藏干加权（本气=0.5权重）
  const allHidden = [
    ...hiddenStems.year, ...hiddenStems.month, ...hiddenStems.day, ...hiddenStems.hour,
  ];
  for (const s of allHidden) {
    const elem = STEM_ELEMENT[s];
    if (elem && count[elem] !== undefined) count[elem] += 0.5;
  }

  return count;
}

/**
 * 计算大运起运年龄与方向
 * 阳年生男或阴年生女：顺排，起运向后（晚晚）
 * 阴年生男或阳年生女：逆排，起运向前（往前数节气）
 * 简化计算：返回起运年龄估算（通常3-8岁）
 * @param {object} pillars
 * @param {number} year
 * @param {number} month
 * @param {number} day
 * @param {string} gender
 * @returns {object}
 */
function calcLuckCycleStart(pillars, year, month, day, gender) {
  // 阳年：年干为甲丙戊庚壬（索引 0,2,4,6,8）
  const stemIndex = HEAVENLY_STEMS.indexOf(pillars.year.stem);
  const isYangYear = stemIndex % 2 === 0;
  const isMale = gender === 'male';

  // 顺行：阳年男命、阴年女命
  const isForward = (isYangYear && isMale) || (!isYangYear && !isMale);

  // 简化起运年龄估算（实际需节气精确计算，此处使用近似值）
  // 标准算法：从生日数到最近节气的天数 / 3 = 起运岁数
  // 近似：生于月初者约3-4岁起运，生于月中者约5-6岁，生于月末者约7-8岁
  const approxStartAge = Math.max(3, Math.min(8, Math.round(day / 4)));

  return {
    isForward,
    direction: isForward ? '顺行' : '逆行',
    approxStartAge,
    note: `约${approxStartAge}岁起运，${isForward ? '顺' : '逆'}行大运`,
  };
}

/**
 * 获取天干的十神关系
 * @param {string} dayStem   - 日主天干
 * @param {string} otherStem - 目标天干
 * @returns {string} 十神名称
 */
function getTenGod(dayStem, otherStem) {
  if (dayStem === otherStem) return '比肩';

  const dayElem  = STEM_ELEMENT[dayStem];
  const otherElem = STEM_ELEMENT[otherStem];
  const dayYY    = STEM_YIN_YANG[dayStem];
  const otherYY  = STEM_YIN_YANG[otherStem];
  const sameYY   = dayYY === otherYY;

  // 五行生克关系
  const generates = { 木: '火', 火: '土', 土: '金', 金: '水', 水: '木' };
  const controls  = { 木: '土', 火: '金', 土: '水', 金: '木', 水: '火' };
  const generatedBy = { 火: '木', 土: '火', 金: '土', 水: '金', 木: '水' };
  const controlledBy = { 土: '木', 金: '火', 水: '土', 木: '金', 火: '水' };

  if (otherElem === dayElem) {
    return sameYY ? '比肩' : '劫财';
  }
  if (generates[dayElem] === otherElem) {
    return sameYY ? '食神' : '伤官';
  }
  if (controls[dayElem] === otherElem) {
    return sameYY ? '偏财' : '正财';
  }
  if (controlledBy[dayElem] === otherElem) {
    return sameYY ? '七杀' : '正官';
  }
  if (generatedBy[dayElem] === otherElem) {
    return sameYY ? '偏印' : '正印';
  }

  return '未知';
}

/**
 * 获取地支的主要十神（取本气天干的十神）
 * @param {string} dayStem - 日主天干
 * @param {string} branch  - 地支
 * @returns {string} 十神名称
 */
function getBranchTenGod(dayStem, branch) {
  const hidden = HIDDEN_STEMS[branch];
  if (!hidden || hidden.length === 0) return '未知';
  return getTenGod(dayStem, hidden[0]);
}

module.exports = {
  HEAVENLY_STEMS,
  EARTHLY_BRANCHES,
  STEM_ELEMENT,
  STEM_YIN_YANG,
  BRANCH_ELEMENT,
  HIDDEN_STEMS,
  MONTH_BRANCHES,
  HOUR_BRANCHES,
  calcFourPillars,
  calcYearGanzhi,
  calcMonthGanzhi,
  calcDayGanzhi,
  calcHourGanzhi,
  calcElementCount,
  getTenGod,
  getBranchTenGod,
  approxLunarMonth,
  toJulianDay,
};
