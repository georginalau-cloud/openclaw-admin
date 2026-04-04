'use strict';

/**
 * handler.js - 八字精批 Skill 处理器入口
 *
 * 主处理流程：
 *   输入八字 (年月日时)
 *     ↓
 *   [1] 排盘 & 定格 → 命盘基础数据
 *     ↓
 *   [2] 十神分析 → 性格特质画像
 *     ↓
 *   [3] 六亲关系 → 人脉脉络
 *     ↓
 *   [4] 财富事业 → 职业赛道建议
 *     ↓
 *   [5] 健康预警 → 脏腑与灾厄
 *     ↓
 *   [6] 大运流年 → 时间轴预测
 *     ↓
 *   [7] 趋吉避凶 → 开运建议
 *     ↓
 *   输出完整精批报告（分模块展示）
 *
 * 调用方式：
 *   算命 agent 在识别用户提及八字、运势、性格等内容时自动调用
 *
 * 参考典籍：
 *   梁湘润《子平真诠》、《三命通会》、《滴天髓》、《渊海子平》、《穷通宝鉴》
 */

const ganzhiCalculator  = require('./lib/ganzhi-calculator');
const tenGodsAnalyzer   = require('./lib/ten-gods-analyzer');
const formatAnalyzer    = require('./lib/format-analyzer');
const characterProfiler = require('./lib/character-profiler');
const sixRelations      = require('./lib/six-relations-analyzer');
const wealthCareer      = require('./lib/wealth-career-analyzer');
const healthPredictor   = require('./lib/health-predictor');
const luckCycleAnalyzer = require('./lib/luck-cycle-analyzer');
const adviceGenerator   = require('./lib/advice-generator');
const ancientBooks      = require('./lib/ancient-books-fetcher');

const logger = console;

/**
 * 解析输入参数
 * 支持多种格式：
 *   1. 结构化对象: { year, month, day, hour, gender }
 *   2. 八字字符串（年柱月柱日柱时柱）: "甲子 丙寅 戊午 庚申"
 *   3. 公历生日: "1990-01-15 14:00 male"
 *
 * @param {object|string} input - 输入数据
 * @returns {object} 标准化输入 { year, month, day, hour, gender }
 */
function parseInput(input) {
  if (typeof input === 'object' && input !== null) {
    const { year, month, day, hour, gender } = input;
    if (!year || !month || !day) {
      throw new Error('缺少必要参数：year, month, day（公历年月日）');
    }
    return {
      year:   parseInt(year,  10),
      month:  parseInt(month, 10),
      day:    parseInt(day,   10),
      hour:   parseInt(hour  || 12, 10),
      gender: gender || 'male',
    };
  }

  if (typeof input === 'string') {
    return parseStringInput(input);
  }

  throw new Error('不支持的输入格式，请提供 { year, month, day, hour, gender } 对象或生日字符串');
}

/**
 * 解析字符串格式输入
 * 支持: "1990-01-15 14:00 male" 或 "1990/1/15 14 female"
 */
function parseStringInput(str) {
  const parts = str.trim().split(/[\s,]+/);

  // 尝试解析 YYYY-MM-DD 格式
  const dateMatch = str.match(/(\d{4})[-/](\d{1,2})[-/](\d{1,2})/);
  if (dateMatch) {
    const year  = parseInt(dateMatch[1], 10);
    const month = parseInt(dateMatch[2], 10);
    const day   = parseInt(dateMatch[3], 10);

    // 查找时间
    const timeMatch = str.match(/(\d{1,2})[:时]/);
    const hour = timeMatch ? parseInt(timeMatch[1], 10) : 12;

    // 查找性别
    const isFemale = /female|女|女命/i.test(str);
    const gender   = isFemale ? 'female' : 'male';

    return { year, month, day, hour, gender };
  }

  throw new Error(`无法解析输入字符串: "${str}"。请使用 YYYY-MM-DD HH:MM [male|female] 格式`);
}

/**
 * 格式化四柱展示
 */
function formatPillarsDisplay(baziData) {
  const { pillars, hiddenStems, dayMaster, dayMasterElement, dayMasterYinYang } = baziData;
  const lines = [];

  lines.push('┌──────┬──────┬──────┬──────┐');
  lines.push(`│ 时柱 │ 日柱 │ 月柱 │ 年柱 │`);
  lines.push('├──────┼──────┼──────┼──────┤');
  lines.push(`│  ${pillars.hour.stem}   │  ${pillars.day.stem}   │  ${pillars.month.stem}   │  ${pillars.year.stem}   │`);
  lines.push(`│  ${pillars.hour.branch}   │  ${pillars.day.branch}   │  ${pillars.month.branch}   │  ${pillars.year.branch}   │`);
  lines.push('└──────┴──────┴──────┴──────┘');

  lines.push('');
  lines.push('藏干：');
  lines.push(`  年支${pillars.year.branch}：${hiddenStems.year.join('、') || '无'}`);
  lines.push(`  月支${pillars.month.branch}：${hiddenStems.month.join('、') || '无'}`);
  lines.push(`  日支${pillars.day.branch}：${hiddenStems.day.join('、') || '无'}`);
  lines.push(`  时支${pillars.hour.branch}：${hiddenStems.hour.join('、') || '无'}`);

  lines.push('');
  lines.push(`日主：${dayMaster}（${dayMasterElement}${dayMasterYinYang}）`);

  // 五行力量统计
  const { elementCount } = baziData;
  const elemStr = Object.entries(elementCount)
    .sort((a, b) => b[1] - a[1])
    .map(([e, c]) => `${e}×${c.toFixed(1)}`)
    .join('  ');
  lines.push(`五行：${elemStr}`);

  return lines.join('\n');
}

/**
 * 主处理函数 - 生成完整八字精批报告
 *
 * @param {object|string} input - 输入参数
 * @param {object} [options]    - 选项
 * @param {boolean} [options.includeAncientBooks=true] - 是否包含古籍引用
 * @param {number}  [options.currentYear]              - 当前年份（默认使用系统年份）
 * @returns {Promise<object>} 精批报告
 */
async function handle(input, options = {}) {
  const {
    includeAncientBooks = true,
    currentYear = new Date().getFullYear(),
  } = options;

  let parsedInput;
  try {
    parsedInput = parseInput(input);
  } catch (err) {
    return { success: false, error: err.message };
  }

  logger.info('[bazi-analyzer] 开始八字精批分析:', JSON.stringify(parsedInput));

  const report = {
    success:    true,
    input:      parsedInput,
    generatedAt: new Date().toISOString(),
    sections:   {},
  };

  try {
    // ─── [1] 排盘 & 定格 ──────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [1] 排盘计算...');
    const baziData = ganzhiCalculator.calcFourPillars(parsedInput);
    report.baziData = baziData;

    const pillarsDisplay = formatPillarsDisplay(baziData);

    // ─── [2] 十神分析 ─────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [2] 十神分析...');
    const tenGodsAnalysis = tenGodsAnalyzer.analyze(baziData);

    // ─── [2a] 格局判断 ────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [2a] 格局判断...');
    const formatAnalysis = formatAnalyzer.analyze(baziData, tenGodsAnalysis.strengthAnalysis);

    // ─── [3] 性格画像 ─────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [3] 性格画像...');
    const characterProfile = characterProfiler.analyze(baziData, tenGodsAnalysis, formatAnalysis);

    // ─── [4] 六亲关系 ─────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [4] 六亲分析...');
    const sixRelationsAnalysis = sixRelations.analyze(baziData, tenGodsAnalysis, parsedInput.gender);

    // ─── [5] 财富事业 ─────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [5] 财富事业...');
    const wealthCareerAnalysis = wealthCareer.analyze(baziData, tenGodsAnalysis, formatAnalysis);

    // ─── [6] 健康预警 ─────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [6] 健康预警...');
    const healthAnalysis = healthPredictor.analyze(baziData, tenGodsAnalysis);

    // ─── [7] 大运流年 ─────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [7] 大运流年...');
    const luckCycleAnalysis = luckCycleAnalyzer.analyze(baziData, tenGodsAnalysis, formatAnalysis, currentYear);

    // ─── [8] 趋吉避凶 ─────────────────────────────────────────────────────
    logger.info('[bazi-analyzer] [8] 趋吉避凶...');
    const adviceAnalysis = adviceGenerator.analyze(baziData, tenGodsAnalysis, formatAnalysis);

    // ─── 古籍引用（可选）────────────────────────────────────────────────────
    let classicRefs = null;
    if (includeAncientBooks) {
      logger.info('[bazi-analyzer] 查询古籍引用...');
      try {
        classicRefs = await ancientBooks.batchQuery([
          formatAnalysis.format,
          tenGodsAnalysis.yongJiShen.yongShenTenGods[0] || '用神',
        ]);
      } catch (err) {
        logger.warn('[bazi-analyzer] 古籍查询失败（不影响报告）:', err.message);
      }
    }

    // ─── 组装报告 ─────────────────────────────────────────────────────────
    report.sections = {
      pillarsDisplay,
      tenGodsAnalysis,
      formatAnalysis,
      characterProfile,
      sixRelationsAnalysis,
      wealthCareerAnalysis,
      healthAnalysis,
      luckCycleAnalysis,
      adviceAnalysis,
      classicRefs,
    };

    report.fullReport = buildFullReport(report.sections, parsedInput);
    logger.info('[bazi-analyzer] 八字精批分析完成');

  } catch (err) {
    logger.error('[bazi-analyzer] 分析过程出错:', err.message, err.stack);
    report.success = false;
    report.error   = err.message;
  }

  return report;
}

/**
 * 构建完整精批报告文本
 */
function buildFullReport(sections, input) {
  const { gender } = input;
  const genderStr  = gender === 'female' ? '女命' : '男命';
  const lines      = [];

  lines.push('═'.repeat(60));
  lines.push(`🔮 八字精批报告（${genderStr}）`);
  lines.push(`公历生日：${input.year}年${input.month}月${input.day}日 ${input.hour}时`);
  lines.push('═'.repeat(60));
  lines.push('');

  // ── 第一部分：命盘基础 ────────────────────────────────
  lines.push('【第一模块】命盘排布与格局定位');
  lines.push('─'.repeat(40));
  lines.push(sections.pillarsDisplay || '');
  lines.push('');
  if (sections.tenGodsAnalysis) {
    lines.push(sections.tenGodsAnalysis.summary || '');
    lines.push('');
  }
  if (sections.formatAnalysis) {
    lines.push(sections.formatAnalysis.summary || '');
    lines.push('');
  }

  // ── 第二部分：性格画像 ────────────────────────────────
  lines.push('【第二模块】性格特质深度画像');
  lines.push('─'.repeat(40));
  if (sections.characterProfile) {
    lines.push(sections.characterProfile.summary || '');
    lines.push('');
  }

  // ── 第三部分：六亲关系 ────────────────────────────────
  lines.push('【第三模块】六亲关系与社会脉络');
  lines.push('─'.repeat(40));
  if (sections.sixRelationsAnalysis) {
    lines.push(sections.sixRelationsAnalysis.summary || '');
    lines.push('');
  }

  // ── 第四部分：财富事业 ────────────────────────────────
  lines.push('【第四模块】事业财运分析');
  lines.push('─'.repeat(40));
  if (sections.wealthCareerAnalysis) {
    lines.push(sections.wealthCareerAnalysis.summary || '');
    lines.push('');
  }

  // ── 第五部分：健康预警 ────────────────────────────────
  lines.push('【第五模块】身体健康预警');
  lines.push('─'.repeat(40));
  if (sections.healthAnalysis) {
    lines.push(sections.healthAnalysis.summary || '');
    lines.push('');
  }

  // ── 第六部分：大运流年 ────────────────────────────────
  lines.push('【第六模块】大运与流年预测');
  lines.push('─'.repeat(40));
  if (sections.luckCycleAnalysis) {
    lines.push(sections.luckCycleAnalysis.summary || '');
    lines.push('');
  }

  // ── 第七部分：趋吉避凶 ────────────────────────────────
  lines.push('【第七模块】趋吉避凶建议');
  lines.push('─'.repeat(40));
  if (sections.adviceAnalysis) {
    lines.push(sections.adviceAnalysis.summary || '');
    lines.push('');
  }

  // ── 古籍引用 ─────────────────────────────────────────
  if (sections.classicRefs) {
    const refs = sections.classicRefs.queries || {};
    const refLines = [];
    for (const [kw, result] of Object.entries(refs)) {
      if (result.success && result.results && result.results.length > 0) {
        const r = result.results[0];
        refLines.push(`《${r.title || '古籍'}》：${r.text ? r.text.slice(0, 80) : ''}...`);
      }
    }
    if (refLines.length) {
      lines.push('【古籍引用】');
      lines.push('─'.repeat(40));
      lines.push(...refLines);
      lines.push('');
    }
  }

  lines.push('═'.repeat(60));
  lines.push('（本报告依据子平法，参考梁湘润《子平真诠》等经典著作）');
  lines.push('🔮 算命喵精批 · 仅供参考，命运还需自己把握');

  return lines.join('\n');
}

// ─── CLI 支持 ────────────────────────────────────────────────────────────────
if (require.main === module) {
  const args = process.argv.slice(2);

  // 解析 CLI 参数
  const cliInput = {};
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--year')   cliInput.year   = args[++i];
    if (args[i] === '--month')  cliInput.month  = args[++i];
    if (args[i] === '--day')    cliInput.day    = args[++i];
    if (args[i] === '--hour')   cliInput.hour   = args[++i];
    if (args[i] === '--gender') cliInput.gender = args[++i];
    if (args[i] === '--date') {
      const dateParts = args[++i].split('-');
      cliInput.year  = dateParts[0];
      cliInput.month = dateParts[1];
      cliInput.day   = dateParts[2];
    }
  }

  if (!cliInput.year || !cliInput.month || !cliInput.day) {
    console.error('用法: node handler.js --year 1990 --month 1 --day 15 --hour 14 --gender male');
    console.error('   或: node handler.js --date 1990-01-15 --hour 14 --gender male');
    process.exit(1);
  }

  handle(cliInput, { includeAncientBooks: false }).then((result) => {
    if (result.success) {
      console.log(result.fullReport);
    } else {
      console.error('分析失败:', result.error);
      process.exit(1);
    }
  }).catch((err) => {
    console.error('未预期错误:', err.message);
    process.exit(1);
  });
}

module.exports = { handle, parseInput };
