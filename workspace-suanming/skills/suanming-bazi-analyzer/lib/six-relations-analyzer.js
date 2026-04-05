'use strict';

/**
 * six-relations-analyzer.js - 六亲关系分析
 *
 * 功能：
 *   1. 父母缘分与祖荫分析
 *   2. 婚姻感情分析（配偶特征、婚姻稳定性、二婚风险）
 *   3. 子女情况分析
 *   4. 兄弟手足分析
 *   5. 晚年福气
 *
 * 理论依据：《三命通会》六亲十神论命、《渊海子平》
 *
 * 六亲对应十神：
 *   父：偏财（正财亦可）
 *   母：正印（偏印亦有影响）
 *   配偶（男）：正财（偏财亦有关）
 *   配偶（女）：正官（七杀亦有关）
 *   子女（男）：七杀（正官）
 *   子女（女）：食神（伤官）
 *   兄弟：比肩劫财
 */

/**
 * 分析六亲关系
 * @param {object} baziData        - 四柱数据
 * @param {object} tenGodsAnalysis - 十神分析
 * @param {string} gender          - 性别 'male' | 'female'
 * @returns {object} 六亲分析结果
 */
function analyze(baziData, tenGodsAnalysis, gender) {
  const { pillars, dayMaster, dayMasterElement } = baziData;
  const tenGodCount = (tenGodsAnalysis.tenGods || {}).tenGodCount || {};
  const { yongJiShen } = tenGodsAnalysis;

  const isMale = gender === 'male';

  // 父母缘
  const parents = analyzeParents(tenGodCount, pillars, dayMasterElement);

  // 婚姻感情
  const marriage = analyzeMarriage(tenGodCount, pillars, dayMaster, dayMasterElement, isMale, yongJiShen);

  // 子女
  const children = analyzeChildren(tenGodCount, pillars, dayMasterElement, isMale);

  // 兄弟手足
  const siblings = analyzeSiblings(tenGodCount, pillars);

  // 晚年福气（时柱）
  const laterLife = analyzeLaterLife(pillars, tenGodsAnalysis);

  return {
    parents,
    marriage,
    children,
    siblings,
    laterLife,
    summary: buildSummary({ parents, marriage, children, siblings, laterLife }),
  };
}

/**
 * 分析父母缘分
 * 父：年柱或偏财星；母：正印星；年柱代表祖荫
 */
function analyzeParents(tenGodCount, pillars, dayMasterElem) {
  const fatherStar = (tenGodCount['偏财'] || 0) + (tenGodCount['正财'] || 0);
  const motherStar = (tenGodCount['正印'] || 0) + (tenGodCount['偏印'] || 0);

  const fatherBond = assessRelationship(fatherStar, '偏财正财', '父缘');
  const motherBond = assessRelationship(motherStar, '正印偏印', '母缘');

  // 年柱代表祖荫（简化：年柱天干为正官、正印、偏印者祖荫较好）
  const yearStemHint = pillars.year.stem;

  return {
    fatherBond: fatherBond.text,
    motherBond: motherBond.text,
    ancestralBlessing: assessAncestralBlessing(pillars),
    detail: `父缘${fatherBond.level}，母缘${motherBond.level}。${assessAncestralBlessing(pillars)}`,
  };
}

function assessRelationship(count, starName, name) {
  if (count === 0) return { level: '淡薄', text: `${name}淡薄，与父/母之间可能缘分较浅，或早年分离` };
  if (count === 1) return { level: '普通', text: `${name}正常，与父/母关系平和，有一定照应` };
  if (count >= 2) return { level: '深厚', text: `${name}深厚，父/母感情深，受父/母荫护` };
  return { level: '普通', text: `${name}普通` };
}

function assessAncestralBlessing(pillars) {
  const yearStem = pillars.year.stem;
  const auspiciousStems = ['甲', '丙', '戊', '壬', '庚']; // 阳干一般气势较足
  if (auspiciousStems.includes(yearStem)) {
    return '年柱阳干，祖上有一定根基，能得到一定荫护';
  }
  return '年柱阴干，祖上根基一般，主要靠自身努力';
}

/**
 * 分析婚姻感情
 * 男：正财为妻，日支为妻宫
 * 女：正官为夫，日支为夫宫
 */
function analyzeMarriage(tenGodCount, pillars, dayMaster, dayMasterElem, isMale, yongJiShen) {
  let spouseStar, adversaryStar;
  if (isMale) {
    spouseStar = (tenGodCount['正财'] || 0);
    adversaryStar = (tenGodCount['偏财'] || 0);
  } else {
    spouseStar = (tenGodCount['正官'] || 0);
    adversaryStar = (tenGodCount['七杀'] || 0);
  }

  // 配偶特征（基于日支藏干）
  const spouseFeatures = analyzeSpouseFeatures(pillars, dayMaster, isMale);

  // 婚姻稳定性
  const stability = assessMarriageStability(spouseStar, adversaryStar, tenGodCount, isMale);

  // 二婚风险
  const remarriageRisk = assessRemarriageRisk(adversaryStar, tenGodCount, isMale);

  // 婚配建议
  const compatibleElements = getCompatibleElement(dayMasterElem, yongJiShen);

  return {
    spouseFeatures,
    stability: stability.text,
    remarriageRisk: remarriageRisk.text,
    compatibleElements,
    bestMarriageAge: estimateBestMarriageAge(pillars),
    detail: buildMarriageDetail(isMale, spouseStar, adversaryStar, stability, remarriageRisk, spouseFeatures),
  };
}

function analyzeSpouseFeatures(pillars, dayMaster, isMale) {
  const dayBranch = pillars.day.branch;
  const branchFeatures = {
    子: '聪明伶俐，水性灵活，适应力强',
    丑: '踏实稳重，勤劳持家，但有时固执',
    寅: '豪爽仗义，事业心强，有领导力',
    卯: '温柔体贴，感情细腻，有艺术气质',
    辰: '稳重包容，踏实可靠，大局观好',
    巳: '聪明干练，有主见，事业心强',
    午: '热情开朗，情感丰富，但有时冲动',
    未: '温和善良，顾家细心，但有时优柔',
    申: '聪明机智，行动力强，财务能力好',
    酉: '精致优雅，追求完美，有艺术品味',
    戌: '忠诚可靠，重情重义，踏实勤劳',
    亥: '聪慧深沉，独立性强，有神秘气质',
  };
  return branchFeatures[dayBranch] || '配偶特征需结合整体命局分析';
}

function assessMarriageStability(spouseStar, adversaryStar, tenGodCount, isMale) {
  const injuryStar = (tenGodCount['伤官'] || 0);
  const siblingStar = (tenGodCount['比肩'] || 0) + (tenGodCount['劫财'] || 0);

  if (adversaryStar >= 2) {
    return { level: 'unstable', text: isMale ? '偏财多见，感情较为复杂，婚姻不够稳定，需注意' : '七杀多见，婚姻有波折，需要更多磨合' };
  }
  if (!isMale && injuryStar >= 2) {
    return { level: 'unstable', text: '伤官过旺，女命伤官重，婚姻感情多有波折，丈夫缘薄' };
  }
  if (spouseStar === 1) {
    return { level: 'stable', text: '配偶星得宜，婚姻相对稳定，感情平和' };
  }
  if (spouseStar === 0) {
    return { level: 'weak', text: '配偶星不现，感情缘分较淡，婚姻较晚或需主动经营' };
  }
  return { level: 'normal', text: '婚姻状态正常，有一定波折但整体稳定' };
}

function assessRemarriageRisk(adversaryStar, tenGodCount, isMale) {
  let risk = 0;
  risk += adversaryStar;
  if (!isMale) risk += (tenGodCount['伤官'] || 0);
  risk += Math.floor(((tenGodCount['劫财'] || 0)) / 2);

  if (risk >= 3) return { level: 'high', text: '二婚或感情曲折的风险较高，感情路上需多加谨慎' };
  if (risk >= 2) return { level: 'mid',  text: '有一定感情波折，不排除二婚可能，需珍惜缘分' };
  return { level: 'low', text: '二婚风险较低，感情相对单纯稳定' };
}

function getCompatibleElement(dayMasterElem, yongJiShen) {
  const elemNames = {
    木: '属虎兔（寅卯）的伴侣',
    火: '属马蛇（午巳）的伴侣',
    土: '属牛龙羊狗（丑辰未戌）的伴侣',
    金: '属猴鸡（申酉）的伴侣',
    水: '属鼠猪（子亥）的伴侣',
  };
  const yong = (yongJiShen.yongShen || [])[0];
  const compatElem = elemNames[yong] || '';
  return compatElem ? `用神为${yong}，建议选择${compatElem}，五行相辅相成` : '参考用神五行选择合适的伴侣';
}

function estimateBestMarriageAge(pillars) {
  // 简化推算：根据月支估算
  const monthBranch = pillars.month.branch;
  const earlyBranches = ['子', '丑', '寅', '卯'];
  const midBranches   = ['辰', '巳', '午', '未'];
  if (earlyBranches.includes(monthBranch)) return '25-28岁婚配较为适宜';
  if (midBranches.includes(monthBranch)) return '28-32岁婚配较为适宜';
  return '30-35岁婚配较为适宜';
}

function buildMarriageDetail(isMale, spouseStar, adversaryStar, stability, remarriageRisk, spouseFeatures) {
  const lines = [];
  lines.push(`配偶宫特征：${spouseFeatures}`);
  lines.push(`婚姻稳定性：${stability.text}`);
  lines.push(`二婚风险：${remarriageRisk.text}`);
  return lines.join('；');
}

/**
 * 分析子女情况
 * 男命：七杀正官为子女；女命：食神伤官为子女
 */
function analyzeChildren(tenGodCount, pillars, dayMasterElem, isMale) {
  let childStar;
  if (isMale) {
    childStar = (tenGodCount['七杀'] || 0) + (tenGodCount['正官'] || 0);
  } else {
    childStar = (tenGodCount['食神'] || 0) + (tenGodCount['伤官'] || 0);
  }

  const hourPillar = pillars.hour;

  let childBond, childCount;
  if (childStar === 0) {
    childBond = '子女缘薄，子女数量偏少，或子女早离身边';
    childCount = '1-2个子女，缘分一般';
  } else if (childStar === 1) {
    childBond = '子女缘普通，与子女关系平和，有所照应';
    childCount = '1-2个子女';
  } else if (childStar >= 2) {
    childBond = '子女缘较深，子女数量较多，与子女感情深厚';
    childCount = '2-3个子女，子女较孝顺';
  } else {
    childBond = '子女缘普通';
    childCount = '子女数量正常';
  }

  return {
    childBond,
    childCount,
    detail: `${childBond}，${childCount}。时柱为子女晚年运势指标，需结合大运流年综合判断。`,
  };
}

/**
 * 分析兄弟手足
 * 比肩劫财代表兄弟
 */
function analyzeSiblings(tenGodCount, pillars) {
  const siblingStar = (tenGodCount['比肩'] || 0) + (tenGodCount['劫财'] || 0);
  if (siblingStar === 0) return { detail: '比劫不现，兄弟手足缘薄，或各自独立，彼此往来不多' };
  if (siblingStar >= 2) return { detail: '比劫较多，兄弟手足较多，感情尚好，但也有竞争摩擦' };
  return { detail: '比劫适中，与兄弟手足关系平和，互有往来' };
}

/**
 * 分析晚年福气（时柱为晚年宫）
 */
function analyzeLaterLife(pillars, tenGodsAnalysis) {
  const hourStemTenGod  = tenGodsAnalysis.tenGods.hour.stem;
  const hourBranchTenGod = tenGodsAnalysis.tenGods.hour.branch;

  const auspiciousTenGods = ['食神', '正财', '正官', '正印'];
  const isAuspicious = auspiciousTenGods.includes(hourStemTenGod) || auspiciousTenGods.includes(hourBranchTenGod);

  if (isAuspicious) {
    return {
      quality: '晚景可期',
      detail: `时柱现${hourStemTenGod}/${hourBranchTenGod}，晚年生活安稳，子女孝顺，晚年福气较好`,
    };
  }

  return {
    quality: '晚年需自立',
    detail: `时柱现${hourStemTenGod}/${hourBranchTenGod}，晚年需靠自身努力和积累，子女缘分一般，建议早做养老规划`,
  };
}

function buildSummary(data) {
  const { parents, marriage, children, siblings, laterLife } = data;
  const lines = [];
  lines.push(`【父母缘】${parents.detail}`);
  lines.push(`【婚姻感情】${marriage.detail}`);
  lines.push(`【最佳婚龄】${marriage.bestMarriageAge}；${marriage.compatibleElements}`);
  lines.push(`【子女情况】${children.detail}`);
  lines.push(`【兄弟手足】${siblings.detail}`);
  lines.push(`【晚年福气】${laterLife.detail}`);
  return lines.join('\n');
}

module.exports = { analyze };
