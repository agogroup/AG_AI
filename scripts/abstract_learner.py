#!/usr/bin/env python3
"""
抽象化学習モジュール
具体的な修正から一般的なパターンを抽出し、応用可能な知識として蓄積
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import defaultdict
import re
import logging

logger = logging.getLogger(__name__)


class PatternExtractor:
    """修正履歴からパターンを抽出するクラス"""
    
    def __init__(self):
        self.patterns = {
            "naming_patterns": [],
            "role_patterns": [],
            "org_patterns": [],
            "context_patterns": []
        }
    
    def extract_naming_patterns(self, corrections: List[Dict]) -> List[Dict]:
        """名前に関する修正パターンを抽出"""
        patterns = []
        
        for correction in corrections:
            if correction.get('type') == 'entity':
                original = correction.get('original', {})
                corrected = correction.get('corrected', {})
                
                orig_name = original.get('name', '')
                corr_name = corrected.get('name', '')
                
                # パターン1: 名前の省略形 → フルネーム
                if len(orig_name) < len(corr_name) and orig_name in corr_name:
                    patterns.append({
                        'type': 'abbreviation_to_fullname',
                        'example': f"{orig_name} → {corr_name}",
                        'rule': '短い名前は姓名の一部の可能性が高い',
                        'confidence_boost': -0.2  # 省略形の場合は信頼度を下げる
                    })
                
                # パターン2: 漢字の読み間違い
                if self._is_similar_reading(orig_name, corr_name):
                    patterns.append({
                        'type': 'kanji_misreading',
                        'example': f"{orig_name} → {corr_name}",
                        'rule': '似た読みの漢字に注意',
                        'check_similar_kanji': True
                    })
        
        return patterns
    
    def extract_role_patterns(self, corrections: List[Dict]) -> List[Dict]:
        """役職に関する修正パターンを抽出"""
        patterns = []
        role_upgrades = defaultdict(list)
        
        for correction in corrections:
            if correction.get('type') == 'entity':
                orig_role = correction.get('original', {}).get('role', '')
                corr_role = correction.get('corrected', {}).get('role', '')
                
                if orig_role and corr_role and orig_role != corr_role:
                    # 役職の格上げパターン
                    if self._is_role_upgrade(orig_role, corr_role):
                        role_upgrades['upgrade'].append({
                            'from': orig_role,
                            'to': corr_role,
                            'context': correction.get('context', '')
                        })
        
        # パターン化
        if len(role_upgrades['upgrade']) >= 2:
            patterns.append({
                'type': 'role_underestimation',
                'rule': '小規模組織では上位役職者が直接対応することが多い',
                'examples': role_upgrades['upgrade'],
                'action': 'consider_higher_roles'
            })
        
        return patterns
    
    def extract_org_patterns(self, corrections: List[Dict]) -> List[Dict]:
        """組織・所属に関するパターンを抽出"""
        patterns = []
        org_mistakes = []
        
        for correction in corrections:
            if correction.get('type') == 'entity':
                orig_dept = correction.get('original', {}).get('department', '')
                corr_dept = correction.get('corrected', {}).get('department', '')
                
                # フリーランス誤認パターン
                if 'フリーランス' in corr_dept and 'グループ' in orig_dept:
                    org_mistakes.append({
                        'pattern': 'freelance_misidentified_as_employee',
                        'indicator': '仲介的な動きをしている人物'
                    })
        
        if org_mistakes:
            patterns.append({
                'type': 'organization_affiliation',
                'rule': '仲介者やコーディネーターはフリーランスの可能性を考慮',
                'indicators': ['複数組織間の調整', '外部からの発注', '独立した立場での交渉']
            })
        
        return patterns
    
    def _is_similar_reading(self, name1: str, name2: str) -> bool:
        """似た読みの可能性があるかチェック"""
        # 簡易実装：文字数が同じで一部が共通
        return len(name1) == len(name2) and any(c in name2 for c in name1)
    
    def _is_role_upgrade(self, orig: str, corrected: str) -> bool:
        """役職が上位に修正されたかチェック"""
        lower_roles = ['担当', 'マネージャー', 'リーダー', '主任']
        higher_roles = ['社長', '代表', '取締役', 'CEO', 'オーナー']
        
        return any(l in orig for l in lower_roles) and any(h in corrected for h in higher_roles)


class AbstractLearner:
    """抽象的な学習を行うクラス"""
    
    def __init__(self, knowledge_base_path: str = "data/feedback/abstract_knowledge.json"):
        self.knowledge_path = Path(knowledge_base_path)
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)
        self.pattern_extractor = PatternExtractor()
        self.load_abstract_knowledge()
    
    def load_abstract_knowledge(self):
        """抽象的な知識を読み込む"""
        if self.knowledge_path.exists():
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                self.abstract_knowledge = json.load(f)
        else:
            self.abstract_knowledge = {
                "learned_patterns": [],
                "inference_rules": [],
                "context_rules": [],
                "meta_statistics": {
                    "total_corrections": 0,
                    "pattern_success_rate": {}
                }
            }
    
    def save_abstract_knowledge(self):
        """抽象的な知識を保存"""
        with open(self.knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(self.abstract_knowledge, f, ensure_ascii=False, indent=2)
    
    def learn_from_corrections(self, corrections: List[Dict]):
        """修正履歴から抽象的なパターンを学習"""
        # 各種パターンを抽出
        naming_patterns = self.pattern_extractor.extract_naming_patterns(corrections)
        role_patterns = self.pattern_extractor.extract_role_patterns(corrections)
        org_patterns = self.pattern_extractor.extract_org_patterns(corrections)
        
        # 新しいパターンを知識ベースに追加
        all_patterns = naming_patterns + role_patterns + org_patterns
        
        for pattern in all_patterns:
            if not self._is_duplicate_pattern(pattern):
                pattern['learned_at'] = datetime.now().isoformat()
                pattern['usage_count'] = 0
                pattern['success_rate'] = 1.0
                self.abstract_knowledge['learned_patterns'].append(pattern)
        
        # 推論ルールを生成
        self._generate_inference_rules(all_patterns)
        
        # 統計を更新
        self.abstract_knowledge['meta_statistics']['total_corrections'] = len(corrections)
        
        self.save_abstract_knowledge()
        logger.info(f"Learned {len(all_patterns)} new patterns from corrections")
    
    def _is_duplicate_pattern(self, pattern: Dict) -> bool:
        """既存のパターンと重複していないかチェック"""
        for existing in self.abstract_knowledge['learned_patterns']:
            if (existing.get('type') == pattern.get('type') and 
                existing.get('rule') == pattern.get('rule')):
                return True
        return False
    
    def _generate_inference_rules(self, patterns: List[Dict]):
        """パターンから推論ルールを生成"""
        rules = []
        
        # 名前に関するルール
        name_patterns = [p for p in patterns if 'naming' in p.get('type', '')]
        if len(name_patterns) >= 2:
            rules.append({
                'id': 'name_fullform_preference',
                'condition': 'ビジネスコンテキストでの人名',
                'action': 'フルネームを優先的に推定',
                'confidence_adjustment': 0.8
            })
        
        # 役職に関するルール
        role_patterns = [p for p in patterns if 'role' in p.get('type', '')]
        if role_patterns:
            rules.append({
                'id': 'small_org_executive_involvement',
                'condition': '小規模組織での直接的なやり取り',
                'action': '上位役職者の可能性を考慮',
                'role_candidates': ['代表', '社長', 'オーナー']
            })
        
        # 新しいルールを追加
        for rule in rules:
            if not any(r.get('id') == rule.get('id') for r in self.abstract_knowledge['inference_rules']):
                self.abstract_knowledge['inference_rules'].append(rule)
    
    def apply_abstract_knowledge(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """抽象的な知識を新しい分析に適用"""
        enhanced_analysis = analysis.copy()
        applied_patterns = []
        
        # 人物情報に対してパターンを適用
        if 'identified_persons' in enhanced_analysis:
            for person in enhanced_analysis['identified_persons']:
                # 名前のパターンチェック
                name_adjustments = self._apply_naming_patterns(person)
                if name_adjustments:
                    person.update(name_adjustments)
                    applied_patterns.append(f"名前パターン適用: {person['name']}")
                
                # 役職のパターンチェック
                role_adjustments = self._apply_role_patterns(person, enhanced_analysis)
                if role_adjustments:
                    person.update(role_adjustments)
                    applied_patterns.append(f"役職パターン適用: {person['role']}")
                
                # 組織のパターンチェック
                org_adjustments = self._apply_org_patterns(person, enhanced_analysis)
                if org_adjustments:
                    person.update(org_adjustments)
                    applied_patterns.append(f"組織パターン適用: {person['department']}")
        
        # 適用したパターンを記録
        if applied_patterns:
            enhanced_analysis['abstract_patterns_applied'] = applied_patterns
            logger.info(f"Applied {len(applied_patterns)} abstract patterns")
        
        return enhanced_analysis
    
    def _apply_naming_patterns(self, person: Dict) -> Optional[Dict]:
        """名前に関するパターンを適用"""
        adjustments = {}
        name = person.get('name', '')
        
        # 短い名前の場合、フルネームの可能性を示唆
        if len(name) <= 3 and not ' ' in name:
            for pattern in self.abstract_knowledge['learned_patterns']:
                if pattern.get('type') == 'abbreviation_to_fullname':
                    adjustments['name_confidence'] = 0.7
                    adjustments['name_note'] = 'フルネームではない可能性があります'
                    break
        
        return adjustments
    
    def _apply_role_patterns(self, person: Dict, full_analysis: Dict) -> Optional[Dict]:
        """役職に関するパターンを適用"""
        adjustments = {}
        current_role = person.get('role', '')
        
        # 小規模組織での役職推定
        for rule in self.abstract_knowledge['inference_rules']:
            if rule.get('id') == 'small_org_executive_involvement':
                # コンテキストから小規模組織かどうかを判断
                if self._is_small_organization_context(full_analysis):
                    if any(keyword in current_role for keyword in ['担当', 'マネージャー']):
                        adjustments['alternative_roles'] = rule.get('role_candidates', [])
                        adjustments['role_confidence'] = 0.6
        
        return adjustments
    
    def _apply_org_patterns(self, person: Dict, full_analysis: Dict) -> Optional[Dict]:
        """組織に関するパターンを適用"""
        adjustments = {}
        activities = person.get('activities', [])
        
        # フリーランスパターンのチェック
        freelance_indicators = ['仲介', '複数組織', '外部', '独立']
        if any(any(ind in act for ind in freelance_indicators) for act in activities):
            for pattern in self.abstract_knowledge['learned_patterns']:
                if pattern.get('type') == 'organization_affiliation':
                    adjustments['org_note'] = 'フリーランスまたは外部協力者の可能性'
                    adjustments['org_confidence'] = 0.7
                    break
        
        return adjustments
    
    def _is_small_organization_context(self, analysis: Dict) -> bool:
        """小規模組織のコンテキストかどうかを判断"""
        # 簡易的な判断: 識別された人物が5人以下
        persons = analysis.get('identified_persons', [])
        return len(persons) <= 5
    
    def generate_learning_report(self) -> str:
        """抽象的学習のレポートを生成"""
        report = ["=== 抽象的学習レポート ===\n"]
        
        # 学習したパターン
        patterns = self.abstract_knowledge['learned_patterns']
        if patterns:
            report.append(f"🧠 学習したパターン数: {len(patterns)}")
            
            # タイプ別に分類
            by_type = defaultdict(list)
            for p in patterns:
                by_type[p.get('type', 'unknown')].append(p)
            
            for ptype, items in by_type.items():
                report.append(f"\n📌 {ptype}:")
                for item in items[:3]:  # 最初の3つ
                    report.append(f"  - {item.get('rule', 'No rule')}")
                    if 'example' in item:
                        report.append(f"    例: {item['example']}")
        
        # 推論ルール
        rules = self.abstract_knowledge['inference_rules']
        if rules:
            report.append(f"\n🔧 生成された推論ルール: {len(rules)}")
            for rule in rules:
                report.append(f"  - {rule.get('condition')} → {rule.get('action')}")
        
        # 統計情報
        stats = self.abstract_knowledge['meta_statistics']
        report.append(f"\n📊 統計:")
        report.append(f"  - 総修正数: {stats.get('total_corrections', 0)}")
        
        return "\n".join(report)


class PreventiveLearner:
    """予防的な学習を行うクラス"""
    
    def __init__(self, abstract_learner: AbstractLearner):
        self.abstract_learner = abstract_learner
        self.warning_threshold = 0.7
    
    def analyze_potential_errors(self, analysis: Dict[str, Any]) -> List[Dict]:
        """潜在的なエラーを分析して警告を生成"""
        warnings = []
        
        # 人物情報のチェック
        for person in analysis.get('identified_persons', []):
            # 名前の警告
            if person.get('name_confidence', 1.0) < self.warning_threshold:
                warnings.append({
                    'type': 'name_uncertainty',
                    'target': person['name'],
                    'message': f"{person['name']}はフルネームではない可能性があります",
                    'suggestion': '正式な名前を確認してください'
                })
            
            # 役職の警告
            if person.get('role_confidence', 1.0) < self.warning_threshold:
                alt_roles = person.get('alternative_roles', [])
                if alt_roles:
                    warnings.append({
                        'type': 'role_uncertainty',
                        'target': person['name'],
                        'current': person.get('role'),
                        'alternatives': alt_roles,
                        'message': f"{person['name']}の役職は{alt_roles}の可能性もあります"
                    })
            
            # 組織の警告
            if person.get('org_confidence', 1.0) < self.warning_threshold:
                warnings.append({
                    'type': 'org_uncertainty',
                    'target': person['name'],
                    'message': person.get('org_note', '所属組織に不確実性があります')
                })
        
        return warnings
    
    def suggest_verifications(self, warnings: List[Dict]) -> List[str]:
        """警告に基づいて確認すべき項目を提案"""
        suggestions = []
        
        # 警告タイプ別に確認項目を生成
        name_warnings = [w for w in warnings if w['type'] == 'name_uncertainty']
        if name_warnings:
            suggestions.append("📝 以下の人物の正式名称を確認してください:")
            for w in name_warnings:
                suggestions.append(f"  - {w['target']}")
        
        role_warnings = [w for w in warnings if w['type'] == 'role_uncertainty']
        if role_warnings:
            suggestions.append("\n👤 以下の人物の正確な役職を確認してください:")
            for w in role_warnings:
                alts = ', '.join(w['alternatives'])
                suggestions.append(f"  - {w['target']}: 現在「{w['current']}」→ 可能性「{alts}」")
        
        org_warnings = [w for w in warnings if w['type'] == 'org_uncertainty']
        if org_warnings:
            suggestions.append("\n🏢 以下の人物の所属を再確認してください:")
            for w in org_warnings:
                suggestions.append(f"  - {w['target']}: {w['message']}")
        
        return suggestions


if __name__ == "__main__":
    # テスト実行
    learner = AbstractLearner()
    
    # サンプル修正データ
    sample_corrections = [
        {
            "timestamp": "2025-01-13T10:00:00",
            "type": "entity",
            "original": {"name": "まゆ", "role": "担当"},
            "corrected": {"name": "四ノ宮まゆ", "role": "製作担当"},
            "context": "フルネームへの修正"
        },
        {
            "timestamp": "2025-01-13T10:05:00",
            "type": "entity",
            "original": {"name": "りょうた", "role": "マネージャー"},
            "corrected": {"name": "菅野隆太", "role": "代表取締役社長"},
            "context": "役職の修正"
        }
    ]
    
    # パターン学習
    learner.learn_from_corrections(sample_corrections)
    
    # レポート表示
    print(learner.generate_learning_report())