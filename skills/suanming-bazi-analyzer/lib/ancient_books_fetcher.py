"""
[21] lib/ancient_books_fetcher.py - 古籍查询模块
调用层级：被 bin/bazi 调用
依赖：data/classic-texts.json（本地备选）

优先从 ctext.org API 查询经典著作原文，
失败时降级使用本地 classic-texts.json。
查询结果缓存72小时。
"""

import json
import os
import time
import hashlib

try:
    import urllib.request
    import urllib.parse
    HAS_URLLIB = True
except ImportError:
    HAS_URLLIB = False

_DATA_DIR  = os.path.join(os.path.dirname(__file__), '..', 'data')
_CACHE_DIR = os.path.join(os.path.expanduser('~'), '.openclaw', 'workspace-suanming',
                          'memory', 'knowledge-cache')
_CACHE_TTL = 72 * 3600  # 72小时

# ctext.org API 基础 URL
CTEXT_API_BASE = 'https://ctext.org/api.pl'

# 经典著作映射
BOOK_URN_MAP = {
    '滴天髓': 'urn:ctext:wiki:滴天髓',
    '渊海子平': None,   # ctext 暂无完整版，降级本地
    '子平真诠': None,   # 降级本地
    '三命通会': None,   # 降级本地
    '穷通宝鉴': None,   # 降级本地
}


def _load_local_texts():
    """加载本地经典文本库"""
    path = os.path.join(_DATA_DIR, 'classic-texts.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _get_cache_path(cache_key):
    """获取缓存文件路径"""
    hashed = hashlib.md5(cache_key.encode('utf-8')).hexdigest()[:12]
    return os.path.join(_CACHE_DIR, f'ctext-{hashed}.json')


def _load_cache(cache_key):
    """加载缓存（如有效则返回，否则返回None）"""
    cache_path = _get_cache_path(cache_key)
    try:
        if not os.path.exists(cache_path):
            return None
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        # 检查是否过期
        if time.time() - cached.get('cached_at', 0) < _CACHE_TTL:
            return cached.get('data')
    except Exception:
        pass
    return None


def _save_cache(cache_key, data):
    """保存查询结果到缓存"""
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        cache_path = _get_cache_path(cache_key)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump({'cached_at': time.time(), 'data': data}, f, ensure_ascii=False)
    except Exception:
        pass  # 缓存失败不影响主流程


def _fetch_from_ctext(urn, keyword=None, timeout=5):
    """
    从 ctext.org API 查询文本
    参数:
        urn: 文本的 URN
        keyword: 搜索关键词（可选）
        timeout: 超时秒数
    返回: 文本内容列表，失败返回 None
    """
    if not HAS_URLLIB or not urn:
        return None

    try:
        params = {
            'if': 'en',
            'urn': urn,
            'mode': 'json',
        }
        if keyword:
            params['q'] = keyword

        url = CTEXT_API_BASE + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'OpenClaw-BaziAnalyzer/1.0'},
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode('utf-8')
            data = json.loads(raw)

            # ctext API 返回格式处理
            if isinstance(data, dict):
                records = data.get('records', [])
                if records:
                    return records

        return None
    except Exception:
        return None


def get_relevant_passages(topic, day_master=None, format_name=None):
    """
    获取与主题相关的古籍段落
    参数:
        topic: 查询主题（如 '用神', '正官格', '财星' 等）
        day_master: 日主天干（可选，用于精确查询）
        format_name: 格局名称（可选）
    返回: 相关段落列表
    """
    local_texts = _load_local_texts()
    passages = []

    # 构建查询关键词
    keywords = [topic]
    if day_master:
        keywords.append(day_master)
    if format_name:
        keywords.append(format_name.replace('（', '').replace('）', '').replace('格', ''))

    # 遍历各本典籍
    for book_name, book_data in local_texts.get('经典著作摘录', {}).items():
        book_passages = book_data.get('key_passages', [])
        for passage in book_passages:
            original = passage.get('original', '')
            interpretation = passage.get('interpretation', '')
            chapter = passage.get('chapter', '')

            # 匹配关键词
            text_to_search = original + interpretation + chapter
            matched = any(kw in text_to_search for kw in keywords)

            if matched:
                passages.append({
                    'source': book_name,
                    'chapter': chapter,
                    'original': original,
                    'interpretation': interpretation,
                })

    # 如果本地没有匹配，尝试在线查询（仅滴天髓有URN）
    if not passages:
        cache_key = f'ctext_{topic}_{day_master}'
        cached = _load_cache(cache_key)
        if cached:
            return cached

        urn = BOOK_URN_MAP.get('滴天髓')
        if urn:
            online_result = _fetch_from_ctext(urn, keyword=topic)
            if online_result:
                for rec in online_result[:3]:
                    passages.append({
                        'source': '滴天髓（在线）',
                        'chapter': rec.get('title', ''),
                        'original': rec.get('text', ''),
                        'interpretation': '（在线查询原文，请结合命理师解读）',
                    })
                _save_cache(cache_key, passages)

    return passages[:5]  # 最多返回5条


def format_passages_for_report(passages, topic=''):
    """将段落格式化为报告文字"""
    if not passages:
        return ''

    lines = [f"【经典参考：{topic}】" if topic else "【古籍参考】"]
    for p in passages[:3]:
        source = p.get('source', '')
        chapter = p.get('chapter', '')
        original = p.get('original', '')
        interpretation = p.get('interpretation', '')
        lines.append(f"  《{source}》{f'·{chapter}' if chapter else ''}：")
        if original:
            lines.append(f"  「{original}」")
        if interpretation:
            lines.append(f"  ↳ {interpretation}")
    return '\n'.join(lines)
