'use strict';

/**
 * wealth-career-analyzer.js - 财富事业分析
 *
 * 功能：
 *   1. 财富等级评估（小富、中富、巨富）
 *   2. 求财方式（薪资、创业、投机）
 *   3. 行业指导（五行喜忌匹配职业）
 *   4. 事业高低点识别
 *
 * 理论依据：《三命通会》财官论、《穷通宝鉴》行业五行
 */

const path = require('path');
const fs   = require('fs');

// 加载行业对应表
let INDUSTRIES_DATA = {};
try {
  INDUSTRIES_DATA = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'data', 'industries-mapping.json'), 'utf8')
  );
} catch { /* 使用内置备选 */ }

/**
 * 财富事业完整分析
 * @param {object} baziData        - 四柱数据
 * @param {object} tenGodsAnalysis - 十神分析
 * @param {object} formatAnalysis  - 格局分析
 * @returns {object} 财富事业分析
 */
function analyze(baziData, tenGodsAnalysis, formatAnalysis) {
  const { dayMaster, dayMasterElement, elementCount } = baziData;
  const tenGodCount = (tenGodsAnalysis.tenGods || {}).tenGodCount || {};
  const { yongJiShen, strengthAnalysis } = tenGodsAnalysis;

  // 财富等级
  const wealthLevel = assessWealthLevel(tenGodCount, formatAnalysis, strengthAnalysis, elementCount);

  // 求财方式
  const wealthMethod = assessWealthMethod(tenGodCount, dayMasterElement, strengthAnalysis);

  // 行业指导
  const careerIndustries = recommendIndustries(yongJiShen, dayMasterElement, tenGodCount);

  // 事业高低点
  const careerPeakValleys = identifyCareerTrends(baziData, tenGodCount, formatAnalysis);

  // 财富积累建议
  const wealthAdvice = generateWealthAdvice(wealthLevel, wealthMethod, yongJiShen);

  return {
    wealthLevel,
    wealthMethod,
    careerIndustries,
    careerPeakValleys,
    wealthAdvice,
    summary: buildSummary({ wealthLevel, wealthMethod, careerIndustries, careerPeakValleys, wealthAdvice }),
  };
}

/**
 * 评估财富等级
 * 基于财星力量、官印配合、格局层次
 */
function assessWealthLevel(tenGodCount, formatAnalysis, strengthAnalysis, elementCount) {
  let score = 0;

  // 格局层次
  if (formatAnalysis.level === 'high') score += 3;
  else if (formatAnalysis.level === 'mid') score += 1;

  // 财星力量
  const caiCount = (tenGodCount['正财'] || 0) + (tenGodCount['偏财'] || 0);
  score += Math.min(caiCount, 2);

  // 官星力量（正官格最利财运）
  const guanCount = (tenGodCount['正官'] || 0) + (tenGodCount['七杀'] || 0);
  if (guanCount >= 1) score += 1;

  // 食伤生财
  const shiShangCount = (tenGodCount['食神'] || 0) + (tenGodCount['伤官'] || 0);
  if (shiShangCount >= 1) score += 1;

  // 日主强弱适中加分
  if (strengthAnalysis.strength === 'strong' || strengthAnalysis.strength === 'balanced') score += 1;

  let level, description, characteristics;
  if (score >= 6) {
    level = 'great_wealth';
    description = '巨富潜力（命中有大财格局）';
    characteristics = '有成为富豪的命理基础，需把握大运时机，投资眼光独到，财富可观';
  } else if (score >= 4) {
    level = 'moderate_wealth';
    description = '中富（财运稳健，小康有余）';
    characteristics = '财运稳健，能过上较为富裕的生活，通过努力可积累可观财富';
  } else if (score >= 2) {
    level = 'small_wealth';
    description = '小富（生活宽裕，衣食无忧）';
    characteristics = '财运一般但稳定，能维持较好的生活水平，需勤劳积累';
  } else {
    level = 'modest';
    description = '普通（需勤劳积累，靠本分赚钱）';
    characteristics = '财运平平，靠本分勤劳赚钱，生活无虞但大富不易';
  }

  return { score, level, description, characteristics };
}

/**
 * 评估求财方式
 */
function assessWealthMethod(tenGodCount, dayMasterElem, strengthAnalysis) {
  const methods = [];
  const primaryMethod = [];
  const riskWarning = [];

  // 正财：稳定薪资/勤劳积累
  if ((tenGodCount['正财'] || 0) >= 1) {
    primaryMethod.push('稳定薪资或勤劳积累');
    methods.push({ type: 'salary', desc: '正财得力，适合通过稳定工作积累财富，理财有道' });
  }

  // 偏财：投机或经商
  if ((tenGodCount['偏财'] || 0) >= 1) {
    primaryMethod.push('经商或投机');
    methods.push({ type: 'business', desc: '偏财得力，有偏财运，适合做生意或把握横财机会' });
  }

  // 食伤生财：靠才华/技能
  if ((tenGodCount['食神'] || 0) + (tenGodCount['伤官'] || 0) >= 1) {
    primaryMethod.push('才华技能变现');
    methods.push({ type: 'skill', desc: '食伤旺，靠才华、技能、创意赚钱效果最好' });
  }

  // 官杀：靠职位/权力
  if ((tenGodCount['正官'] || 0) + (tenGodCount['七杀'] || 0) >= 1) {
    primaryMethod.push('职位晋升');
    methods.push({ type: 'career', desc: '官杀有力，靠职位晋升和权力资源积累财富' });
  }

  // 比劫旺：需防破财
  if ((tenGodCount['比肩'] || 0) + (tenGodCount['劫财'] || 0) >= 2) {
    riskWarning.push('比劫过旺，需防因合伙或朋友破财，财务要独立');
  }

  // 伤官重：需防冲动损失
  if ((tenGodCount['伤官'] || 0) >= 2) {
    riskWarning.push('伤官过旺，需防因冲动或不服管教导致职业挫折');
  }

  return {
    primaryMethods: primaryMethod.length > 0 ? primaryMethod : ['勤劳本分赚钱'],
    methods,
    riskWarning,
    summary: `主要求财方式：${(primaryMethod.length > 0 ? primaryMethod : ['勤劳本分赚钱']).join('、')}`,
  };
}

/**
 * 推荐行业
 * 基于用神五行选择有利行业
 */
function recommendIndustries(yongJiShen, dayMasterElem, tenGodCount) {
  const recommended = [];
  const avoid = [];

  const fiveElems = INDUSTRIES_DATA.five_elements || {};

  // 用神五行对应推荐行业
  for (const elem of (yongJiShen.yongShen || [])) {
    const elemData = fiveElems[elem];
    if (elemData) {
      recommended.push({
        element: elem,
        industries: elemData.industries ? elemData.industries.slice(0, 5) : [],
        reason: `用神为${elem}，从事${elem}相关行业有助于财运`,
      });
    }
  }

  // 忌神五行对应回避行业
  for (const elem of (yongJiShen.jiShen || [])) {
    const elemData = fiveElems[elem];
    if (elemData) {
      avoid.push({
        element: elem,
        industries: elemData.industries ? elemData.industries.slice(0, 3) : [],
        reason: `忌神为${elem}，回避${elem}相关行业可减少阻力`,
      });
    }
  }

  // 基于食伤推荐才华类行业
  if ((tenGodCount['食神'] || 0) + (tenGodCount['伤官'] || 0) >= 2) {
    recommended.push({
      element: '食伤',
      industries: ['创意产业', '艺术设计', '娱乐传媒', '教育培训', '咨询顾问'],
      reason: '食伤旺，才华横溢，创意类行业最能发挥潜能',
    });
  }

  return { recommended, avoid };
}

/**
 * 识别事业高低点
 * 基于格局和日主五行，推断大致事业周期
 */
function identifyCareerTrends(baziData, tenGodCount, formatAnalysis) {
  const { dayMasterElement, dayMasterYinYang } = baziData;

  // 五行旺季（日主得令的季节）
  const elementSeasons = {
    木: { peak: '春季（寅卯月）', valley: '秋季（申酉月）' },
    火: { peak: '夏季（巳午月）', valley: '冬季（亥子月）' },
    土: { peak: '四季末月（辰戌丑未）', valley: '木旺春季' },
    金: { peak: '秋季（申酉月）', valley: '夏季（巳午月）' },
    水: { peak: '冬季（亥子月）', valley: '夏季（巳午月）' },
  };

  const seasons = elementSeasons[dayMasterElement] || { peak: '日主当令月份', valley: '日主失令月份' };

  // 格局对事业影响
  const formatCareerNote = getFormatCareerNote(formatAnalysis.format);

  return {
    naturalPeak: seasons.peak,
    naturalValley: seasons.valley,
    formatNote: formatCareerNote,
    generalPattern: buildCareerPattern(tenGodCount, formatAnalysis),
  };
}

function getFormatCareerNote(format) {
  const notes = {
    '正官格': '适合稳定发展，循序渐进，不宜跳槽频繁，官运亨通期在官星得令大运',
    '七杀格': '事业起伏较大，有机会一飞冲天，需在关键时机果断出手',
    '食神格': '事业发展平稳，靠才华积累，不急于求成，财运随年龄渐佳',
    '伤官格': '事业变化多，有创业天赋，适合自主创业，不宜久居人下',
    '偏财格': '财运亨通，商业嗅觉好，适合经商，事业起伏中总能抓到机会',
    '正财格': '事业稳健，财富积累慢但扎实，适合金融、行政等稳定职业',
    '正印格': '适合学术、文化、教育领域，官印相生期事业大有作为',
    '建禄格': '靠自身努力，事业起步较晚但稳健，中年后有重大突破',
  };
  return notes[format] || '事业发展需结合大运流年综合判断';
}

function buildCareerPattern(tenGodCount, formatAnalysis) {
  const patterns = [];

  if ((tenGodCount['正官'] || 0) + (tenGodCount['七杀'] || 0) >= 2) {
    patterns.push('官杀旺，有当官或管理层的潜力，适合政府、企业管理方向');
  }
  if ((tenGodCount['食神'] || 0) + (tenGodCount['伤官'] || 0) >= 2) {
    patterns.push('食伤旺，才华横溢，适合创业或自由职业，靠专业技能立身');
  }
  if ((tenGodCount['正财'] || 0) + (tenGodCount['偏财'] || 0) >= 2) {
    patterns.push('财星旺，经商天赋好，可在商业领域取得不俗成就');
  }

  return patterns.length > 0 ? patterns.join('；') : '事业发展方向多元，需结合个人兴趣和时机把握';
}

/**
 * 生成财富积累建议
 */
function generateWealthAdvice(wealthLevel, wealthMethod, yongJiShen) {
  const advice = [];

  switch (wealthLevel.level) {
    case 'great_wealth':
      advice.push('命中有大财格局，需找准事业赛道，大胆投资，善用杠杆');
      advice.push('关键在于找到适合自己五行用神的行业，一旦入对行，财运将大幅提升');
      break;
    case 'moderate_wealth':
      advice.push('财运稳健，坚持主业的同时适当投资理财，可实现财富积累');
      advice.push('避免过度投机，稳扎稳打，财富会随年龄增长而增加');
      break;
    default:
      advice.push('勤劳节俭是主要积累方式，量入为出，避免大额投机');
      advice.push('通过提升专业技能增加收入，是最稳妥的财富增长路径');
  }

  // 用神五行建议
  if (yongJiShen.yongShen && yongJiShen.yongShen.length) {
    advice.push(`用神为${yongJiShen.yongShen.join('、')}，在用神五行对应行业中创业或投资胜算更高`);
  }

  return advice;
}

function buildSummary(data) {
  const { wealthLevel, wealthMethod, careerIndustries, careerPeakValleys, wealthAdvice } = data;
  const lines = [];
  lines.push(`【财富等级】${wealthLevel.description}`);
  lines.push(`【特征】${wealthLevel.characteristics}`);
  lines.push(`【求财方式】${wealthMethod.summary}`);
  if (wealthMethod.riskWarning.length) lines.push(`【财务风险】${wealthMethod.riskWarning.join('；')}`);
  const recIndustries = (careerIndustries.recommended || []).flatMap(r => r.industries).slice(0, 6);
  if (recIndustries.length) lines.push(`【推荐行业】${recIndustries.join('、')}`);
  lines.push(`【事业规律】${careerPeakValleys.naturalPeak}为旺盛期，${careerPeakValleys.naturalValley}需谨慎`);
  lines.push(`【格局事业】${careerPeakValleys.formatNote}`);
  lines.push(`【积累建议】${wealthAdvice.join('；')}`);
  return lines.join('\n');
}

module.exports = { analyze };
