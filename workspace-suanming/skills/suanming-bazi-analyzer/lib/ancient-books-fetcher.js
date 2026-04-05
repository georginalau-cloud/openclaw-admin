'use strict';

/**
 * ancient-books-fetcher.js - 古籍在线查询
 *
 * 功能：
 *   1. 优先查询 ctext.org 获取古籍原文
 *   2. 备选 archive.org 查询
 *   3. 查询结果缓存到本地 memory/knowledge-cache/
 *   4. 在线查询失败时降级使用本地 classic-wisdom.json
 *
 * 支持的古籍：
 *   - 《子平真诠》(zi-ping-zhen-quan)
 *   - 《三命通会》(san-ming-tong-hui)
 *   - 《滴天髓》(di-tian-sui)
 *   - 《渊海子平》(yuan-hai-zi-ping)
 *   - 《穷通宝鉴》(qiong-tong-bao-jian)
 */

const https    = require('https');
const http     = require('http');
const fs       = require('fs');
const path     = require('path');
const { URL }  = require('url');

const logger = console;

// 本地 classic-wisdom.json 路径
const LOCAL_WISDOM_PATH = path.join(__dirname, '..', 'data', 'classic-wisdom.json');

// 缓存目录（运行时环境路径）
const CACHE_DIR = path.join(
  process.env.HOME || '/root',
  '.openclaw', 'workspace-suanming', 'memory', 'knowledge-cache'
);

// ctext.org API 基础 URL
// 文档参考: https://ctext.org/tools/api
const CTEXT_API_BASE = 'https://ctext.org/api.pl';

// 古籍在 ctext.org 上的书目标识
const BOOK_IDS = {
  'ziping-zhenjian':   'zp',  // 子平真诠（子平法精粹）
  'san-ming-tonghui':  'smth', // 三命通会
  'di-tian-sui':       'dts',  // 滴天髓
  'yuan-hai-zi-ping':  'yhzp', // 渊海子平
  'qiong-tong-bao-jian': 'qtbj', // 穷通宝鉴
};

// 请求超时（毫秒）
const REQUEST_TIMEOUT = 8000;

/**
 * 从 ctext.org 查询古籍文本
 * @param {string} keyword - 查询关键词
 * @param {string} book    - 古籍名称（book key from BOOK_IDS or null for all）
 * @returns {Promise<object>} 查询结果
 */
async function queryCtextOrg(keyword, book = null) {
  const params = new URLSearchParams({
    fn:   'searchtexts',
    q:    keyword,
    remap: 'true',
  });

  if (book && BOOK_IDS[book]) {
    params.set('book', BOOK_IDS[book]);
  }

  const url = `${CTEXT_API_BASE}?${params.toString()}`;

  try {
    const rawData = await httpGet(url, REQUEST_TIMEOUT);
    const parsed  = JSON.parse(rawData);

    if (parsed.status !== 'ok') {
      throw new Error(`ctext.org 返回错误: ${parsed.message || '未知错误'}`);
    }

    const results = (parsed.result || []).slice(0, 5).map(r => ({
      title:   r.title || '',
      chapter: r.chapter || '',
      text:    r.text   || '',
      url:     r.url    || '',
    }));

    return { success: true, source: 'ctext.org', keyword, results };
  } catch (err) {
    logger.warn('[ancient-books] ctext.org 查询失败:', err.message);
    return { success: false, source: 'ctext.org', error: err.message };
  }
}

/**
 * 从本地 classic-wisdom.json 查询
 * @param {string} keyword - 关键词
 * @returns {object} 查询结果
 */
function queryLocalWisdom(keyword) {
  try {
    const wisdom = JSON.parse(fs.readFileSync(LOCAL_WISDOM_PATH, 'utf8'));
    const results = [];

    // 搜索所有书籍的关键段落
    const books = [
      'ziping_zhenjian', 'san_ming_tonghui', 'di_tian_sui', 'yuan_hai_zi_ping', 'qiong_tong_bao_jian',
    ];

    for (const bookKey of books) {
      const book = wisdom[bookKey];
      if (!book) continue;

      const passages = book.key_passages || {};
      for (const [passageKey, text] of Object.entries(passages)) {
        if (text.includes(keyword)) {
          results.push({
            title:   book.title || bookKey,
            chapter: passageKey,
            text,
            source:  'local',
          });
        }
      }
    }

    // 搜索特殊格局
    const special = wisdom.special_patterns || {};
    for (const [pattern, text] of Object.entries(special)) {
      if (text.includes(keyword) || pattern.includes(keyword)) {
        results.push({
          title:   '特殊格局',
          chapter: pattern,
          text,
          source:  'local',
        });
      }
    }

    return {
      success: true,
      source:  'local',
      keyword,
      results: results.slice(0, 5),
    };
  } catch (err) {
    logger.error('[ancient-books] 本地知识库查询失败:', err.message);
    return { success: false, source: 'local', error: err.message, results: [] };
  }
}

/**
 * 查询古籍（优先在线，降级本地）
 * @param {string} keyword - 查询关键词（如"正官格"、"用神"等）
 * @param {string} book    - 指定古籍（可选）
 * @returns {Promise<object>} 查询结果
 */
async function query(keyword, book = null) {
  // 检查缓存
  const cached = readCache(keyword);
  if (cached) {
    logger.info(`[ancient-books] 缓存命中: ${keyword}`);
    return { ...cached, fromCache: true };
  }

  // 优先在线查询
  const onlineResult = await queryCtextOrg(keyword, book);
  if (onlineResult.success && onlineResult.results.length > 0) {
    writeCache(keyword, onlineResult);
    return onlineResult;
  }

  // 降级本地查询
  logger.info(`[ancient-books] 在线查询失败，降级本地: ${keyword}`);
  const localResult = queryLocalWisdom(keyword);

  if (localResult.success && localResult.results.length > 0) {
    return localResult;
  }

  // 返回空结果
  return {
    success: false,
    source:  'none',
    keyword,
    results: [],
    note:    '在线和本地查询均未找到相关古籍内容',
  };
}

/**
 * 批量查询多个关键词（用于格局分析时并行查询）
 * @param {string[]} keywords - 关键词数组
 * @param {string}   book     - 指定古籍（可选）
 * @returns {Promise<object>} 合并结果
 */
async function batchQuery(keywords, book = null) {
  const results = await Promise.allSettled(
    keywords.map(kw => query(kw, book))
  );

  const merged = { success: true, queries: {} };
  for (let i = 0; i < keywords.length; i++) {
    const r = results[i];
    merged.queries[keywords[i]] = r.status === 'fulfilled' ? r.value : { success: false, error: r.reason.message };
  }

  return merged;
}

/**
 * 读取缓存
 */
function readCache(keyword) {
  try {
    const cacheFile = getCacheFilePath(keyword);
    if (!fs.existsSync(cacheFile)) return null;

    const data = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
    // 缓存有效期7天
    const cachedAt = new Date(data.cachedAt || 0);
    const now      = new Date();
    const diffDays = (now - cachedAt) / (1000 * 60 * 60 * 24);
    if (diffDays > 7) return null;

    return data;
  } catch {
    return null;
  }
}

/**
 * 写入缓存
 */
function writeCache(keyword, data) {
  try {
    if (!fs.existsSync(CACHE_DIR)) {
      fs.mkdirSync(CACHE_DIR, { recursive: true });
    }
    const cacheFile = getCacheFilePath(keyword);
    fs.writeFileSync(cacheFile, JSON.stringify({ ...data, cachedAt: new Date().toISOString() }, null, 2), 'utf8');
  } catch (err) {
    logger.warn('[ancient-books] 写入缓存失败:', err.message);
  }
}

/**
 * 生成缓存文件路径
 */
function getCacheFilePath(keyword) {
  // 对关键词进行简单哈希，避免特殊字符
  const safeKey = keyword.replace(/[^\w\u4e00-\u9fa5]/g, '_').slice(0, 50);
  return path.join(CACHE_DIR, `${safeKey}.json`);
}

/**
 * HTTP GET 请求
 */
function httpGet(url, timeout) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const lib    = parsed.protocol === 'https:' ? https : http;

    const req = lib.get(url, { timeout }, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${url}`));
        }
      });
    });

    req.on('timeout', () => {
      req.destroy();
      reject(new Error(`请求超时: ${url}`));
    });

    req.on('error', reject);
  });
}

/**
 * 获取格局相关的古籍引用
 * @param {string} format - 格局名称，如 '正官格'
 * @returns {Promise<object>}
 */
async function getFormatClassicRef(format) {
  return query(format);
}

/**
 * 获取用神相关的古籍引用
 * @param {string} yongShenDesc - 用神描述
 * @returns {Promise<object>}
 */
async function getYongShenClassicRef(yongShenDesc) {
  return query(yongShenDesc);
}

module.exports = {
  query,
  batchQuery,
  queryCtextOrg,
  queryLocalWisdom,
  getFormatClassicRef,
  getYongShenClassicRef,
};
