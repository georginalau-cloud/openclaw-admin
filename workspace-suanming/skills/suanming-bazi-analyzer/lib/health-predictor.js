'use strict';

/**
 * health-predictor.js - 健康预警
 *
 * 功能：
 *   1. 基于五行偏枯预测脏腑健康
 *   2. 识别特定年份风险
 *   3. 灾厄规避建议
 *
 * 理论依据：《穷通宝鉴》五行脏腑论、《三命通会》健康预测
 *
 * 五行与脏腑对应：
 *   木 → 肝、胆
 *   火 → 心脏、小肠
 *   土 → 脾、胃
 *   金 → 肺、大肠
 *   水 → 肾、膀胱、生殖系统
 */

// 五行脏腑对应
const ELEMENT_ORGAN = {
  木: { organs: ['肝', '胆'], risk: ['肝炎', '胆囊炎', '筋骨问题', '眼睛疾患'], season: '春季' },
  火: { organs: ['心脏', '小肠'], risk: ['心脏病', '高血压', '血液循环', '焦虑失眠'], season: '夏季' },
  土: { organs: ['脾', '胃'], risk: ['脾胃不适', '消化系统', '糖尿病倾向', '肌肉疾患'], season: '季末' },
  金: { organs: ['肺', '大肠'], risk: ['呼吸道疾患', '肺炎', '皮肤问题', '大肠疾患'], season: '秋季' },
  水: { organs: ['肾', '膀胱', '生殖系统'], risk: ['肾脏问题', '泌尿系统', '骨骼问题', '内分泌失调'], season: '冬季' },
};

// 天干五行
const STEM_ELEMENT = {
  甲: '木', 乙: '木', 丙: '火', 丁: '火',
  戊: '土', 己: '土', 庚: '金', 辛: '金',
  壬: '水', 癸: '水',
};

// 地支五行
const BRANCH_ELEMENT = {
  子: '水', 丑: '土', 寅: '木', 卯: '木',
  辰: '土', 巳: '火', 午: '火', 未: '土',
  申: '金', 酉: '金', 戌: '土', 亥: '水',
};

/**
 * 健康预警分析
 * @param {object} baziData        - 四柱数据
 * @param {object} tenGodsAnalysis - 十神分析
 * @returns {object} 健康预警结果
 */
function analyze(baziData, tenGodsAnalysis) {
  const { elementCount, dayMasterElement, pillars } = baziData;

  // 五行平衡分析
  const elementBalance = analyzeElementBalance(elementCount, dayMasterElement);

  // 脏腑健康风险
  const organRisks = identifyOrganRisks(elementBalance);

  // 最弱五行的健康重点
  const primaryHealthFocus = getPrimaryHealthFocus(elementBalance.weakest);

  // 年龄阶段健康提示
  const ageHealthTips = getAgeHealthTips(dayMasterElement, elementBalance);

  // 灾厄年份识别（基于冲克）
  const disasterYears = identifyDisasterPeriods(pillars, tenGodsAnalysis);

  // 规避建议
  const avoidanceAdvice = generateAvoidanceAdvice(organRisks, elementBalance);

  return {
    elementBalance,
    organRisks,
    primaryHealthFocus,
    ageHealthTips,
    disasterYears,
    avoidanceAdvice,
    summary: buildSummary({ elementBalance, organRisks, primaryHealthFocus, ageHealthTips, disasterYears, avoidanceAdvice }),
  };
}

/**
 * 分析五行平衡状态
 */
function analyzeElementBalance(elementCount, dayMasterElement) {
  const total = Object.values(elementCount).reduce((a, b) => a + b, 0) || 1;
  const normalShare = total / 5;

  const analysis = {};
  let weakest = null, strongest = null;
  let weakestScore = Infinity, strongestScore = -Infinity;

  for (const [elem, count] of Object.entries(elementCount)) {
    const ratio = count / normalShare;
    let status;
    if (ratio < 0.3) status = 'absent';
    else if (ratio < 0.6) status = 'weak';
    else if (ratio < 1.4) status = 'balanced';
    else if (ratio < 2.0) status = 'strong';
    else status = 'excessive';

    analysis[elem] = { count, ratio: ratio.toFixed(2), status };

    if (count < weakestScore) { weakestScore = count; weakest = elem; }
    if (count > strongestScore) { strongestScore = count; strongest = elem; }
  }

  return { analysis, weakest, strongest, total };
}

/**
 * 识别脏腑健康风险
 * 五行偏枯（过少或过多）都可能引发对应脏腑问题
 */
function identifyOrganRisks(elementBalance) {
  const risks = [];

  for (const [elem, data] of Object.entries(elementBalance.analysis)) {
    const organData = ELEMENT_ORGAN[elem];
    if (!organData) continue;

    if (data.status === 'absent' || data.status === 'weak') {
      risks.push({
        element: elem,
        organs: organData.organs,
        risks: organData.risk,
        severity: data.status === 'absent' ? 'high' : 'medium',
        note: `${elem}五行过弱（力量${data.count}），${organData.organs.join('/')}功能可能较弱，需注意${organData.risk.slice(0, 2).join('、')}`,
      });
    } else if (data.status === 'excessive') {
      risks.push({
        element: elem,
        organs: organData.organs,
        risks: [`${elem}五行过旺导致的过度消耗`],
        severity: 'medium',
        note: `${elem}五行过旺，过分消耗可能导致${organData.organs.join('/')}代谢负担加重`,
      });
    }
  }

  // 按严重程度排序
  return risks.sort((a, b) => (a.severity === 'high' ? -1 : 1));
}

/**
 * 获取主要健康关注点（最弱五行）
 */
function getPrimaryHealthFocus(weakestElem) {
  if (!weakestElem) return '五行较为均衡，无明显健康短板';
  const organData = ELEMENT_ORGAN[weakestElem];
  if (!organData) return '';
  return `命中${weakestElem}五行最弱，需重点保养${organData.organs.join('/')}，预防${organData.risk.slice(0, 3).join('、')}`;
}

/**
 * 年龄阶段健康提示
 */
function getAgeHealthTips(dayMasterElem, elementBalance) {
  const tips = [];
  const organData = ELEMENT_ORGAN[dayMasterElem];

  tips.push({
    phase: '青年期（20-35岁）',
    focus: '体能充沛，注意饮食规律，避免熬夜，预防日主五行对应脏腑的早期损耗',
  });
  tips.push({
    phase: '中年期（35-50岁）',
    focus: `注意${organData ? organData.organs.join('、') : ''}健康，建议每年定期检查相关指标`,
  });
  tips.push({
    phase: '晚年期（50岁以后）',
    focus: elementBalance.weakest
      ? `${elementBalance.weakest}五行随年龄渐弱，需加强${ELEMENT_ORGAN[elementBalance.weakest].organs.join('/')}保养`
      : '维持规律生活，定期健康检查',
  });

  return tips;
}

/**
 * 识别灾厄年份/时期（基于日支冲克）
 */
function identifyDisasterPeriods(pillars, tenGodsAnalysis) {
  const dayBranch   = pillars.day.branch;
  const yearBranch  = pillars.year.branch;
  const monthBranch = pillars.month.branch;

  // 地支六冲
  const chongMap = {
    子: '午', 午: '子',
    丑: '未', 未: '丑',
    寅: '申', 申: '寅',
    卯: '酉', 酉: '卯',
    辰: '戌', 戌: '辰',
    巳: '亥', 亥: '巳',
  };

  const dayChong   = chongMap[dayBranch];
  const yearChong  = chongMap[yearBranch];

  const risks = [];

  if (dayChong) {
    risks.push({
      type: '日支冲',
      trigger: `流年逢${dayChong}年`,
      note: `流年地支${dayChong}与日支${dayBranch}相冲，该年份婚姻、健康需格外注意，宜低调处事`,
    });
  }

  if (tenGodsAnalysis.strengthAnalysis.strength === 'very_weak') {
    risks.push({
      type: '日主极弱',
      trigger: '官杀旺盛的流年',
      note: '日主本弱，逢官杀旺流年（克日主五行）需特别注意健康与压力管理',
    });
  }

  risks.push({
    type: '一般规律',
    trigger: `${dayBranch}对应冲年、本命年`,
    note: '本命年（与年支相同年份）及日支冲年是命理常见不稳定时段，建议保守处事',
  });

  return risks;
}

/**
 * 生成灾厄规避建议
 */
function generateAvoidanceAdvice(organRisks, elementBalance) {
  const advice = [];

  // 饮食调养
  const weakElem = elementBalance.weakest;
  if (weakElem) {
    const dietMap = {
      木: '多食绿色蔬菜、护肝食品，如菠菜、芦笋、绿茶',
      火: '适当食用红色食物，如番茄、红枣，注意心脏健康',
      土: '多食黄色食物，如南瓜、玉米，注意脾胃调养',
      金: '多食白色食物，如梨、百合、白木耳，保护肺部',
      水: '多食黑色食物，如黑豆、黑芝麻，保护肾脏',
    };
    advice.push(`饮食调养：${dietMap[weakElem] || '均衡饮食，避免偏食'}`);
  }

  // 运动建议
  advice.push('坚持适量运动，推荐与日主五行相符的运动方式');

  // 精神调养
  advice.push('注意情绪管理，避免长期过度劳累，定期休假放松');

  // 医疗建议
  const highRiskOrgans = organRisks
    .filter(r => r.severity === 'high')
    .flatMap(r => r.organs);
  if (highRiskOrgans.length) {
    advice.push(`重点体检项目：每年检查${highRiskOrgans.join('、')}相关指标`);
  }

  return advice;
}

function buildSummary(data) {
  const { elementBalance, organRisks, primaryHealthFocus, ageHealthTips, disasterYears, avoidanceAdvice } = data;
  const lines = [];

  lines.push(`【五行健康概况】最弱：${elementBalance.weakest || '无'} | 最强：${elementBalance.strongest || '无'}`);
  lines.push(`【重点健康关注】${primaryHealthFocus}`);

  if (organRisks.length) {
    lines.push('【脏腑风险】');
    for (const r of organRisks.slice(0, 3)) {
      lines.push(`  • ${r.note}`);
    }
  }

  lines.push('【年龄健康提示】');
  for (const tip of ageHealthTips) {
    lines.push(`  ${tip.phase}：${tip.focus}`);
  }

  if (disasterYears.length) {
    lines.push('【特定风险时段】');
    for (const d of disasterYears.slice(0, 2)) {
      lines.push(`  • ${d.note}`);
    }
  }

  lines.push(`【规避建议】${avoidanceAdvice.slice(0, 3).join('；')}`);

  return lines.join('\n');
}

module.exports = { analyze };
