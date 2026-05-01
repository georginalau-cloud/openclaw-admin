#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[20] lib/wuyu_analyzer.py - 妻财子禄寿五运分析引擎
调用层级：被 bin/bazi 调用
依赖：lib/ten_gods_analyzer.py [11]、lib/zhi_relations.py [10]

五运维度：
  妻（感情/婚姻）  财（财运/事业）  子（子女/后代）
  禄（官禄/地位）  寿（健康/寿元）

层级结构（强制，不可跳级）：
  原局（命局底色）
    └── 大运（10年背景）
          └── 流年（年度叠加）
                └── 流月（月度叠加）
                      └── 流日（日度叠加）

每一层分析都必须包含上层的影响，输出时明确标注各层贡献。
"""

import os
import sys
from typing import Dict, List

_LIB_DIR   = os.path.dirname(os.path.abspath(__file__))
_SKILL_DIR = os.path.dirname(_LIB_DIR)
sys.path.insert(0, os.path.join(_SKILL_DIR, "vendor"))

# ─────────────────────────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────────────────────────

GAN_WUXING = {
    "甲":"木","乙":"木","丙":"火","丁":"火","戊":"土",
    "己":"土","庚":"金","辛":"金","壬":"水","癸":"水",
}
ZHI_WUXING = {
    "子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火",
    "午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水",
}
ZHI_CANGYGAN = {
    "子":["癸"],"丑":["己","癸","辛"],"寅":["甲","丙","戊"],
    "卯":["乙"],"辰":["戊","乙","癸"],"巳":["丙","戊","庚"],
    "午":["丁","己"],"未":["己","丁","乙"],"申":["庚","壬","戊"],
    "酉":["辛"],"戌":["戊","辛","丁"],"亥":["壬","甲"],
}
SHISHEN_FULL = {
    "比":"比肩","劫":"劫财","食":"食神","伤":"伤官",
    "才":"偏财","财":"正财","杀":"七杀","官":"正官",
    "枭":"偏印","印":"正印","日主":"日主",
}
CHONG = {
    "子":"午","午":"子","丑":"未","未":"丑",
    "寅":"申","申":"寅","卯":"酉","酉":"卯",
    "辰":"戌","戌":"辰","巳":"亥","亥":"巳",
}
HE6 = {
    "子":"丑","丑":"子","寅":"亥","亥":"寅",
    "卯":"戌","戌":"卯","辰":"酉","酉":"辰",
    "巳":"申","申":"巳","午":"未","未":"午",
}
SANHE = [
    ({"申","子","辰"}, "水局"),
    ({"寅","午","戌"}, "火局"),
    ({"巳","酉","丑"}, "金局"),
    ({"亥","卯","未"}, "木局"),
]
SANHUI = [
    ({"寅","卯","辰"}, "木局", "东方三会"),
    ({"巳","午","未"}, "火局", "南方三会"),
    ({"申","酉","戌"}, "金局", "西方三会"),
    ({"亥","子","丑"}, "水局", "北方三会"),
]
XING = {
    "子":"卯","卯":"子",
    "寅":"巳","巳":"申","申":"寅",
    "丑":"戌","戌":"未","未":"丑",
}

WUYU_DIMS = {
    "qi":   {"name_male": "妻", "name_female": "夫", "label_male": "妻（感情/婚姻）", "label_female": "夫（感情/婚姻）"},
    "cai":  {"name_male": "财", "name_female": "财", "label_male": "财（财运/事业）", "label_female": "财（财运/事业）"},
    "zi":   {"name_male": "子", "name_female": "子", "label_male": "子（子女/后代）", "label_female": "子（子女/后代）"},
    "lu":   {"name_male": "禄", "name_female": "禄", "label_male": "禄（官禄/地位）", "label_female": "禄（官禄/地位）"},
    "shou": {"name_male": "寿", "name_female": "寿", "label_male": "寿（健康/寿元）", "label_female": "寿（健康/寿元）"},
}

def _dim_name(dim: str, gender: str) -> str:
    """根据性别返回维度名称（妻/夫）。"""
    key = "name_female" if gender == "female" else "name_male"
    return WUYU_DIMS[dim].get(key, WUYU_DIMS[dim].get("name_male", dim))

def _dim_label(dim: str, gender: str) -> str:
    """根据性别返回维度标签。"""
    key = "label_female" if gender == "female" else "label_male"
    return WUYU_DIMS[dim].get(key, WUYU_DIMS[dim].get("label_male", dim))

# 男命：妻=正财/偏财，财=财星+食伤，子=食伤，禄=官杀，寿=印比
# 女命：妻=官杀（夫星），财=财星+食伤，子=食伤，禄=官杀，寿=印比
WUYU_SHISHEN_MAP = {
    "male": {
        "qi":   ["财","才"],
        "cai":  ["财","才","食","伤"],
        "zi":   ["食","伤"],
        "lu":   ["官","杀"],
        "shou": ["印","枭","比","劫"],
    },
    "female": {
        "qi":   ["官","杀"],
        "cai":  ["财","才","食","伤"],
        "zi":   ["食","伤"],
        "lu":   ["官","杀"],
        "shou": ["印","枭","比","劫"],
    },
}

LAYER_WEIGHTS = {"原局": 3.0, "大运": 2.0, "流年": 1.5, "流月": 1.0, "流日": 0.5}


# ─────────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────────

def _gz_split(gz):
    if gz and len(gz) >= 2:
        return gz[0], gz[1]
    return None, None


def _get_interactions(zhi_a, zhi_set):
    """
    获取地支关系描述列表，调用统一的 zhi_relations 引擎。
    力量排序：三会 > 三合 > 六合 > 半三合 > 六冲 > 三刑 > 六害 > 相破
    """
    from .zhi_relations import analyze_zhi_relations
    result = analyze_zhi_relations(zhi_a, frozenset(zhi_set) - {zhi_a})
    # 返回描述列表（供原有逻辑使用）
    return [r['desc'] for r in result['relations']]


def _score_shishen(shishen, dim, gender):
    relevant = WUYU_SHISHEN_MAP.get(gender, WUYU_SHISHEN_MAP["male"]).get(dim, [])
    if shishen in relevant:
        return 2
    BAD_FOR = {
        "qi":   ["劫","比"],
        "cai":  ["劫","杀"],
        "zi":   ["杀","官"],
        "lu":   ["伤","食"],
        "shou": ["财","才"],
    }
    if shishen in BAD_FOR.get(dim, []):
        return -1
    return 0


# ─────────────────────────────────────────────────────────────────
# 单层分析
# ─────────────────────────────────────────────────────────────────

def _analyze_one_layer(gz, day_gan, gender, layer_name, yuanju_zhis):
    gan, zhi = _gz_split(gz)
    if not gan:
        return {}

    from .ten_gods_analyzer import get_ten_god
    shishen_gan  = get_ten_god(day_gan, gan)
    cangygan     = ZHI_CANGYGAN.get(zhi, [])
    shishen_zhi  = get_ten_god(day_gan, cangygan[0]) if cangygan else ""
    interactions = _get_interactions(zhi, yuanju_zhis)

    wuyu = {}
    for dim in WUYU_DIMS:
        score    = _score_shishen(shishen_gan, dim, gender)
        score   += _score_shishen(shishen_zhi, dim, gender) // 2
        notes    = []
        relevant = WUYU_SHISHEN_MAP.get(gender, WUYU_SHISHEN_MAP["male"]).get(dim, [])
        full_gan = SHISHEN_FULL.get(shishen_gan, shishen_gan)
        full_zhi = SHISHEN_FULL.get(shishen_zhi, shishen_zhi)
        dim_n    = _dim_name(dim, gender)  # 妻/夫/财/子/禄/寿

        if shishen_gan in relevant:
            notes.append(f"天干{gan}（{full_gan}）为{dim_n}星，{layer_name}有力")
        if shishen_zhi in relevant:
            notes.append(f"地支{zhi}藏{cangygan[0] if cangygan else ''}（{full_zhi}）为{dim_n}星，有根")

        for inter in interactions:
            if "冲" in inter:
                notes.append(f"{inter}，{dim_n}宫受冲，需防波动")
            elif "三会" in inter:
                notes.append(f"{inter}，{dim_n}宫五行大旺，影响显著")
            elif "三合" in inter:
                notes.append(f"{inter}，{dim_n}宫五行聚合，有助力")
            elif "六合" in inter:
                notes.append(f"{inter}，{dim_n}宫得合（合而不化），有稳定助力")
            elif "半合" in inter:
                notes.append(f"{inter}，{dim_n}宫小有聚合之力")
            elif "合" in inter:
                notes.append(f"{inter}，{dim_n}宫得合，有助力")
            elif "刑" in inter:
                notes.append(f"{inter}，{dim_n}宫受刑，需防摩擦")
            elif "害" in inter:
                notes.append(f"{inter}，{dim_n}宫受害，需防暗耗")
            elif "破" in inter:
                notes.append(f"{inter}，{dim_n}宫受破，轻微影响")

        wuyu[dim] = {
            "score":       max(-3, min(3, score)),
            "notes":       notes,
            "shishen_gan": shishen_gan,
            "shishen_zhi": shishen_zhi,
        }

    return {
        "gz":           gz,
        "layer":        layer_name,
        "gan_wuxing":   GAN_WUXING.get(gan, ""),
        "zhi_wuxing":   ZHI_WUXING.get(zhi, ""),
        "shishen_gan":  shishen_gan,
        "shishen_zhi":  shishen_zhi,
        "interactions": interactions,
        "wuyu":         wuyu,
    }


# ─────────────────────────────────────────────────────────────────
# 多层叠加
# ─────────────────────────────────────────────────────────────────

def _merge_layers(layers, gender):
    merged = {}
    for dim in WUYU_DIMS:
        total_score     = 0.0
        all_notes       = []
        layer_summaries = []

        for layer in layers:
            layer_name = layer.get("layer", "")
            w          = LAYER_WEIGHTS.get(layer_name, 1.0)
            dim_data   = layer.get("wuyu", {}).get(dim, {})
            score      = dim_data.get("score", 0)
            notes      = dim_data.get("notes", [])

            total_score += score * w
            if notes:
                all_notes.extend([f"[{layer_name}] {n}" for n in notes])
            layer_summaries.append({
                "layer": layer_name,
                "gz":    layer.get("gz", ""),
                "score": score,
                "notes": notes,
            })

        if total_score >= 3:
            rating = "大吉"
        elif total_score >= 1:
            rating = "小吉"
        elif total_score >= -1:
            rating = "平"
        elif total_score >= -3:
            rating = "需防"
        else:
            rating = "凶"

        merged[dim] = {
            "dim_name":        _dim_name(dim, gender),
            "dim_label":       _dim_label(dim, gender),
            "total_score":     round(total_score, 1),
            "rating":          rating,
            "notes":           all_notes,
            "layer_summaries": layer_summaries,
        }
    return merged


def _build_text(merged, layers, title):
    """
    生成五运分析文字报告。
    不只是罗列要点，而是对每个维度做叙述性分析：
    - 原局底色（命局先天基础）
    - 大运背景（10年运势走向）
    - 流年叠加（当年具体影响）
    - 综合评级与建议
    """
    lines = [f"【{title}】", "─" * 50]
    layer_desc = " → ".join(f"{l['layer']}（{l.get('gz', '')}）" for l in layers)
    lines.append(f"分析层级：{layer_desc}")
    lines.append("")

    # 评级说明
    rating_desc = {
        '大吉': '运势旺盛，宜主动出击，把握机遇',
        '小吉': '运势偏顺，稳步推进，可适度扩展',
        '平':   '运势平稳，维持现状，不宜大动',
        '需防': '运势偏弱，宜守不宜攻，注意防范',
        '凶':   '运势受阻，需谨慎行事，避免冒险',
    }

    for dim in WUYU_DIMS:
        d = merged[dim]
        rating = d['rating']
        label  = d['dim_label']
        notes  = d['notes']
        layer_summaries = d.get('layer_summaries', [])

        lines.append(f"▶ {label}  【{rating}】")
        lines.append(f"  总评：{rating_desc.get(rating, '')}")

        # 寿星维度加注释说明
        if dim == 'shou':
            lines.append(f"  注：寿星包含印星（生身）和比劫（帮身），均代表日主生命力的来源")

        # 按层级分组叙述
        for ls in layer_summaries:
            layer_name = ls['layer']
            gz         = ls.get('gz', '')
            layer_notes = ls.get('notes', [])

            if not layer_notes:
                if layer_name == '原局':
                    lines.append(f"  ◆ 原局底色：此维度命局中无明显星曜，先天基础中性")
                else:
                    lines.append(f"  ◆ {layer_name}（{gz}）：对此维度影响平稳，无特别加减")
                continue

            if layer_name == '原局':
                lines.append(f"  ◆ 原局底色（先天基础）：")
            elif layer_name == '大运':
                lines.append(f"  ◆ {gz}大运背景（10年走向）：")
            elif layer_name == '流年':
                lines.append(f"  ◆ {gz}流年叠加（当年影响）：")
            elif layer_name == '流月':
                lines.append(f"  ◆ {gz}流月（本月影响）：")
            elif layer_name == '流日':
                lines.append(f"  ◆ {gz}流日（今日影响）：")

            for note in layer_notes[:3]:
                lines.append(f"    • {note}")

        # 综合建议
        if rating in ('大吉', '小吉'):
            advice = _get_dim_positive_advice(dim)
        elif rating in ('需防', '凶'):
            advice = _get_dim_caution_advice(dim)
        else:
            advice = _get_dim_neutral_advice(dim)
        if advice:
            lines.append(f"  ➤ 建议：{advice}")

        lines.append("")

    return "\n".join(lines)


def _get_dim_positive_advice(dim: str) -> str:
    """运势好时的维度建议"""
    advice_map = {
        'qi':   '感情运顺，已婚者宜增进感情，未婚者可主动拓展社交，缘分易至',
        'cai':  '财运旺盛，可适度投资或拓展业务，正财偏财均有进账机会',
        'zi':   '子女缘好，已有子女者亲子关系融洽，有生育计划者时机较佳',
        'lu':   '事业运旺，宜主动争取晋升机会，贵人相助，名声地位有望提升',
        'shou': '健康状态良好，精力充沛，适合开展新计划，注意保持规律作息',
    }
    return advice_map.get(dim, '')


def _get_dim_caution_advice(dim: str) -> str:
    """运势弱时的维度建议"""
    advice_map = {
        'qi':   '感情易生波折，已婚者多沟通避免误解，未婚者不宜仓促定情，耐心等待',
        'cai':  '财运偏弱，宜守不宜攻，避免大额投资或借贷，谨防财务损失',
        'zi':   '子女缘稍弱，与子女相处需多耐心，有生育计划者可稍作等待',
        'lu':   '事业压力较大，宜低调行事，避免与上司冲突，守住现有成果为先',
        'shou': '健康需注意，宜定期体检，避免过度劳累，注意饮食作息规律',
    }
    return advice_map.get(dim, '')


def _get_dim_neutral_advice(dim: str) -> str:
    """运势平稳时的维度建议"""
    advice_map = {
        'qi':   '感情平稳，维持现状，用心经营即可',
        'cai':  '财运平稳，稳健理财，量入为出',
        'zi':   '子女关系平稳，多陪伴交流',
        'lu':   '事业平稳推进，积累实力，等待时机',
        'shou': '健康状态平稳，保持良好生活习惯',
    }
    return advice_map.get(dim, '')


# ─────────────────────────────────────────────────────────────────
# 主分析器
# ─────────────────────────────────────────────────────────────────

class WuyuAnalyzer:
    """妻财子禄寿五运分析器，接收 bazi_chart 完整输出。"""

    def __init__(self, chart):
        self.chart   = chart
        self.day_gan = chart.get("day_gan", "")
        gender_raw   = chart.get("meta", {}).get("gender", "male")
        self.gender  = "male" if gender_raw.lower() in ("male", "m", "男") else "female"
        pillars      = chart.get("pillars", [])
        self.yuanju_zhis = {p["zhi"] for p in pillars if "zhi" in p}
        self._yuanju_layer = self._build_yuanju_layer()

    def _build_yuanju_layer(self):
        from .ten_gods_analyzer import get_ten_god
        pillars = self.chart.get("pillars", [])
        wuyu = {dim: {"score": 0, "notes": [], "shishen_gan": "", "shishen_zhi": ""} for dim in WUYU_DIMS}

        for p in pillars:
            gan      = p.get("gan", "")
            zhi      = p.get("zhi", "")
            is_day   = (p.get("index") == 2)
            shishen_gan      = p.get("gan_shishen", "")
            cangygan_details = p.get("cangygan_details", [])

            for dim in WUYU_DIMS:
                relevant = WUYU_SHISHEN_MAP.get(self.gender, WUYU_SHISHEN_MAP["male"]).get(dim, [])
                score    = _score_shishen(shishen_gan, dim, self.gender)
                notes    = wuyu[dim]["notes"]
                full     = SHISHEN_FULL.get(shishen_gan, shishen_gan)
                dim_n    = _dim_name(dim, self.gender)

                if shishen_gan in relevant and not is_day:
                    notes.append(f"{p['name']}天干{gan}（{full}）为{dim_n}星")

                for cd in cangygan_details:
                    ss = cd.get("shishen", "")
                    if ss in relevant:
                        notes.append(
                            f"{p['name']}地支{zhi}藏{cd['gan']}"
                            f"（{SHISHEN_FULL.get(ss, ss)}）为{dim_n}星"
                        )
                        score += 1

                wuyu[dim]["score"] = min(3, wuyu[dim]["score"] + score)

        return {"gz": "原局", "layer": "原局", "wuyu": wuyu}

    def _layer(self, gz, name):
        return _analyze_one_layer(gz, self.day_gan, self.gender, name, self.yuanju_zhis)

    # ── 公开接口 ──────────────────────────────────────────────────

    def analyze_yuanju(self):
        """原局五运（命局底色）。"""
        layers = [self._yuanju_layer]
        merged = _merge_layers(layers, self.gender)
        return {"title": "原局五运分析", "layers": layers, "merged": merged,
                "text": _build_text(merged, layers, "原局五运分析")}

    def analyze_with_dayun(self, dayun_gz):
        """原局 + 大运。"""
        layers = [self._yuanju_layer, self._layer(dayun_gz, "大运")]
        merged = _merge_layers(layers, self.gender)
        title  = f"原局 × {dayun_gz}大运 五运分析"
        return {"title": title, "layers": layers, "merged": merged,
                "text": _build_text(merged, layers, title)}

    def analyze_with_liuyear(self, dayun_gz, year_gz):
        """原局 + 大运 + 流年（必须提供大运）。"""
        layers = [self._yuanju_layer, self._layer(dayun_gz, "大运"), self._layer(year_gz, "流年")]
        merged = _merge_layers(layers, self.gender)
        title  = f"原局 × {dayun_gz}大运 × {year_gz}流年 五运分析"
        return {"title": title, "layers": layers, "merged": merged,
                "text": _build_text(merged, layers, title)}

    def analyze_with_liuyue(self, dayun_gz, year_gz, month_gz):
        """原局 + 大运 + 流年 + 流月（必须提供大运和流年）。"""
        layers = [self._yuanju_layer, self._layer(dayun_gz, "大运"),
                  self._layer(year_gz, "流年"), self._layer(month_gz, "流月")]
        merged = _merge_layers(layers, self.gender)
        title  = f"原局 × {dayun_gz}大运 × {year_gz}流年 × {month_gz}流月 五运分析"
        return {"title": title, "layers": layers, "merged": merged,
                "text": _build_text(merged, layers, title)}

    def analyze_with_liuri(self, dayun_gz, year_gz, month_gz, day_gz):
        """原局 + 大运 + 流年 + 流月 + 流日（完整五层）。"""
        layers = [self._yuanju_layer, self._layer(dayun_gz, "大运"),
                  self._layer(year_gz, "流年"), self._layer(month_gz, "流月"),
                  self._layer(day_gz, "流日")]
        merged = _merge_layers(layers, self.gender)
        title  = f"原局 × {dayun_gz}大运 × {year_gz}流年 × {month_gz}流月 × {day_gz}流日 五运分析"
        return {"title": title, "layers": layers, "merged": merged,
                "text": _build_text(merged, layers, title)}

    def analyze_current(self):
        """自动分析当前时间点（原局 + 当前大运 + 当前流年）。"""
        current  = self.chart.get("current", {})
        if not current:
            return self.analyze_yuanju()
        dayun_gz = current.get("dayun", {}).get("ganzhi", "")
        liuyear  = current.get("liuyear", {})
        year_gz  = liuyear.get("ganzhi", "") if liuyear else ""
        if dayun_gz and year_gz:
            return self.analyze_with_liuyear(dayun_gz, year_gz)
        elif dayun_gz:
            return self.analyze_with_dayun(dayun_gz)
        return self.analyze_yuanju()

    def analyze_current_with_month(self, month_gz):
        """当前大运 + 当前流年 + 指定流月（不可跳过大运和流年）。"""
        current  = self.chart.get("current", {})
        dayun_gz = current.get("dayun", {}).get("ganzhi", "") if current else ""
        liuyear  = current.get("liuyear", {}) if current else {}
        year_gz  = liuyear.get("ganzhi", "") if liuyear else ""
        if not dayun_gz or not year_gz:
            return {"error": "无法获取当前大运或流年，无法分析流月"}
        return self.analyze_with_liuyue(dayun_gz, year_gz, month_gz)

    def analyze_current_with_day(self, month_gz, day_gz):
        """当前大运 + 当前流年 + 指定流月 + 指定流日（完整五层）。"""
        current  = self.chart.get("current", {})
        dayun_gz = current.get("dayun", {}).get("ganzhi", "") if current else ""
        liuyear  = current.get("liuyear", {}) if current else {}
        year_gz  = liuyear.get("ganzhi", "") if liuyear else ""
        if not dayun_gz or not year_gz:
            return {"error": "无法获取当前大运或流年，无法分析流日"}
        return self.analyze_with_liuri(dayun_gz, year_gz, month_gz, day_gz)
