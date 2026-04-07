#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字五运分析系统（感情、财富、后代、禄运、寿运）
基于调候、病药、格局、喜用神的深度分析

术语说明：
- shishen: 十神（正财、偏财、正官、七煞、正印、偏印、伤官、食神、比肩、劫财）
- wangshuai: 旺衰 - 天干地支在十二长生中的旺衰状态
- nayin: 纳音五行 - 天干地支组合对应的五行属性
"""

import json
import re
from typing import Dict, List

class BaziFortuneAnalyzer:
    """八字五运分析器"""
    
    def __init__(self, bazi_data: Dict, full_report: str):
        """
        初始化分析器
        bazi_data: 原局四柱数据 {'year': '己巳', 'month': '丁丑', 'day': '庚辰', 'hour': '庚辰'}
        full_report: 完整的八字分析报告文本
        """
        self.ganzhi = bazi_data
        self.report = full_report
        self.dayun = self._parse_dayun()
        
    def _parse_dayun(self) -> List[Dict]:
        """提取大运信息"""
        dayun_list = []
        
        # 大运数据行格式:
        # 44       壬申 建 剑锋金    食:壬＋合丁　　　　空申＋建 - 庚比　壬食　戊枭
        pattern = r'^(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+?)(?:\n|$)'
        
        for line in self.report.split('\n'):
            line = line.strip()
            if not line or not re.match(r'^\d+\s+\S+\s+\S+\s+\S+', line):
                continue
            
            match = re.match(pattern, line)
            if match:
                age = int(match.group(1))
                ganzhi = match.group(2)
                wangshuai = match.group(3)  # 旺衰状态
                nayin = match.group(4)       # 纳音五行
                detail = match.group(5)
                
                shishen_dict = self._extract_shishen(detail)
                relations = self._extract_dayun_relations(detail)
                
                dayun_list.append({
                    'age': age,
                    'ganzhi': ganzhi,
                    'wangshuai': wangshuai,  # 旺衰
                    'nayin': nayin,          # 纳音五行
                    'detail': detail,
                    'shishen': shishen_dict, # 十神
                    'relations': relations
                })
        
        return dayun_list
    
    def _extract_shishen(self, text: str) -> Dict:
        """从文本中提取十神信息"""
        shishen = {}
        pattern = r'(\S+?):([^\s　]+)'
        for match in re.finditer(pattern, text):
            name = match.group(1).strip()
            symbol = match.group(2).strip()
            shishen[name] = symbol
        return shishen
    
    def _extract_dayun_relations(self, text: str) -> Dict:
        """从大运详情中提取干支关系"""
        relations = {
            'chong': [],
            'xing': [],
            'hai': [],
            'he': [],
            'po': []
        }
        
        if '冲' in text:
            matches = re.findall(r'冲:?(\S+)', text)
            relations['chong'] = matches
        if '刑' in text:
            matches = re.findall(r'刑:?(\S+)', text)
            relations['xing'] = matches
        if '害' in text:
            matches = re.findall(r'害:?(\S+)', text)
            relations['hai'] = matches
        if '合' in text:
            matches = re.findall(r'合:?(\S+)', text)
            relations['he'] = matches
        if '破' in text:
            matches = re.findall(r'破:?(\S+)', text)
            relations['po'] = matches
        
        return relations
    
    def _ensure_dayun_fields(self, dayun: Dict) -> Dict:
        """确保 dayun 有所有必需字段"""
        if 'shishen' not in dayun or not dayun['shishen']:
            dayun['shishen'] = {}
        if 'relations' not in dayun:
            dayun['relations'] = {'chong': [], 'xing': [], 'hai': [], 'he': [], 'po': []}
        if 'nayin' not in dayun:
            dayun['nayin'] = '未知'
        if 'wangshuai' not in dayun:
            dayun['wangshuai'] = '平'
        return dayun
    
    def analyze_intimate(self, dayun: Dict) -> Dict:
        """分析感情运"""
        dayun = self._ensure_dayun_fields(dayun)
        
        analysis = {
            'name': '感情运',
            'status': self._evaluate_status(dayun),
            'insights': []
        }
        
        shishen = dayun.get('shishen', {})
        
        # 检查财星（妻星）
        if '财' in shishen:
            symbol = shishen['财']
            if '＋' in symbol:
                analysis['insights'].append('财星透干，异性缘旺盛，感情易有机遇或发展')
            else:
                analysis['insights'].append('财星隐藏，感情较为内敛，需主动追求')
        
        # 检查旺衰
        wangshuai = dayun.get('wangshuai', '')
        wangshuai_meaning = self._get_wangshuai_meaning(wangshuai)
        if wangshuai_meaning:
            analysis['insights'].append(wangshuai_meaning)
        
        # 检查纳音
        nayin = dayun.get('nayin', '')
        if nayin:
            nayin_meaning = self._get_nayin_meaning(nayin, 'intimate')
            if nayin_meaning:
                analysis['insights'].append(nayin_meaning)
        
        # 检查干支关系
        relations = dayun.get('relations', {})
        if relations.get('chong'):
            analysis['insights'].append('大运冲克原局，感情可能有波折或转变')
        if relations.get('xing'):
            analysis['insights'].append('大运相刑，感情易有摩擦或冷淡')
        if relations.get('he'):
            analysis['insights'].append(f"大运相合，感情融洽，有利于婚配或巩固关系")
        
        return analysis
    
    def analyze_wealth(self, dayun: Dict) -> Dict:
        """分析财运"""
        dayun = self._ensure_dayun_fields(dayun)
        
        analysis = {
            'name': '财运',
            'status': self._evaluate_status(dayun),
            'insights': []
        }
        
        shishen = dayun.get('shishen', {})
        
        if '财' in shishen:
            symbol = shishen['财']
            if '＋' in symbol:
                analysis['insights'].append('财星透干，财运显露，收入增加，适合投资')
            else:
                analysis['insights'].append('财星隐藏，财运需耐心积累，稳健为上')
        
        if '官' in shishen or '杀' in shishen:
            analysis['insights'].append('官杀透干，事业推动财运，工作收入稳定')
        
        wangshuai = dayun.get('wangshuai', '')
        wangshuai_level = self._get_wangshuai_level(wangshuai)
        if wangshuai_level >= 4:
            analysis['insights'].append(f"大运处于{wangshuai}，身强气盛，适合主动投资理财")
        elif wangshuai_level <= 1:
            analysis['insights'].append(f"大运处于{wangshuai}，宜保守理财，积攒能量")
        
        nayin = dayun.get('nayin', '')
        if nayin:
            nayin_meaning = self._get_nayin_meaning(nayin, 'wealth')
            if nayin_meaning:
                analysis['insights'].append(nayin_meaning)
        
        relations = dayun.get('relations', {})
        if relations.get('chong'):
            analysis['insights'].append('大运冲克，事业可能有变动，财运受影响')
        if relations.get('he'):
            analysis['insights'].append('大运相合，事业顺畅，人脉助力财运')
        
        return analysis
    
    def analyze_children(self, dayun: Dict) -> Dict:
        """分析子运（后代）"""
        dayun = self._ensure_dayun_fields(dayun)
        
        analysis = {
            'name': '子运',
            'status': self._evaluate_status(dayun),
            'insights': []
        }
        
        shishen = dayun.get('shishen', {})
        
        if '食' in shishen:
            analysis['insights'].append('食神透干，子女宫活跃，此期易有子女运势变化')
        if '伤' in shishen:
            analysis['insights'].append('伤官透干，需多关注子女教育和健康')
        
        wangshuai = dayun.get('wangshuai', '')
        wangshuai_level = self._get_wangshuai_level(wangshuai)
        if wangshuai_level >= 4:
            analysis['insights'].append(f"大运旺地，子女聪慧，亲子关系融洽")
        elif wangshuai_level <= 1:
            analysis['insights'].append(f"大运衰地，需多陪伴子女，给予关心教导")
        
        relations = dayun.get('relations', {})
        if relations.get('xing') or relations.get('chong'):
            analysis['insights'].append('大运有刑冲，子女可能需要更多关注')
        
        return analysis
    
    def analyze_official(self, dayun: Dict) -> Dict:
        """分析禄运（事业福禄）"""
        dayun = self._ensure_dayun_fields(dayun)
        
        analysis = {
            'name': '禄运',
            'status': self._evaluate_status(dayun),
            'insights': []
        }
        
        shishen = dayun.get('shishen', {})
        
        if '官' in shishen:
            symbol = shishen['官']
            if '＋' in symbol:
                analysis['insights'].append('正官透干，事业机遇显露，升职有望')
            else:
                analysis['insights'].append('正官隐藏，事业运需耐心积累')
        
        if '杀' in shishen:
            analysis['insights'].append('七煞透干，事业中竞争压力大，需更强能力')
        
        wangshuai = dayun.get('wangshuai', '')
        if '建' in wangshuai:
            analysis['insights'].append('大运建禄，禄旺身强，事业正当其时，大有可为')
        elif '帝' in wangshuai:
            analysis['insights'].append('大运帝旺，运势巅峰，事业发展最佳时期')
        elif self._get_wangshuai_level(wangshuai) <= 1:
            analysis['insights'].append('大运衰弱，事业可能遇冷，宜低调积累')
        
        nayin = dayun.get('nayin', '')
        if nayin:
            nayin_meaning = self._get_nayin_meaning(nayin, 'official')
            if nayin_meaning:
                analysis['insights'].append(nayin_meaning)
        
        relations = dayun.get('relations', {})
        if relations.get('chong'):
            analysis['insights'].append('大运冲克，职场易有变动或冲突')
        if relations.get('he'):
            analysis['insights'].append('大运相合，人脉畅通，升职有助力')
        
        return analysis
    
    def analyze_longevity(self, dayun: Dict) -> Dict:
        """分析寿运（健康寿命）"""
        dayun = self._ensure_dayun_fields(dayun)
        
        analysis = {
            'name': '寿运',
            'status': self._evaluate_status(dayun),
            'insights': []
        }
        
        wangshuai = dayun.get('wangshuai', '')
        wangshuai_level = self._get_wangshuai_level(wangshuai)
        if wangshuai_level >= 4:
            analysis['insights'].append(f"大运处于{wangshuai}，身体强健，精力充沛")
        elif wangshuai_level <= 1:
            analysis['insights'].append(f"大运处于{wangshuai}，需多关注身体，定期体检")
        else:
            analysis['insights'].append(f"大运处于{wangshuai}，身体平稳，注意保养即可")
        
        if '墓' in wangshuai:
            analysis['insights'].append('大运入墓库，此期需特别关注健康，预防为主')
        
        nayin = dayun.get('nayin', '')
        if nayin:
            nayin_meaning = self._get_nayin_meaning(nayin, 'longevity')
            if nayin_meaning:
                analysis['insights'].append(nayin_meaning)
        
        relations = dayun.get('relations', {})
        if relations.get('chong'):
            analysis['insights'].append('大运冲克，容易出现身体不适，需加强预防')
        if relations.get('xing'):
            analysis['insights'].append('大运相刑，身体可能有小恙，宜及早防治')
        if relations.get('hai'):
            analysis['insights'].append('大运相害，暗中伤害健康，需提高警惕')
        
        return analysis
    
    def _evaluate_status(self, dayun: Dict) -> str:
        """评估总体状态"""
        wangshuai_level = self._get_wangshuai_level(dayun.get('wangshuai', ''))
        relations = dayun.get('relations', {})
        relations_count = sum([len(v) if v else 0 for v in relations.values()])
        
        if wangshuai_level >= 4 and relations_count == 0:
            return '吉'
        elif wangshuai_level <= 1 or (relations_count >= 2 and relations.get('chong')):
            return '凶'
        else:
            return '平'
    
    def _get_wangshuai_level(self, wangshuai: str) -> int:
        """获取旺衰等级"""
        if not wangshuai:
            return 2
        
        levels = {
            '帝': 5, '建': 4, '冠': 3, '长': 3,
            '沐': 2, '养': 2, '衰': 2,
            '胎': 1, '病': 1,
            '死': 0, '绝': 0, '墓': 0
        }
        
        for key, level in levels.items():
            if key in wangshuai:
                return level
        return 2
    
    def _get_wangshuai_meaning(self, wangshuai: str) -> str:
        """获取旺衰含义"""
        if not wangshuai:
            return ''
        
        meanings = {
            '帝': '大运帝旺，运势达到巅峰，各方面机遇叠加',
            '建': '大运建禄，禄旺身强，是积累和发展的好时期',
            '冠': '大运冠带，初展锋芒，逐渐展现实力',
            '长': '大运长生，生机旺盛，充满活力和希望',
            '沐': '大运沐浴，初生阶段，需要保护和培养',
            '养': '大运养地，积蓄阶段，缓慢积累能量',
            '胎': '大运胎地，孕育阶段，前景未明',
            '衰': '大运衰地，开始衰退，需要调整策略',
            '病': '大运病地，困顿阶段，需要坚持',
            '死': '大运死地，停滞不前，运势低迷',
            '绝': '大运绝地，绝望困顿，需要转变',
            '墓': '大运墓库，事物入库，需要发掘潜力'
        }
        
        for key, meaning in meanings.items():
            if key in wangshuai:
                return meaning
        return ''
    
    def _get_nayin_meaning(self, nayin: str, dimension: str) -> str:
        """根据纳音五行给出维度分析"""
        nayin_effects = {
            'intimate': {
                '金': '金纳音主坚硬，感情如刀刃，需要温柔对待',
                '木': '木纳音主生长，感情生机勃勃，易有新的缘份',
                '水': '水纳音主流动，感情易起易伏，需要稳定',
                '火': '火纳音主热烈，感情激情洋溢，但易躁动',
                '土': '土纳音主厚重，感情沉稳踏实，感情基础稳固'
            },
            'wealth': {
                '金': '金纳音主收敛，财运紧凑，需谨慎理财',
                '木': '木纳音主扩张，财运发展迅速，适合创业',
                '水': '水纳音主流动，财运流动变化，需要把握机遇',
                '火': '火纳音主消耗，财运需要主动开拓，容易虚耗',
                '土': '土纳音主积累，财运厚���稳固，适合储蓄投资'
            },
            'official': {
                '金': '金纳音主决断，事业果敢有力，易有领导机遇',
                '木': '木纳音主生发，事业蓬勃向上，升迁有望',
                '水': '水纳音主智慧，事业聪慧灵活，需要把握机遇',
                '火': '火纳音主显露，事业光芒显露，声名鹊起',
                '土': '土纳音主厚德，事业稳扎稳打，信誉良好'
            },
            'longevity': {
                '金': '金纳音主肃杀，需注意呼吸系统和秋冬季节',
                '木': '木纳音主生发，身体活力充足，适合运动',
                '水': '水纳音主寒冷，需注意肾系统和冬季保暖',
                '火': '火纳音主热烈，需注意心血管和夏季防暑',
                '土': '土纳音主稳重，脾胃功能较好，注意消化'
            }
        }
        
        dimension_map = nayin_effects.get(dimension, {})
        
        for element, meaning in dimension_map.items():
            if element in nayin:
                return meaning
        
        return ''

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 3:
        try:
            bazi_json = json.loads(sys.argv[1])
            full_report = sys.argv[2]
            fortune_type = sys.argv[3]
            dayun_json = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
            
            analyzer = BaziFortuneAnalyzer(bazi_json, full_report)
            
            methods = {
                'intimate': analyzer.analyze_intimate,
                'wealth': analyzer.analyze_wealth,
                'children': analyzer.analyze_children,
                'official': analyzer.analyze_official,
                'longevity': analyzer.analyze_longevity
            }
            
            method = methods.get(fortune_type)
            if method:
                target_dayun = dayun_json if dayun_json else (analyzer.dayun[-1] if analyzer.dayun else {})
                result = method(target_dayun)
            else:
                result = {'error': f'Unknown fortune type: {fortune_type}'}
            
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(json.dumps({'error': str(e)}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({'error': 'Usage: python3 fortune_analyzer.py <bazi_json> <full_report> <fortune_type> [dayun_json]'}, ensure_ascii=False, indent=2))
