'use strict';

/**
 * character-profiler.js - 性格特质深度画像
 *
 * 功能：
 *   1. 基于十神分布生成显性性格（外在表现）
 *   2. 基于日主和格局生成隐性性格（内心渴望）
 *   3. 分析优缺点
 *   4. 挖掘天赋与性格缺陷
 *
 * 理论依据：《滴天髓》性情论、十神性格特征
 */

const path = require('path');
const fs   = require('fs');

// 加载十神特征库
let TEN_GODS_TRAITS = {};
try {
  TEN_GODS_TRAITS = JSON.parse(
    fs.readFileSync(path.join(__dirname, '..', 'data', 'ten-gods-traits.json'), 'utf8')
  ).ten_gods || {};
} catch { /* 使用内置备选 */ }

// 日主天干性格基调
const DAY_MASTER_BASE_PERSONALITY = {
  甲: { base: '参天大树，正直坚毅', trait: '有主见，重原则，领导力强，但有时固执' },
  乙: { base: '藤蔓花草，柔韧灵活', trait: '聪明变通，善于借力，外柔内刚，情感细腻' },
  丙: { base: '太阳普照，热情开朗', trait: '开朗活泼，充满活力，慷慨豪爽，但有时粗心' },
  丁: { base: '蜡烛灯火，细腻温柔', trait: '温柔细心，艺术天赋，感情丰富，但有时优柔' },
  戊: { base: '厚土大山，稳重可靠', trait: '踏实稳重，可靠诚信，包容大度，但有时保守' },
  己: { base: '田园沃土，滋养万物', trait: '勤勉细致，善于积累，顾家持家，但有时小气' },
  庚: { base: '钢刀铁剑，果断刚强', trait: '果断刚强，有执行力，重义气，但有时冲动' },
  辛: { base: '珠宝玉石，精致完美', trait: '追求完美，敏感细腻，艺术气质，但有时多虑' },
  壬: { base: '大海江河，智慧广博', trait: '聪明灵活，博学多才，处世圆融，但有时多变' },
  癸: { base: '雨露细流，滋润内敛', trait: '内敛深沉，直觉敏锐，感情细腻，但有时多疑' },
};

/**
 * 生成性格特质画像
 * @param {object} baziData         - 四柱数据
 * @param {object} tenGodsAnalysis  - 十神分析
 * @param {object} formatAnalysis   - 格局分析
 * @returns {object} 性格画像
 */
function analyze(baziData, tenGodsAnalysis, formatAnalysis) {
  const { dayMaster, dayMasterElement, dayMasterYinYang } = baziData;
  const { yongJiShen, strengthAnalysis } = tenGodsAnalysis;
  const tenGodCount = (tenGodsAnalysis.tenGods || {}).tenGodCount || {};

  // 日主基础性格
  const basePersonality = DAY_MASTER_BASE_PERSONALITY[dayMaster] || { base: dayMaster, trait: '' };

  // 主导十神（出现最多的）
  const dominantTenGod = getDominantTenGod(tenGodCount);

  // 月令十神（最重要的性格影响）
  const monthTenGod = tenGodsAnalysis.tenGods.month.stem;
  const monthBranchTenGod = tenGodsAnalysis.tenGods.month.branch;

  // 显性性格（外在表现）
  const visiblePersonality = buildVisiblePersonality(dayMaster, dayMasterElement, dominantTenGod, monthTenGod, tenGodCount);

  // 隐性性格（内心渴望）
  const hiddenPersonality = buildHiddenPersonality(dayMaster, dayMasterElement, tenGodsAnalysis.strengthAnalysis, formatAnalysis);

  // 优缺点
  const strengths = buildStrengths(dayMaster, dominantTenGod, monthTenGod, tenGodCount);
  const weaknesses = buildWeaknesses(dayMaster, dominantTenGod, tenGodCount);

  // 天赋
  const talents = buildTalents(dayMaster, dayMasterElement, tenGodCount, formatAnalysis);

  // 性格缺陷
  const defects = buildDefects(dayMaster, dayMasterElement, tenGodCount, tenGodsAnalysis.strengthAnalysis);

  return {
    dayMasterSummary: `${dayMaster}日主（${dayMasterElement}${dayMasterYinYang}）：${basePersonality.base}`,
    basePersonality: basePersonality.trait,
    visiblePersonality,
    hiddenPersonality,
    strengths,
    weaknesses,
    talents,
    defects,
    summary: buildSummary({
      dayMaster, basePersonality: basePersonality.trait, visiblePersonality, hiddenPersonality,
      strengths, weaknesses, talents, defects,
    }),
  };
}

/**
 * 获取主导十神（出现最多的十神，排除比肩劫财）
 */
function getDominantTenGod(tenGodCount) {
  const sorted = Object.entries(tenGodCount)
    .sort((a, b) => b[1] - a[1]);
  return sorted.length > 0 ? sorted[0][0] : null;
}

/**
 * 构建显性性格（别人眼中的你）
 */
function buildVisiblePersonality(dayMaster, dayMasterElem, dominantTenGod, monthTenGod, tenGodCount) {
  const traits = [];
  const baseInfo = DAY_MASTER_BASE_PERSONALITY[dayMaster];
  if (baseInfo) traits.push(baseInfo.trait);

  // 月令十神的影响
  const monthTraits = getTenGodOuterTrait(monthTenGod);
  if (monthTraits) traits.push(monthTraits);

  // 主导十神影响
  if (dominantTenGod && dominantTenGod !== monthTenGod) {
    const domTraits = getTenGodOuterTrait(dominantTenGod);
    if (domTraits) traits.push(domTraits);
  }

  // 五行偏旺影响
  const elemTraits = getElementOuterTrait(dayMasterElem);
  if (elemTraits) traits.push(elemTraits);

  return traits.join('；');
}

/**
 * 构建隐性性格（内心真实渴望）
 */
function buildHiddenPersonality(dayMaster, dayMasterElem, strengthAnalysis, formatAnalysis) {
  const traits = [];

  // 日主强弱影响内心
  if (strengthAnalysis.isStrong) {
    traits.push('内心充满自信，渴望独立自主，不甘受人支配，追求在自己的领域中出类拔萃');
  } else {
    traits.push('内心渴望被认可和支持，需要安全感，希望有依靠，在意他人的看法和评价');
  }

  // 格局影响内心渴望
  const formatInnerDesires = getFormatInnerDesire(formatAnalysis.format);
  if (formatInnerDesires) traits.push(formatInnerDesires);

  // 日主本质内心
  const innerDesire = getDayMasterInnerDesire(dayMaster);
  if (innerDesire) traits.push(innerDesire);

  return traits.join('；');
}

function getDayMasterInnerDesire(dayMaster) {
  const desires = {
    甲: '渴望成就感和社会认可，希望成为领域中的领导者和榜样',
    乙: '渴望和谐稳定的环境，希望在温柔中发挥自己的影响力',
    丙: '渴望展现自我，希望成为众人关注的焦点，内心需要被肯定',
    丁: '渴望深度的情感连接，希望被理解和珍视，内心世界丰富',
    戊: '渴望稳定和安全感，希望积累实质的成就，重视家庭和事业的稳固',
    己: '渴望被需要的感觉，希望照顾好身边的人，在细节中找到意义',
    庚: '渴望被尊重和认可自己的能力，希望在竞争中脱颖而出',
    辛: '渴望完美和精致，希望在细节中创造美好，内心敏感而深刻',
    壬: '渴望广阔的空间和自由，希望探索未知，内心深邃如大海',
    癸: '渴望深层的情感和智慧的探索，希望被真正理解，直觉灵敏',
  };
  return desires[dayMaster] || '';
}

function getFormatInnerDesire(format) {
  const desires = {
    '正官格': '内心重视社会规范和秩序，渴望被认可的正统地位',
    '七杀格': '内心充满斗志，渴望权威和控制感，不服输',
    '食神格': '内心追求享受和创作的乐趣，渴望自由表达',
    '伤官格': '内心追求极致完美，渴望突破束缚，拒绝平庸',
    '正财格': '内心渴望稳定的物质积累，重视务实和安全感',
    '偏财格': '内心渴望丰富的社交圈和物质享受，喜欢刺激',
    '正印格': '内心渴望知识和精神的提升，重视道德修养',
    '偏印格': '内心追求独特和深邃，渴望被理解的孤独智者',
    '建禄格': '内心渴望独立和自强，靠自己的努力实现价值',
  };
  return desires[format] || '';
}

function getTenGodOuterTrait(tenGod) {
  const traits = {
    比肩: '外表独立自信，给人可靠感，但有时显得固执不听劝',
    劫财: '外表豪爽义气，人缘好，但有时冲动难控',
    食神: '外表温和开朗，善于表达，才华自然流露',
    伤官: '外表才华出众，个性鲜明，有时显得傲慢',
    偏财: '外表大方爽朗，财运显著，人脉广泛',
    正财: '外表踏实可靠，勤俭持家，理财有道',
    七杀: '外表威严强势，有领导气场，给人压迫感',
    正官: '外表稳重正直，遵纪守法，威严可靠',
    偏印: '外表神秘内敛，思维独特，不善社交',
    正印: '外表温文儒雅，学识渊博，给人温暖感',
  };
  return traits[tenGod] || '';
}

function getElementOuterTrait(element) {
  const traits = {
    木: '带有仁慈宽厚的气质，给人温和正直的感觉',
    火: '带有热情活泼的气质，给人开朗积极的感觉',
    土: '带有稳重诚信的气质，给人可靠踏实的感觉',
    金: '带有刚强果断的气质，给人干练利落的感觉',
    水: '带有灵活智慧的气质，给人聪明通透的感觉',
  };
  return traits[element] || '';
}

function buildStrengths(dayMaster, dominantTenGod, monthTenGod, tenGodCount) {
  const strengths = [];
  const baseInfo = DAY_MASTER_BASE_PERSONALITY[dayMaster];

  // 日主基础优点
  const dayStrengths = {
    甲: ['领导力强', '意志坚定', '正直有原则'],
    乙: ['柔韧变通', '善于借力', '细心体贴'],
    丙: ['热情开朗', '慷慨豪爽', '活力四射'],
    丁: ['细腻温柔', '艺术天赋', '感情丰富'],
    戊: ['稳重可靠', '包容大度', '踏实诚信'],
    己: ['细心勤勉', '持家有道', '善于积累'],
    庚: ['果断执行', '讲义气', '处理问题果断'],
    辛: ['追求完美', '艺术气质', '精益求精'],
    壬: ['聪明灵活', '博学多才', '处世圆融'],
    癸: ['直觉敏锐', '深谋远虑', '感情细腻'],
  };
  if (dayStrengths[dayMaster]) strengths.push(...dayStrengths[dayMaster]);

  // 主导十神优点
  const dominantTenGodTraits = TEN_GODS_TRAITS[dominantTenGod];
  if (dominantTenGodTraits && dominantTenGodTraits.personality && dominantTenGodTraits.personality.positive) {
    strengths.push(...dominantTenGodTraits.personality.positive.slice(0, 2));
  }

  return [...new Set(strengths)].slice(0, 6);
}

function buildWeaknesses(dayMaster, dominantTenGod, tenGodCount) {
  const weaknesses = [];

  const dayWeaknesses = {
    甲: ['固执己见', '不善借助他人'],
    乙: ['优柔寡断', '依赖性较强'],
    丙: ['粗心大意', '难以坚持'],
    丁: ['情绪化', '过于敏感'],
    戊: ['保守迟钝', '变化适应慢'],
    己: ['心胸偏小', '过于在意细节'],
    庚: ['冲动莽撞', '有时显得强硬'],
    辛: ['多虑消极', '完美主义过强'],
    壬: ['多变不稳', '有时不踏实'],
    癸: ['多疑猜忌', '情绪起伏'],
  };
  if (dayWeaknesses[dayMaster]) weaknesses.push(...dayWeaknesses[dayMaster]);

  // 主导十神缺点
  const dominantTenGodTraits = TEN_GODS_TRAITS[dominantTenGod];
  if (dominantTenGodTraits && dominantTenGodTraits.personality && dominantTenGodTraits.personality.negative) {
    weaknesses.push(...dominantTenGodTraits.personality.negative.slice(0, 2));
  }

  return [...new Set(weaknesses)].slice(0, 5);
}

function buildTalents(dayMaster, dayMasterElem, tenGodCount, formatAnalysis) {
  const talents = [];

  const elemTalents = {
    木: ['文学创作', '教育传授', '医疗慈善'],
    火: ['演讲表达', '艺术表演', '科技创新'],
    土: ['管理经营', '土地建筑', '积累理财'],
    金: ['精密执行', '法律裁判', '金融财务'],
    水: ['智谋策划', '沟通谈判', '哲学研究'],
  };
  if (elemTalents[dayMasterElem]) talents.push(...elemTalents[dayMasterElem]);

  // 格局对应天赋
  const formatTalents = {
    '食神格': ['艺术天赋', '口才出众', '享受美食'],
    '伤官格': ['创新思维', '艺术才华', '独特见解'],
    '正印格': ['学术研究', '文学创作', '教育'],
    '偏印格': ['玄学直觉', '深层研究', '独创想法'],
    '七杀格': ['军事领导', '竞技体育', '危机处理'],
    '正官格': ['管理组织', '政务行政', '稳定发展'],
  };
  const fmtTalents = formatTalents[formatAnalysis.format];
  if (fmtTalents) talents.push(...fmtTalents);

  return [...new Set(talents)].slice(0, 5);
}

function buildDefects(dayMaster, dayMasterElem, tenGodCount, strengthAnalysis) {
  const defects = [];

  if (strengthAnalysis.strength === 'very_strong') {
    defects.push('日主过强，有时过于自我，难以接受他人建议');
  } else if (strengthAnalysis.strength === 'very_weak') {
    defects.push('日主过弱，容易缺乏自信，过度依赖外界支持');
  }

  // 十神偏颇造成的缺陷
  if ((tenGodCount['七杀'] || 0) >= 2) {
    defects.push('官杀过多，性情较为急躁，容易与他人产生冲突');
  }
  if ((tenGodCount['伤官'] || 0) >= 2) {
    defects.push('伤官太多，容易不服管教，与权威人士摩擦多');
  }
  if ((tenGodCount['偏印'] || 0) >= 2) {
    defects.push('偏印过旺，有时过于孤僻，不善与他人合作');
  }
  if ((tenGodCount['劫财'] || 0) >= 2) {
    defects.push('劫财多现，财运不稳，容易因冲动损失钱财');
  }

  return defects.slice(0, 4);
}

function buildSummary(data) {
  const { dayMaster, basePersonality, visiblePersonality, hiddenPersonality, strengths, weaknesses, talents, defects } = data;
  const lines = [];
  lines.push(`【性格概述】${dayMaster}日主，${basePersonality}`);
  lines.push(`【显性性格】${visiblePersonality}`);
  lines.push(`【隐性性格】${hiddenPersonality}`);
  lines.push(`【核心优点】${strengths.join('、')}`);
  lines.push(`【主要缺点】${weaknesses.join('、')}`);
  lines.push(`【天赋领域】${talents.join('、')}`);
  if (defects.length) lines.push(`【性格缺陷】${defects.join('；')}`);
  return lines.join('\n');
}

module.exports = { analyze };
