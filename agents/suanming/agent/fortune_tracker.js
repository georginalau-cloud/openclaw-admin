'use strict';

/**
 * fortune_tracker.js - 五运追踪对话系统
 *
 * 功能：
 *   1. 解析用户的五运追踪问询（例如："分析第2个大运的感情"、"2026年财运如何"）
 *   2. 调用五运分析服务（通过 Python bazi_analyzer）
 *   3. 格式化五维度深度分析结果
 *   4. 支持后续追问（流月、流日逐级追踪）
 *
 * 支持的查询格式：
 *   - "分析第N个大运的[感情/财运/子运/禄运/寿运]"
 *   - "[感情/财运/子运/禄运/寿运]运怎么样"（使用当前大运）
 *   - "YYYY年[感情/财运/子运/禄运/寿运]如何"（指定流年）
 *   - "当前大运[感情/财运/子运/禄运/寿运]分析"
 *   - "所有维度" / "全部分析"（五维度汇总）
 */

const { execFile } = require('child_process');
const path = require('path');

const logger = console;

// 工作空间路径（与 core.js 保持一致）
const WORKSPACE_PATH = process.env.WORKSPACE_PATH
  || path.join(process.env.HOME || '/root', '.openclaw', 'workspace-suanming');

const BAZI_ANALYZER_PATH = path.join(
  WORKSPACE_PATH, 'skills', 'suanming-bazi-analyzer', 'bazi_analyzer.py'
);

// ─── 维度关键词映射 ─────────────────────────────────────────────────────────

const DIMENSION_KEYWORDS = {
  intimate: ['感情', '妻', '夫', '婚姻', '桃花', '爱情', '恋爱', '配偶', '情缘', '情感'],
  wealth:   ['财运', '财', '钱财', '收入', '投资', '偏财', '正财', '赚钱', '财富', '财星'],
  children: ['子运', '子女', '孩子', '儿女', '后代', '子嗣', '生育', '育儿'],
  official: ['禄运', '官运', '事业', '仕途', '职位', '晋升', '工作', '官禄', '职业'],
  longevity: ['寿运', '健康', '寿元', '身体', '体质', '养生', '长寿', '疾病', '病灾'],
};

const DIMENSION_LABELS = {
  intimate:  '感情运',
  wealth:    '财运',
  children:  '子运',
  official:  '禄运',
  longevity: '寿运',
};

// 序数词映射
const ORDINAL_MAP = {
  '第一': 1, '第1': 1, '一': 1,
  '第二': 2, '第2': 2, '二': 2,
  '第三': 3, '第3': 3, '三': 3,
  '第四': 4, '第4': 4, '四': 4,
  '第五': 5, '第5': 5, '五': 5,
  '第六': 6, '第6': 6, '六': 6,
  '第七': 7, '第7': 7, '七': 7,
  '第八': 8, '第8': 8, '八': 8,
  '第九': 9, '第9': 9, '九': 9,
  '第十': 10, '第10': 10, '十': 10,
};

// ─── 查询解析 ───────────────────────────────────────────────────────────────

/**
 * 解析维度关键词
 * @param {string} query - 用户输入
 * @returns {string|null} - dimension key 或 null（表示所有维度）
 */
function parseDimension(query) {
  // 检查是否要分析所有维度
  if (/所有|全部|五运|所有维度|全面分析/.test(query)) {
    return 'all';
  }

  for (const [dim, keywords] of Object.entries(DIMENSION_KEYWORDS)) {
    for (const kw of keywords) {
      if (query.includes(kw)) {
        return dim;
      }
    }
  }
  return null;
}

/**
 * 从查询中提取时间帧（大运序号 或 流年年份）
 * @param {string} query - 用户输入
 * @returns {{ type: 'dayun'|'liunya'|'current', index?: number, year?: number }}
 */
function extractTimeFrame(query) {
  // 检查流年年份（4位数字）
  const yearMatch = query.match(/(\d{4})\s*年/);
  if (yearMatch) {
    return { type: 'liunya', year: parseInt(yearMatch[1], 10) };
  }

  // 检查"当前大运"
  if (/当前|现在|目前/.test(query)) {
    return { type: 'current' };
  }

  // 检查大运序号
  for (const [word, idx] of Object.entries(ORDINAL_MAP)) {
    if (query.includes(word)) {
      // 判断是否是指大运（含"大运"字样）
      if (query.includes('大运') || query.includes('运程')) {
        return { type: 'dayun', index: idx };
      }
      // 如果只是数字但结合上下文是大运
      if (idx <= 10) {
        return { type: 'dayun', index: idx };
      }
    }
  }

  // 默认：当前大运
  return { type: 'current' };
}

// ─── 运势分析结果格式化 ─────────────────────────────────────────────────────

/**
 * 格式化单个维度的深度分析结果
 * @param {object} dimResult - 来自 FiveYunAnalyzer 的维度分析结果
 * @param {object} dayunInfo - 大运基础信息
 * @returns {string}
 */
function formatSingleDimension(dimResult, dayunInfo) {
  const lines = [];
  const label = DIMENSION_LABELS[dimResult.dimension] || dimResult.label || dimResult.dimension;
  const gz = dimResult.dayun_gz || dayunInfo.gz || '';
  const ageStart = dayunInfo.age_start !== undefined ? dayunInfo.age_start : '';
  const wangshuai = dimResult.wangshuai || '';
  const nayin = dimResult.nayin || '';

  lines.push(`🔮 ${label}分析（${ageStart}岁 ${gz} ${wangshuai}）`);
  lines.push('─'.repeat(44));
  lines.push(`大运：${gz}（${wangshuai}）`);
  if (nayin) {
    lines.push(`纳音：${nayin}`);
  }
  lines.push('');
  lines.push(`总体：${dimResult.overall || ''}`);
  lines.push(`评分：${dimResult.score || 0}/100`);
  lines.push('');

  const keyPoints = dimResult.key_points || [];
  if (keyPoints.length > 0) {
    lines.push('💡 分析要点：');
    keyPoints.forEach((pt, i) => {
      lines.push(`${i + 1}. ${pt}`);
    });
    lines.push('');
  }

  lines.push(`📌 建议：${dimResult.advice || ''}`);

  return lines.join('\n');
}

/**
 * 格式化五维度汇总分析
 * @param {object} allDims - 五维度分析结果（来自 analyze_all_dimensions）
 * @param {object} dayunInfo - 大运基础信息
 * @returns {string}
 */
function formatAllDimensions(allDims, dayunInfo) {
  const lines = [];
  const gz = dayunInfo.gz || '';
  const ageStart = dayunInfo.age_start !== undefined ? dayunInfo.age_start : '';
  const ageEnd = dayunInfo.age_end !== undefined ? dayunInfo.age_end : '';
  const yearStart = dayunInfo.year_start || '';
  const yearEnd = dayunInfo.year_end || '';
  const wangshuai = dayunInfo.wangshuai || '';

  lines.push(`🔮 五运深度分析（${gz}大运，${ageStart}-${ageEnd}岁）`);
  lines.push(`   ${yearStart}-${yearEnd}年  旺衰：${wangshuai}`);
  lines.push('═'.repeat(44));
  lines.push('');

  const dimOrder = ['intimate', 'wealth', 'children', 'official', 'longevity'];
  for (const dimKey of dimOrder) {
    const dim = allDims[dimKey];
    if (!dim) continue;
    const label = DIMENSION_LABELS[dimKey] || dimKey;
    const score = dim.score || 0;
    const overall = dim.overall || '';
    const scoreBar = _buildScoreBar(score);

    lines.push(`【${label}】 ${overall}`);
    lines.push(`  评分 ${score}/100  ${scoreBar}`);
    if (dim.key_points && dim.key_points.length > 0) {
      lines.push(`  要点：${dim.key_points[0]}`);
    }
    lines.push(`  建议：${dim.advice || ''}`);
    lines.push('');
  }

  lines.push('─'.repeat(44));
  lines.push('💬 可继续追问某个维度的详情，例如：');
  lines.push(`   「${gz}大运感情运详细分析」`);
  lines.push(`   「${gz}大运财运要注意什么」`);

  return lines.join('\n');
}

/**
 * 格式化流年追踪分析
 * @param {object} liunyaPred - 流年预测数据
 * @param {string|null} dimension - 指定维度（null 表示综合）
 * @returns {string}
 */
function formatLiunyaAnalysis(liunyaPred, dimension) {
  const lines = [];
  const year = liunyaPred.year || '';
  const gz = liunyaPred.gz || '';
  const fortuneDesc = liunyaPred.fortune_desc || '';
  const score = liunyaPred.fortune_score || 50;
  const aspects = liunyaPred.aspects || {};
  const interactions = liunyaPred.interactions || [];

  lines.push(`🔮 ${year}年流年运势分析（${gz}）`);
  lines.push('─'.repeat(44));
  lines.push(`总体：${fortuneDesc}`);
  lines.push(`评分：${score}/100  ${_buildScoreBar(score)}`);
  lines.push('');

  if (interactions.length > 0) {
    lines.push('⚡ 特殊干支关系：');
    interactions.forEach(i => lines.push(`   ${i}`));
    lines.push('');
  }

  if (dimension && dimension !== 'all') {
    // 针对特定维度的流年分析
    const dimLabel = DIMENSION_LABELS[dimension] || dimension;
    lines.push(`【${dimLabel}】分析：`);
    const aspectMap = {
      intimate: aspects.love,
      wealth:   aspects.wealth,
      children: aspects.career,
      official: aspects.career,
      longevity: null,
    };
    const aspectText = aspectMap[dimension] || '流年数据参考中';
    if (aspectText) {
      lines.push(`   ${aspectText}`);
    }
    lines.push('');
    // 附加通用维度建议
    const adviceMap = {
      intimate: _liunyaIntimateAdvice(liunyaPred),
      wealth:   _liunyaWealthAdvice(liunyaPred),
      children: _liunyaChildrenAdvice(liunyaPred),
      official: _liunyaOfficialAdvice(liunyaPred),
      longevity: _liunyaLongevityAdvice(liunyaPred),
    };
    const advice = adviceMap[dimension];
    if (advice) {
      lines.push(`💡 要点：${advice}`);
    }
  } else {
    // 综合流年分析
    lines.push('各方面运势：');
    if (aspects.career) lines.push(`  事业：${aspects.career}`);
    if (aspects.wealth) lines.push(`  财运：${aspects.wealth}`);
    if (aspects.love)   lines.push(`  感情：${aspects.love}`);
    lines.push('');
    lines.push('💬 可追问特定维度，例如：');
    lines.push(`   「${year}年感情运详细分析」`);
    lines.push(`   「${year}年财运怎么看」`);
  }

  lines.push('─'.repeat(44));
  lines.push('💬 如需流月分析，可追问：');
  lines.push(`   「${year}年几月感情最好」`);
  lines.push(`   「${year}年N月财运如何」`);

  return lines.join('\n');
}

// ─── 流年维度辅助分析 ──────────────────────────────────────────────────────

function _liunyaIntimateAdvice(pred) {
  const tenGod = pred.year_ten_god || '';
  const map = {
    '正财': '流年正财透干，桃花旺，感情进展顺利',
    '偏财': '偏财临年，桃花出现，注意专一',
    '正官': '正官临年（利女命感情），适合确定关系',
    '七杀': '七杀临年，感情波折多，需耐心沟通',
    '食神': '食神临年，感情顺和有浪漫气息',
    '伤官': '伤官临年，感情不稳，容易产生争执',
  };
  return map[tenGod] || '感情运平稳，维系现有关系';
}

function _liunyaWealthAdvice(pred) {
  const tenGod = pred.year_ten_god || '';
  const map = {
    '正财': '正财进账稳定，适合储蓄理财',
    '偏财': '偏财运旺，适合投资或经商',
    '食神': '靠才能变现，财运自然进账',
    '伤官': '靠技能获财，注意不必要开支',
    '比肩': '竞争影响财运，谨慎共财',
    '劫财': '破财风险，谨慎投资',
  };
  return map[tenGod] || '财运平稳，量入为出';
}

function _liunyaChildrenAdvice(pred) {
  const tenGod = pred.year_ten_god || '';
  if (['食神', '伤官'].includes(tenGod)) {
    return '食伤临年，子女缘分旺，有喜事或子女成就机遇';
  }
  if (['正印', '偏印'].includes(tenGod)) {
    return '印星压食伤，子女运稍弱，宜关注子女健康';
  }
  return '子女关系平稳，注重亲子互动';
}

function _liunyaOfficialAdvice(pred) {
  const tenGod = pred.year_ten_god || '';
  const map = {
    '正官': '正官临年，职位晋升机会，上司赏识',
    '七杀': '七杀临年，竞争激烈，需展现实力',
    '食神': '食神临年，工作顺手，创意灵感多',
    '伤官': '伤官临年，发挥才华，注意与上司关系',
    '正印': '贵人相助，学习进修有收获',
  };
  return map[tenGod] || '事业平稳推进';
}

function _liunyaLongevityAdvice(pred) {
  const score = pred.fortune_score || 50;
  const interactions = pred.interactions || [];
  const hasChong = interactions.some(i => i.includes('冲'));
  if (score < 40 || hasChong) {
    return '流年有刑冲，注意突发健康问题，宜提前体检防范';
  }
  if (score >= 70) {
    return '流年运势旺，体力充沛，适合加强锻炼';
  }
  return '健康平稳，保持规律作息，定期体检';
}

// ─── 主追踪函数 ─────────────────────────────────────────────────────────────

/**
 * 处理五运追踪查询
 *
 * @param {string}  userQuery  - 用户的追踪问询文字
 * @param {object}  fullReport - bazi_analyzer.py 返回的完整报告 JSON（含 five_yun_summary）
 * @param {object}  [dayunDataOverride] - 可选：直接提供大运数据，优先使用
 * @returns {{ text: string, data: object, followUpPrompts: string[] }}
 */
function trackFortuneQuery(userQuery, fullReport, dayunDataOverride) {
  logger.info('[fortune_tracker] 处理追踪查询:', userQuery);

  // 1. 解析维度
  const dimension = parseDimension(userQuery);

  // 2. 解析时间帧
  const timeframe = extractTimeFrame(userQuery);

  logger.info(`[fortune_tracker] 维度: ${dimension}, 时间帧: ${JSON.stringify(timeframe)}`);

  // 3. 获取五运摘要数据
  const fiveYunSummary = fullReport.five_yun_summary || {};
  const recentDayun = fiveYunSummary.recent_dayun || [];
  const nextLiunya = fiveYunSummary.next_liunya || [];

  let resultText = '';
  let resultData = {};
  const followUpPrompts = [];

  if (timeframe.type === 'liunya') {
    // ── 流年追踪 ──────────────────────────────────────
    const year = timeframe.year;
    const liunyaPred = _findLiunyaData(fullReport, year);

    if (!liunyaPred) {
      resultText = `暂无 ${year} 年流年数据，请确认该年份在预测范围内。`;
    } else {
      resultText = formatLiunyaAnalysis(liunyaPred, dimension);
      resultData = { year, dimension, liunyaPred };

      // 生成追踪提示
      followUpPrompts.push(`「${year}年N月感情如何」（流月分析）`);
      followUpPrompts.push(`「${year}年整体运势」`);
      if (dimension) {
        const label = DIMENSION_LABELS[dimension] || dimension;
        followUpPrompts.push(`「当前大运${label}分析」`);
      }
    }

  } else {
    // ── 大运追踪 ──────────────────────────────────────
    let dayunData = dayunDataOverride || null;

    if (!dayunData) {
      if (timeframe.type === 'current') {
        // 找当前大运（year_start <= currentYear <= year_end）
        const currentYear = new Date().getFullYear();
        dayunData = recentDayun.find(d =>
          d.year_start <= currentYear && currentYear <= d.year_end
        ) || recentDayun[0];
      } else if (timeframe.type === 'dayun' && timeframe.index) {
        // 按序号找（从近期大运列表里找第N个，或从全量大运找）
        const allCycles = _getAllCycles(fullReport);
        dayunData = allCycles[timeframe.index - 1] || recentDayun[timeframe.index - 1];
      }
    }

    if (!dayunData) {
      resultText = '未能找到对应的大运数据，请确认查询格式，例如："分析第2个大运的感情"。';
    } else if (dimension === 'all') {
      // 五维度汇总
      const allDims = _computeAllDimensions(dayunData, fullReport);
      resultText = formatAllDimensions(allDims, dayunData);
      resultData = { dayunData, dimensions: allDims };

      followUpPrompts.push(`「${dayunData.gz}大运感情详细分析」`);
      followUpPrompts.push(`「${dayunData.gz}大运财运建议」`);
      followUpPrompts.push(`「${dayunData.gz}大运寿运注意事项」`);
    } else if (dimension) {
      // 单维度分析
      const dimResult = _computeSingleDimension(dayunData, dimension, fullReport);
      resultText = formatSingleDimension(dimResult, dayunData);
      resultData = { dayunData, dimension, dimResult };

      const label = DIMENSION_LABELS[dimension] || dimension;
      const otherDims = Object.keys(DIMENSION_LABELS).filter(d => d !== dimension);
      otherDims.slice(0, 2).forEach(d => {
        followUpPrompts.push(`「${dayunData.gz}大运${DIMENSION_LABELS[d]}如何」`);
      });
      followUpPrompts.push(`「${dayunData.gz}大运五运全面分析」`);
    } else {
      // 没有指定维度，显示五运汇总
      const allDims = _computeAllDimensions(dayunData, fullReport);
      resultText = formatAllDimensions(allDims, dayunData);
      resultData = { dayunData, dimensions: allDims };

      followUpPrompts.push(`「${dayunData.gz}大运感情运分析」`);
      followUpPrompts.push(`「${dayunData.gz}大运财运分析」`);
    }
  }

  // 附加追踪提示
  if (followUpPrompts.length > 0) {
    resultText += '\n\n💬 您还可以继续追问：\n';
    followUpPrompts.slice(0, 3).forEach(p => {
      resultText += `   ${p}\n`;
    });
  }

  return {
    text: resultText,
    data: resultData,
    followUpPrompts,
    dimension,
    timeframe,
  };
}

// ─── 辅助函数 ───────────────────────────────────────────────────────────────

/**
 * 从 fullReport 获取所有大运列表
 */
function _getAllCycles(fullReport) {
  // fullReport.five_yun_summary.recent_dayun 包含近几个大运
  const recentDayun = (fullReport.five_yun_summary || {}).recent_dayun || [];
  return recentDayun;
}

/**
 * 从 fullReport 查找指定年份的流年数据
 */
function _findLiunyaData(fullReport, year) {
  const nextLiunya = (fullReport.five_yun_summary || {}).next_liunya || [];
  const found = nextLiunya.find(p => p.year === year);
  if (found) return found;

  // luck_summary 是文本，没有结构化数据
  // 尝试从 full_report JSON 重新构建（如果有 yearly_predictions 字段）
  if (fullReport.yearly_predictions) {
    return fullReport.yearly_predictions.find(p => p.year === year) || null;
  }
  return null;
}

/**
 * 根据 dayunData 和 fullReport 计算五维度分析
 * 注意：此处基于 five_yun_summary 中已计算好的 dimensions 数据
 */
function _computeAllDimensions(dayunData, fullReport) {
  // 如果 dayunData.dimensions 已经存在（来自 five_yun_summary），直接使用
  if (dayunData.dimensions) {
    return dayunData.dimensions;
  }
  // 否则返回空占位
  return {
    intimate:  { score: 0, overall: '数据不足', advice: '请提供完整报告' },
    wealth:    { score: 0, overall: '数据不足', advice: '请提供完整报告' },
    children:  { score: 0, overall: '数据不足', advice: '请提供完整报告' },
    official:  { score: 0, overall: '数据不足', advice: '请提供完整报告' },
    longevity: { score: 0, overall: '数据不足', advice: '请提供完整报告' },
  };
}

/**
 * 获取单维度分析（从已有 dimensions 数据）
 */
function _computeSingleDimension(dayunData, dimension, fullReport) {
  const allDims = _computeAllDimensions(dayunData, fullReport);
  const dimData = allDims[dimension] || {};
  return {
    dimension,
    label: DIMENSION_LABELS[dimension] || dimension,
    dayun_gz: dayunData.gz || '',
    score: dimData.score || 0,
    overall: dimData.overall || '',
    advice: dimData.advice || '',
    key_points: dimData.key_points || [],
    wangshuai: dayunData.wangshuai || '',
    nayin: dayunData.nayin || '',
  };
}

/**
 * 构建分数条形图（ASCII）
 */
function _buildScoreBar(score) {
  const filled = Math.round(score / 10);
  const empty = 10 - filled;
  return '[' + '█'.repeat(filled) + '░'.repeat(empty) + ']';
}

// ─── Python 服务调用（运行时深度分析） ──────────────────────────────────────

/**
 * 通过 Python bazi_analyzer.py 获取完整报告（用于首次分析或刷新数据）
 *
 * @param {object} birthData - { year, month, day, hour, gender }
 * @returns {Promise<object>} - 完整报告 JSON
 */
function fetchFullReport(birthData) {
  return new Promise((resolve) => {
    const { year, month, day, hour = 0, gender = 'unknown' } = birthData;
    const args = [
      BAZI_ANALYZER_PATH,
      '--year', String(year),
      '--month', String(month),
      '--day', String(day),
      '--hour', String(hour),
      '--gender', gender,
    ];

    execFile('python3', args, { timeout: 60000 }, (err, stdout, stderr) => {
      if (err) {
        logger.error('[fortune_tracker] bazi_analyzer 调用失败:', err.message);
        resolve({ success: false, error: err.message });
        return;
      }
      try {
        resolve(JSON.parse(stdout));
      } catch (parseErr) {
        logger.error('[fortune_tracker] 解析 bazi_analyzer 输出失败:', parseErr.message);
        resolve({ success: false, error: '输出解析失败', raw: stdout });
      }
    });
  });
}

/**
 * 完整的追踪流程（含自动获取报告）
 *
 * @param {string} userQuery  - 用户问询
 * @param {object} birthData  - 出生数据 { year, month, day, hour, gender }
 * @param {object} [cachedReport] - 已缓存的完整报告（可选，避免重复计算）
 * @returns {Promise<{ text: string, data: object, report: object }>}
 */
async function handleTrackingQuery(userQuery, birthData, cachedReport) {
  let report = cachedReport;

  if (!report || !report.success) {
    logger.info('[fortune_tracker] 获取完整报告...');
    report = await fetchFullReport(birthData);
  }

  if (!report || !report.success) {
    return {
      text: `分析失败：${(report && report.error) || '未能获取命盘数据'}`,
      data: {},
      report: null,
    };
  }

  const result = trackFortuneQuery(userQuery, report);

  return {
    text:   result.text,
    data:   result.data,
    report,
    followUpPrompts: result.followUpPrompts,
    dimension: result.dimension,
    timeframe: result.timeframe,
  };
}

// ─── CLI 支持 ────────────────────────────────────────────────────────────────

if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 5) {
    console.error('用法: node fortune_tracker.js <year> <month> <day> <hour> <gender> [query]');
    console.error('  例: node fortune_tracker.js 1990 1 15 8 male "分析当前大运的感情运"');
    process.exit(1);
  }

  const birthData = {
    year:   parseInt(args[0], 10),
    month:  parseInt(args[1], 10),
    day:    parseInt(args[2], 10),
    hour:   parseInt(args[3], 10),
    gender: args[4] || 'unknown',
  };
  const query = args[5] || '当前大运五运全面分析';

  handleTrackingQuery(query, birthData).then((result) => {
    console.log(result.text);
  }).catch((err) => {
    console.error('未预期错误:', err.message);
    process.exit(1);
  });
}

module.exports = {
  trackFortuneQuery,
  handleTrackingQuery,
  fetchFullReport,
  parseDimension,
  extractTimeFrame,
  formatSingleDimension,
  formatAllDimensions,
  formatLiunyaAnalysis,
  DIMENSION_KEYWORDS,
  DIMENSION_LABELS,
};
