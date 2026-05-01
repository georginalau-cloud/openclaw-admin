"""
[13] lib/format_analyzer.py - 格局判断 + 用神取用（三法合一）
调用层级：被 bin/bazi 调用（分析层第二步）
依赖：lib/ganzhi_calculator.py [03]、lib/yongshen_analyzer.py [12]
数据：data/format-definitions.json、data/classic-wisdom.json

格局判断：《子平真诠》月令藏干透出法
用神取用：调候（穷通宝鉴）> 病药 > 通关，从格单独处理

外部接口不变：
  format_full_analysis(pillars, ten_gods_analysis) -> dict
  determine_format(pillars, ten_gods_analysis) -> dict
  get_yong_shen(pillars, format_info) -> dict  ← 兼容旧调用
"""

import json
import os

from .ganzhi_calculator import (
    STEM_ELEMENTS, BRANCH_ELEMENTS, HIDDEN_STEMS,
    GENERATES, get_daymaster_strength,
)
from .yongshen_analyzer import get_yongshen

_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')


def _load_format_definitions():
    """加载格局定义库（format-definitions.json）"""
    path = os.path.join(_DATA_DIR, 'format-definitions.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _load_classic_wisdom():
    """加载经典理论速查表（classic-wisdom.json）"""
    path = os.path.join(_DATA_DIR, 'classic-wisdom.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


FORMAT_DEFINITIONS = _load_format_definitions()
CLASSIC_WISDOM = _load_classic_wisdom()

# 格局名称映射（月令主气十神 -> 格局名）
FORMAT_NAME_MAP = {
    '正官': '正官格',
    '七杀': '偏官格（七杀格）',
    '正印': '印绶格（正印格）',
    '偏印': '偏印格（枭神格）',
    '正财': '正财格',
    '偏财': '偏财格',
    '食神': '食神格',
    '伤官': '伤官格',
    '比肩': '建禄格',
    '劫财': '月劫格',
}

# 格局名到 format-definitions.json 键名的映射
FORMAT_DEF_KEY_MAP = {
    '正官格':        '正官格',
    '偏官格（七杀格）': '偏官格',
    '印绶格（正印格）': '印绶格',
    '偏印格（枭神格）': '偏印格',
    '正财格':        '正财格',
    '偏财格':        '偏财格',
    '食神格':        '食神格',
    '伤官格':        '伤官格',
    '建禄格':        '比肩格',
    '月劫格':        '比肩格',
    '从格':          '从格',
    '从财格':        '从格',
    '从官格':        '从格',
    '从儿格':        '从格',
    '从杀格':        '从格',
}

CONTROLS = {'木': '土', '火': '金', '土': '水', '金': '木', '水': '火'}


def get_format_definition(format_name: str) -> dict:
    """
    从 format-definitions.json 中获取格局定义。
    返回格局的特征、优势、职业、名言、财富等级等信息。
    """
    defs = FORMAT_DEFINITIONS.get('格局定义', {})
    # 直接匹配
    if format_name in defs:
        return defs[format_name]
    # 通过映射表匹配
    key = FORMAT_DEF_KEY_MAP.get(format_name)
    if key and key in defs:
        return defs[key]
    # 模糊匹配（格局名包含关键词）
    for def_key, def_val in defs.items():
        if def_key in format_name or format_name in def_key:
            return def_val
    return {}


def get_classic_wisdom_for_format(format_ten_god: str) -> str:
    """
    从 classic-wisdom.json 中获取与格局相关的经典论述。
    """
    wisdom_map = {
        '正官': CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('zheng_guan_ge', ''),
        '七杀': CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('qi_sha_ge', ''),
        '食神': CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('shi_shen_ge', ''),
        '正财': CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('cai_ge', ''),
        '正印': CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('yin_ge', ''),
        '偏印': CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('yin_ge', ''),
        '比肩': CLASSIC_WISDOM.get('yuan_hai_zi_ping', {}).get('key_passages', {}).get('jian_lu_ge', ''),
        '劫财': CLASSIC_WISDOM.get('yuan_hai_zi_ping', {}).get('key_passages', {}).get('yang_ren_ge', ''),
    }
    return wisdom_map.get(format_ten_god, CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('ge_ju', ''))


# ─────────────────────────────────────────────────────────────────
# 格局判断
# ─────────────────────────────────────────────────────────────────

def determine_format(pillars, ten_gods_analysis):
    """
    判断命局格局。
    《子平真诠》：以月令地支藏干为基础，看哪个藏干透出天干成为格局。
    """
    month_branch = pillars['month_pillar']['branch']
    month_hidden = HIDDEN_STEMS.get(month_branch, [])
    month_lord   = month_hidden[0] if month_hidden else None

    transparent_stems = [
        pillars['year_pillar']['stem'],
        pillars['month_pillar']['stem'],
        pillars['hour_pillar']['stem'],
    ]

    format_ten_god = None
    format_source  = None

    for hidden_stem in month_hidden:
        if hidden_stem and hidden_stem in transparent_stems:
            month_data = ten_gods_analysis.get('month_pillar', {})
            for hd in month_data.get('branch_hidden', []):
                if hd['stem'] == hidden_stem:
                    format_ten_god = hd['ten_god']
                    format_source  = f"月令{month_branch}中{hidden_stem}透出"
                    break
            if format_ten_god:
                break

    if not format_ten_god and month_lord:
        month_data = ten_gods_analysis.get('month_pillar', {})
        for hd in month_data.get('branch_hidden', []):
            if hd['stem'] == month_lord:
                format_ten_god = hd['ten_god']
                format_source  = f"月令{month_branch}主气{month_lord}定格"
                break

    format_name = FORMAT_NAME_MAP.get(
        format_ten_god,
        f'{format_ten_god}格' if format_ten_god else '杂气格'
    )

    # 从格判断（用新模块）
    pillars_list = _pillars_dict_to_list(pillars)
    day_gan      = pillars.get('day_master', '')
    cong_ge      = _check_cong_ge_compat(pillars_list, day_gan, ten_gods_analysis)

    final_format_name = cong_ge['name'] if cong_ge else format_name

    # 从 format-definitions.json 获取格局详细定义
    format_def = get_format_definition(final_format_name)

    # 从 classic-wisdom.json 获取经典论述
    classic_quote = get_classic_wisdom_for_format(format_ten_god or '')

    return {
        'format_name':       final_format_name,
        'format_ten_god':    format_ten_god,
        'format_source':     format_source,
        'is_cong_ge':        cong_ge is not None,
        'cong_ge_detail':    cong_ge,
        'month_branch':      month_branch,
        'month_lord':        month_lord,
        # 来自 format-definitions.json 的丰富内容
        'characteristics':   format_def.get('characteristics', ''),
        'strengths':         format_def.get('strengths', []),
        'career':            format_def.get('career', ''),
        'famous_saying':     format_def.get('famous_saying', classic_quote),
        'wealth_level':      format_def.get('wealth_level', ''),
        'life_tendency':     format_def.get('life_tendency', ''),
        'formation':         format_def.get('formation', format_source or ''),
        # 来自 classic-wisdom.json 的经典论述
        'classic_theory':    classic_quote,
    }


def _pillars_dict_to_list(pillars: dict) -> list:
    """将 lib 格式的 pillars 字典转为列表格式（供 yongshen_analyzer 使用）。"""
    key_map = {
        'year_pillar':  0,
        'month_pillar': 1,
        'day_pillar':   2,
        'hour_pillar':  3,
    }
    result = []
    for key, idx in key_map.items():
        p = pillars.get(key, {})
        if p:
            result.append({
                'index': idx,
                'gan':   p.get('stem', ''),
                'zhi':   p.get('branch', ''),
            })
    return result


def _check_cong_ge_compat(pillars_list, day_gan, ten_gods_analysis):
    """兼容旧接口的从格判断，内部调用 yongshen_analyzer。"""
    from .yongshen_analyzer import check_cong_ge
    return check_cong_ge(pillars_list, day_gan, ten_gods_analysis)


# ─────────────────────────────────────────────────────────────────
# 用神取用（新版，三法合一）
# ─────────────────────────────────────────────────────────────────

def get_yong_shen(pillars, format_info):
    """
    取用神和忌神（兼容旧接口）。
    内部调用 yongshen_analyzer.get_yongshen()，三法合一。
    """
    day_gan      = pillars.get('day_master', '')
    pillars_list = _pillars_dict_to_list(pillars)
    month_zhi    = pillars.get('month_pillar', {}).get('branch', '')

    # 构建 ten_gods_map（yongshen_analyzer 需要的格式）
    ten_gods_map = {}
    for key in ('year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar'):
        p = pillars.get(key, {})
        if p:
            ten_gods_map[key] = {
                'stem_ten_god': p.get('stem_ten_god', ''),
                'branch_hidden': p.get('branch_hidden', []),
            }

    result = get_yongshen(pillars_list, day_gan, month_zhi, ten_gods_map)

    # 转换为旧接口格式（保持向后兼容）
    return {
        'yong_shen':           result['yong_shen'],
        'yong_shen_secondary': result['yong_list'][1] if len(result['yong_list']) > 1 else '',
        'yong_list':           result['yong_list'],
        'ji_shen':             result['ji_shen'],
        'xi_shen':             result.get('xi_shen', []),
        'xiang_shen':          result.get('xiang_shen', []),
        'yong_shen_reason':    result['note'],
        'strength':            result['strength'],
        'strength_score':      result['strength_score'],
        'method':              result['method'],
        'tiaohou':             result['tiaohou'],
        'cong_ge':             result['cong_ge'],
        'temp_score':          result['temp_score'],
    }


# ─────────────────────────────────────────────────────────────────
# 综合分析入口
# ─────────────────────────────────────────────────────────────────

def format_full_analysis(pillars, ten_gods_analysis):
    """综合格局分析：格局 + 用神忌神。"""
    format_info    = determine_format(pillars, ten_gods_analysis)
    yong_shen_info = get_yong_shen(pillars, format_info)

    # 从格时覆盖格局名
    if yong_shen_info.get('cong_ge'):
        cg = yong_shen_info['cong_ge']
        format_info['format_name']    = cg.get('name', format_info['format_name'])
        format_info['is_cong_ge']     = True
        format_info['cong_ge_detail'] = cg

    return {
        'format':    format_info,
        'yong_shen': yong_shen_info,
        'summary':   _build_format_summary(format_info, yong_shen_info),
    }


def _build_format_summary(format_info, yong_shen_info):
    """生成格局分析文字摘要。"""
    lines = []
    lines.append(f"▶ 格局：{format_info['format_name']}")
    if format_info.get('format_source'):
        lines.append(f"  成格依据：{format_info['format_source']}")
    if format_info.get('is_cong_ge'):
        cg = format_info.get('cong_ge_detail', {})
        lines.append(f"  ⚠ 特殊从格：{cg.get('note', '')}")

    # 格局特征（来自 format-definitions.json）
    if format_info.get('characteristics'):
        lines.append(f"  格局特征：{format_info['characteristics']}")
    if format_info.get('strengths'):
        lines.append(f"  核心优势：{'、'.join(format_info['strengths'])}")
    if format_info.get('career'):
        lines.append(f"  适合方向：{format_info['career']}")
    if format_info.get('wealth_level'):
        lines.append(f"  财富格局：{format_info['wealth_level']}")
    if format_info.get('life_tendency'):
        lines.append(f"  人生走向：{format_info['life_tendency']}")

    # 经典名言（来自 format-definitions.json 或 classic-wisdom.json）
    famous_saying = format_info.get('famous_saying') or format_info.get('classic_theory')
    if famous_saying:
        lines.append(f"  古籍论述：「{famous_saying}」")

    method = yong_shen_info.get('method', '')
    strength = yong_shen_info.get('strength', '')
    lines.append(f"▶ 日主强弱：{strength}")

    # 日主强弱经典理论（来自 classic-wisdom.json）
    ri_zhu_theory = CLASSIC_WISDOM.get('ziping_zhenjian', {}).get('key_passages', {}).get('ri_zhu_qiang_ruo', '')
    if ri_zhu_theory:
        lines.append(f"  理论依据：「{ri_zhu_theory}」")

    tiaohou = yong_shen_info.get('tiaohou')
    if tiaohou:
        lines.append(f"▶ 调候参考（穷通宝鉴）：{tiaohou['note']}")

    yong = yong_shen_info.get('yong_shen', '')
    yong2 = yong_shen_info.get('yong_shen_secondary', '')
    xi_shen = yong_shen_info.get('xi_shen', [])
    xiang_shen = yong_shen_info.get('xiang_shen', [])
    reason = yong_shen_info.get('yong_shen_reason', '')
    lines.append(f"▶ 用神：{yong}（取用方法：{method}）")
    if yong2:
        lines.append(f"  辅用神：{yong2}")
    if xi_shen:
        lines.append(f"  喜神：{'、'.join(xi_shen)}（生助用神，间接有利）")
    if xiang_shen:
        lines.append(f"  相神：{'、'.join(xiang_shen)}（帮扶日主，日主偏弱时尤为重要）")
    if reason:
        lines.append(f"  取用依据：{reason}")

    # 用神理论（来自 classic-wisdom.json）
    yong_shen_theory = CLASSIC_WISDOM.get('di_tian_sui', {}).get('key_passages', {}).get('yong_shen_qi_ji', '')
    if yong_shen_theory:
        lines.append(f"  《滴天髓》：「{yong_shen_theory}」")

    ji_list = yong_shen_info.get('ji_shen', [])
    if ji_list:
        # 检查忌神里是否有调候用神，加注说明
        tiaohou_info = yong_shen_info.get('tiaohou')
        tiaohou_yong = tiaohou_info['yong'][0] if tiaohou_info and tiaohou_info.get('yong') else ''
        ji_parts = []
        for j in ji_list:
            if j == tiaohou_yong:
                ji_parts.append(f'{j}（调候参考，但日主已{strength}，火生土反为害）')
            else:
                ji_parts.append(j)
        lines.append(f"▶ 忌神：{'、'.join(ji_parts)}")

    temp = yong_shen_info.get('temp_score', 0)
    if temp:
        label = '偏暖燥' if temp > 0 else '偏寒湿'
        lines.append(f"▶ 寒暖：{label}（{temp:+d}分）")

    return '\n'.join(lines)
