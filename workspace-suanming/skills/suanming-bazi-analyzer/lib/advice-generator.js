'use strict';

/**
 * advice-generator.js - 趋吉避凶建议
 *
 * 功能：
 *   1. 开运色推荐
 *   2. 吉祥数字
 *   3. 最佳居住方位
 *   4. 合作伙伴属相建议
 *   5. 综合开运指引
 *
 * 理论依据：《渊海子平》《穷通宝鉴》趋吉避凶理论
 */

const path = require('path');
const fs   = require('fs');

// 加载风水数据
let FENG_SHUI_DATA = {};
try {
  FENG_SHUI_DATA = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'data', 'feng-shui-data.json'), 'utf8')
  );
} catch { /* 使用内置备选 */ }

/**
 * 趋吉避凶建议
 * @param {object} baziData        - 四柱数据
 * @param {object} tenGodsAnalysis - 十神分析
 * @param {object} formatAnalysis  - 格局分析
 * @returns {object} 趋吉避凶建议
 */
function analyze(baziData, tenGodsAnalysis, formatAnalysis) {
  const { dayMasterElement } = baziData;
  const { yongJiShen } = tenGodsAnalysis;

  const yongElem = (yongJiShen.yongShen || [])[0] || dayMasterElement;
  const jiElem   = (yongJiShen.jiShen   || [])[0];

  // 开运色推荐
  const luckyColors = getLuckyColors(yongElem, jiElem);

  // 吉祥数字
  const luckyNumbers = getLuckyNumbers(yongElem);

  // 最佳居住方位
  const luckyDirections = getLuckyDirections(yongElem, jiElem);

  // 合作伙伴属相建议
  const compatibleZodiac = getCompatibleZodiac(baziData.pillars);

  // 综合开运建议
  const generalAdvice = generateGeneralAdvice(baziData, tenGodsAnalysis, formatAnalysis, yongElem, jiElem);

  return {
    luckyColors,
    luckyNumbers,
    luckyDirections,
    compatibleZodiac,
    generalAdvice,
    summary: buildSummary({ luckyColors, luckyNumbers, luckyDirections, compatibleZodiac, generalAdvice, yongElem }),
  };
}

/**
 * 开运色推荐
 */
function getLuckyColors(yongElem, jiElem) {
  const colorData = (FENG_SHUI_DATA.lucky_colors_by_element || {})[yongElem];

  const fallback = {
    木: { primary: ['绿色', '青色'], secondary: ['蓝色', '黑色'], avoid: ['白色', '金色'] },
    火: { primary: ['红色', '紫色'], secondary: ['绿色'], avoid: ['黑色', '蓝色'] },
    土: { primary: ['黄色', '棕色'], secondary: ['红色'], avoid: ['绿色', '青色'] },
    金: { primary: ['白色', '金色'], secondary: ['黄色'], avoid: ['红色', '橙色'] },
    水: { primary: ['黑色', '蓝色'], secondary: ['白色'], avoid: ['黄色', '棕色'] },
  };

  const data = colorData || fallback[yongElem] || { primary: ['白色'], secondary: [], avoid: [] };

  return {
    primary: data.primary || [],
    secondary: data.secondary || [],
    avoid: data.avoid || [],
    reason: `用神为${yongElem}，多穿用${(data.primary || []).join('、')}色系物品有助于提升运势`,
  };
}

/**
 * 吉祥数字
 */
function getLuckyNumbers(yongElem) {
  const numberData = (FENG_SHUI_DATA.lucky_numbers_by_element || {})[yongElem];

  const fallback = {
    木: [3, 4, 8],
    火: [2, 7, 9],
    土: [0, 5, 10],
    金: [1, 6, 7],
    水: [1, 6],
  };

  const numbers = (numberData && numberData.numbers) || fallback[yongElem] || [6, 8];
  const reason  = (numberData && numberData.reason) || `${yongElem}五行对应数字`;

  return {
    numbers,
    reason,
    advice: `手机号、车牌号、门牌号等尽量包含${numbers.join('、')}等数字，可增强用神能量`,
  };
}

/**
 * 最佳居住方位
 */
function getLuckyDirections(yongElem, jiElem) {
  const dirData = (FENG_SHUI_DATA.lucky_directions_by_element || {})[yongElem];

  const fallback = {
    木: { best: ['东', '东南'], good: ['北'], avoid: ['西', '西北'], home_advice: '床头朝东' },
    火: { best: ['南', '东南'], good: ['东'], avoid: ['北'], home_advice: '居室南向采光好' },
    土: { best: ['西南', '东北'], good: ['南'], avoid: ['东'], home_advice: '选择房屋中央位置' },
    金: { best: ['西', '西北'], good: ['西南'], avoid: ['南'], home_advice: '床头朝西或西北' },
    水: { best: ['北', '西北'], good: ['西'], avoid: ['南'], home_advice: '北向房间适合水命人' },
  };

  const data = dirData || fallback[yongElem] || { best: ['东'], good: [], avoid: ['西'], home_advice: '选择用神方位居住' };

  return {
    best:      data.best || [],
    good:      data.good || [],
    avoid:     data.avoid || [],
    homeAdvice: data.home_advice || '',
    reason: `用神为${yongElem}，${(data.best || []).join('、')}方位最利运势发挥`,
  };
}

/**
 * 合作伙伴属相建议
 * 基于日支地支的六合、三合
 */
function getCompatibleZodiac(pillars) {
  const dayBranch = pillars.day.branch;
  const compatData = (FENG_SHUI_DATA.compatible_zodiac || {}).combinations || {};
  const dayData = compatData[dayBranch];

  const branchToZodiac = {
    子: '鼠', 丑: '牛', 寅: '虎', 卯: '兔',
    辰: '龙', 巳: '蛇', 午: '马', 未: '羊',
    申: '猴', 酉: '鸡', 戌: '狗', 亥: '猪',
  };

  if (dayData) {
    return {
      compatible: dayData.zodiac_names || [],
      compatibleBranches: dayData.best_match || [],
      reason: dayData.reason || '',
      advice: `与属${(dayData.zodiac_names || []).join('、')}的伙伴合作，六合三合关系，彼此助力，事半功倍`,
    };
  }

  return {
    compatible: [],
    compatibleBranches: [],
    reason: '需结合完整命局判断',
    advice: '选择合作伙伴时，优先考虑与日支形成六合或三合关系的属相',
  };
}

/**
 * 综合开运建议
 */
function generateGeneralAdvice(baziData, tenGodsAnalysis, formatAnalysis, yongElem, jiElem) {
  const advice = [];
  const { dayMaster, dayMasterElement } = baziData;
  const { strengthAnalysis } = tenGodsAnalysis;

  // 1. 名字/品牌用字建议
  advice.push({
    category: '名字/品牌',
    content: `名字、公司品牌可选含有${yongElem}五行字义的字（如${getElemChars(yongElem)}），有助于汇聚用神能量`,
  });

  // 2. 职业方向
  advice.push({
    category: '职业方向',
    content: `顺应用神五行（${yongElem}），选择对应行业，减少忌神（${jiElem || '无明显忌神'}）行业的束缚`,
  });

  // 3. 行为建议
  if (strengthAnalysis.isStrong) {
    advice.push({
      category: '行为建议',
      content: '日主偏强，宜主动开拓，发挥领导能力，多付出、多贡献，方能化旺为用',
    });
  } else {
    advice.push({
      category: '行为建议',
      content: '日主偏弱，宜借助贵人和外力，善于合作，循序渐进，不可冒进单干',
    });
  }

  // 4. 格局对应建议
  const formatAdvice = getFormatSpecificAdvice(formatAnalysis.format);
  if (formatAdvice) {
    advice.push({ category: '格局建议', content: formatAdvice });
  }

  // 5. 风水摆设
  advice.push({
    category: '风水摆设',
    content: `在家中或办公室${yongElem}方位（参见方位建议）摆放${yongElem}五行相关物品，如${getElemDecor(yongElem)}，有助聚气`,
  });

  return advice;
}

function getElemChars(elem) {
  const chars = {
    木: '林、森、杨、棋、桐',
    火: '炎、晨、明、煌、阳',
    土: '城、坤、培、基、地',
    金: '鑫、铭、金、锋、铮',
    水: '泽、海、涛、润、澄',
  };
  return chars[elem] || '';
}

function getElemDecor(elem) {
  const decors = {
    木: '植物盆栽、竹子、木质摆件',
    火: '红色装饰、灯具、蜡烛',
    土: '陶瓷摆件、黄色水晶',
    金: '金属艺术品、铜器、白色装饰',
    水: '鱼缸、流水摆件、黑色装饰',
  };
  return decors[elem] || '五行对应装饰品';
}

function getFormatSpecificAdvice(format) {
  const advices = {
    '正官格': '正官格宜走正规路线，通过考试、晋升获取成就，切忌走捷径或违规操作',
    '七杀格': '七杀格宜从事有挑战性工作，展现魄力，但需注意控制脾气，防止得罪贵人',
    '食神格': '食神格宜发挥才艺特长，在喜欢的领域深耕，享受创作过程，财富会自然跟随',
    '伤官格': '伤官格切勿待在不喜欢的环境中，要找到展现才华的舞台，创业往往比打工更适合',
    '建禄格': '建禄格靠自身努力最有效，不要指望意外横财，踏实走每一步，中年后有大成就',
    '正财格': '正财格踏实理财最重要，适合定期定额投资，避免高风险投机，财富积累稳健',
    '偏财格': '偏财格善用人脉资源，广结善缘，善于抓住商机，适合做生意或销售',
    '正印格': '正印格宜持续学习深造，官印相生时最旺，考证书、提升学历有助于运势提升',
  };
  return advices[format] || '';
}

function buildSummary(data) {
  const { luckyColors, luckyNumbers, luckyDirections, compatibleZodiac, generalAdvice, yongElem } = data;
  const lines = [];

  lines.push(`【用神五行】${yongElem}（以下建议均围绕用神展开）`);
  lines.push(`【开运颜色】主色：${luckyColors.primary.join('、')}；辅色：${luckyColors.secondary.join('、')}；忌用：${luckyColors.avoid.join('、')}`);
  lines.push(`【吉祥数字】${luckyNumbers.numbers.join('、')}（${luckyNumbers.reason}）`);
  lines.push(`【最佳方位】最佳：${luckyDirections.best.join('、')}；次选：${luckyDirections.good.join('、')}；避免：${luckyDirections.avoid.join('、')}`);
  lines.push(`【居家建议】${luckyDirections.homeAdvice}`);

  if (compatibleZodiac.compatible.length) {
    lines.push(`【合作属相】${compatibleZodiac.compatible.join('、')}（${compatibleZodiac.reason}）`);
  }

  lines.push('【综合开运建议】');
  for (const adv of generalAdvice) {
    lines.push(`  ${adv.category}：${adv.content}`);
  }

  return lines.join('\n');
}

module.exports = { analyze };
