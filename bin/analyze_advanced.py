#!/usr/bin/env python3
"""
高度な分析システム - 抽象化学習機能付き
具体的な修正から一般的なパターンを学習し、類似ケースでの間違いを予防
"""
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any, List

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.feedback_manager import FeedbackManager, create_feedback_enhanced_analyzer
from scripts.abstract_learner import AbstractLearner, PreventiveLearner


class AdvancedBusinessAnalyzer:
    """抽象化学習機能を持つ高度なアナライザー"""
    
    def __init__(self):
        self.base_analyzer = create_feedback_enhanced_analyzer()
        self.feedback_manager = FeedbackManager()
        self.abstract_learner = AbstractLearner()
        self.preventive_learner = PreventiveLearner(self.abstract_learner)
        
        # 既存の修正履歴から抽象的パターンを学習
        self._learn_from_history()
    
    def _learn_from_history(self):
        """過去の修正履歴から学習"""
        knowledge_base = self.feedback_manager.knowledge_base
        corrections = knowledge_base.get('corrections', [])
        
        if corrections:
            print("📚 過去の修正履歴から学習中...")
            self.abstract_learner.learn_from_corrections(corrections)
            print("✅ 抽象的パターンの学習完了\n")
    
    def analyze_with_prevention(self, file_path: Path) -> Dict[str, Any]:
        """予防的な分析を実行"""
        print(f"\n🔍 {file_path.name} を高度な分析中...\n")
        
        # 基本分析
        analysis = self.base_analyzer.analyze_with_claude(file_path)
        
        # 抽象的知識を適用
        print("🧠 抽象的パターンを適用中...")
        enhanced_analysis = self.abstract_learner.apply_abstract_knowledge(analysis)
        
        # 潜在的エラーを検出
        warnings = self.preventive_learner.analyze_potential_errors(enhanced_analysis)
        
        if warnings:
            print("\n⚠️  潜在的な問題を検出しました:")
            print("=" * 60)
            suggestions = self.preventive_learner.suggest_verifications(warnings)
            for suggestion in suggestions:
                print(suggestion)
            print("=" * 60)
            
            # ユーザーに確認を促す
            self._interactive_verification(enhanced_analysis, warnings)
        else:
            print("✅ 高い信頼度で分析完了")
        
        # フィードバック収集
        final_analysis = self.base_analyzer.feedback_collector.collect_feedback(enhanced_analysis)
        
        # 新しい修正があれば抽象的パターンを更新
        self._update_abstract_patterns()
        
        return final_analysis
    
    def _interactive_verification(self, analysis: Dict[str, Any], warnings: List[Dict]):
        """警告に基づいて対話的に確認"""
        print("\n確認作業を開始しますか？ (y/n): ", end='')
        if input().lower() == 'y':
            for warning in warnings:
                if warning['type'] == 'name_uncertainty':
                    print(f"\n❓ {warning['target']}の正式名称は？")
                    print("(わからない場合はEnter): ", end='')
                    full_name = input().strip()
                    if full_name:
                        # 分析結果を更新
                        self._update_person_name(analysis, warning['target'], full_name)
                
                elif warning['type'] == 'role_uncertainty':
                    print(f"\n❓ {warning['target']}の正確な役職は？")
                    print(f"現在: {warning['current']}")
                    print(f"候補: {', '.join(warning['alternatives'])}")
                    print("(わからない場合はEnter): ", end='')
                    role = input().strip()
                    if role:
                        self._update_person_role(analysis, warning['target'], role)
    
    def _update_person_name(self, analysis: Dict, old_name: str, new_name: str):
        """人物名を更新"""
        for person in analysis.get('identified_persons', []):
            if person['name'] == old_name:
                person['name'] = new_name
                person['name_confidence'] = 1.0
                break
    
    def _update_person_role(self, analysis: Dict, name: str, new_role: str):
        """役職を更新"""
        for person in analysis.get('identified_persons', []):
            if person['name'] == name:
                person['role'] = new_role
                person['role_confidence'] = 1.0
                break
    
    def _update_abstract_patterns(self):
        """新しい修正から抽象的パターンを学習"""
        # 最新の修正を取得
        recent_corrections = self.feedback_manager.knowledge_base.get('corrections', [])[-5:]
        if recent_corrections:
            self.abstract_learner.learn_from_corrections(recent_corrections)
    
    def show_learning_status(self):
        """学習状況を表示"""
        print("\n" + "=" * 60)
        print("🎓 高度な学習状況")
        print("=" * 60)
        
        # 基本的な学習内容
        print("\n" + self.feedback_manager.generate_feedback_report())
        
        # 抽象的な学習内容
        print("\n" + self.abstract_learner.generate_learning_report())
        
        print("\n" + "=" * 60)


def demonstrate_abstract_learning():
    """抽象化学習のデモンストレーション"""
    print("🎯 抽象化学習のデモンストレーション")
    print("=" * 60)
    
    # シナリオ1: 名前の省略パターン
    print("\n📌 シナリオ1: 名前の省略パターン")
    print("具体例:")
    print("  - まゆ → 四ノ宮まゆ")
    print("  - りょうた → 菅野隆太")
    print("抽象化:")
    print("  → 「ビジネス文書では姓名フルネームが基本」")
    print("応用:")
    print("  → 次回「たけし」を見たら「○○たけし」の可能性を示唆")
    
    # シナリオ2: 役職の過小評価パターン
    print("\n📌 シナリオ2: 役職の過小評価パターン")
    print("具体例:")
    print("  - 菅野: PM → 社長")
    print("  - 岡﨑: 担当者 → 代表")
    print("抽象化:")
    print("  → 「小規模企業では代表者が直接対応」")
    print("応用:")
    print("  → 少人数での直接やり取り → 上位役職者の可能性大")
    
    # シナリオ3: 組織所属の誤認パターン
    print("\n📌 シナリオ3: 組織所属の誤認パターン")
    print("具体例:")
    print("  - 末武: AGO社員 → フリーランス")
    print("抽象化:")
    print("  → 「複数組織を仲介する人物は外部の可能性」")
    print("応用:")
    print("  → 仲介的な動きを検出 → フリーランスの可能性を警告")


def main():
    """メイン実行関数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demonstrate_abstract_learning()
        return
    
    print("🚀 AGO Group 高度な業務分析システム（抽象化学習機能付き）")
    print("=" * 60)
    
    analyzer = AdvancedBusinessAnalyzer()
    
    # 学習状況を表示
    analyzer.show_learning_status()
    
    # ファイル選択
    raw_files = list(Path("data/raw").rglob("*.txt"))
    if not raw_files:
        print("\n❌ data/raw/ にファイルが見つかりません")
        return
    
    print(f"\n📁 {len(raw_files)}個のファイルが見つかりました")
    for i, file in enumerate(raw_files, 1):
        print(f"{i}. {file.name}")
    
    choice = input("\n分析するファイル番号: ")
    try:
        selected_file = raw_files[int(choice) - 1]
    except (ValueError, IndexError):
        print("❌ 無効な選択です")
        return
    
    # 高度な分析を実行
    try:
        analysis = analyzer.analyze_with_prevention(selected_file)
        
        # 結果を保存
        output_dir = Path("output/advanced_analysis")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{selected_file.stem}_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析結果を保存: {output_file}")
        print("\n✅ 高度な分析完了！学習内容は次回の分析でさらに賢く活用されます")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 分析を中断しました")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()