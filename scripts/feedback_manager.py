#!/usr/bin/env python3
"""
フィードバック学習マネージャー
ユーザーフィードバックを記録し、将来の分析精度を向上させる
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class FeedbackManager:
    """フィードバックを管理し、学習データを蓄積するクラス"""
    
    def __init__(self, feedback_dir: str = "data/feedback"):
        self.feedback_dir = Path(feedback_dir)
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_path = self.feedback_dir / "knowledge_base.json"
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """既存の知識ベースを読み込む"""
        if self.knowledge_base_path.exists():
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                self.knowledge_base = json.load(f)
        else:
            self.knowledge_base = {
                "entities": {},
                "relationships": {},
                "workflows": {},
                "corrections": []
            }
    
    def save_knowledge_base(self):
        """知識ベースを保存"""
        with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
    
    def record_entity_correction(self, original: Dict, corrected: Dict, context: str):
        """人物・組織の修正を記録"""
        correction = {
            "timestamp": datetime.now().isoformat(),
            "type": "entity",
            "original": original,
            "corrected": corrected,
            "context": context
        }
        
        # 知識ベースに追加
        entity_name = corrected.get('name', '')
        if entity_name:
            self.knowledge_base['entities'][entity_name] = {
                "correct_info": corrected,
                "common_mistakes": [original] if original != corrected else [],
                "last_updated": datetime.now().isoformat()
            }
        
        self.knowledge_base['corrections'].append(correction)
        self.save_knowledge_base()
        logger.info(f"Entity correction recorded: {entity_name}")
    
    def record_workflow_correction(self, original: Dict, corrected: Dict, context: str):
        """ワークフローの修正を記録"""
        correction = {
            "timestamp": datetime.now().isoformat(),
            "type": "workflow",
            "original": original,
            "corrected": corrected,
            "context": context
        }
        
        workflow_name = corrected.get('name', '')
        if workflow_name:
            self.knowledge_base['workflows'][workflow_name] = {
                "correct_flow": corrected,
                "variations": [original] if original != corrected else [],
                "last_updated": datetime.now().isoformat()
            }
        
        self.knowledge_base['corrections'].append(correction)
        self.save_knowledge_base()
        logger.info(f"Workflow correction recorded: {workflow_name}")
    
    def get_entity_knowledge(self, name: str) -> Optional[Dict]:
        """特定の人物・組織の知識を取得"""
        return self.knowledge_base['entities'].get(name)
    
    def get_workflow_knowledge(self, name: str) -> Optional[Dict]:
        """特定のワークフローの知識を取得"""
        return self.knowledge_base['workflows'].get(name)
    
    def apply_known_corrections(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """既知の修正を分析結果に適用"""
        corrected = analysis.copy()
        
        # 人物情報の修正
        if 'identified_persons' in corrected:
            for person in corrected['identified_persons']:
                name = person.get('name', '')
                known_info = self.get_entity_knowledge(name)
                if known_info:
                    # 既知の正しい情報で更新
                    person.update(known_info['correct_info'])
        
        # ワークフローの修正
        if 'workflows' in corrected:
            for workflow in corrected['workflows']:
                name = workflow.get('name', '')
                known_info = self.get_workflow_knowledge(name)
                if known_info:
                    workflow.update(known_info['correct_flow'])
        
        return corrected
    
    def generate_feedback_report(self) -> str:
        """学習内容のレポートを生成"""
        report = ["=== フィードバック学習レポート ===\n"]
        
        # 登録された人物・組織
        if self.knowledge_base['entities']:
            report.append("📚 学習した人物・組織:")
            for name, info in self.knowledge_base['entities'].items():
                correct = info['correct_info']
                report.append(f"  • {name} - {correct.get('role', '')} ({correct.get('department', '')})")
        
        # 登録されたワークフロー
        if self.knowledge_base['workflows']:
            report.append("\n📚 学習したワークフロー:")
            for name, info in self.knowledge_base['workflows'].items():
                report.append(f"  • {name}")
        
        # 修正履歴
        corrections = self.knowledge_base['corrections'][-5:]  # 最新5件
        if corrections:
            report.append("\n📝 最近の修正履歴:")
            for c in corrections:
                report.append(f"  • {c['timestamp'][:10]} - {c['type']}修正")
        
        return "\n".join(report)


class InteractiveFeedbackCollector:
    """対話的にフィードバックを収集するクラス"""
    
    def __init__(self, feedback_manager: FeedbackManager):
        self.feedback_manager = feedback_manager
    
    def collect_feedback(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """分析結果に対するフィードバックを収集"""
        print("\n" + "=" * 60)
        print("📝 フィードバック収集")
        print("=" * 60)
        
        # 既知の修正を適用
        corrected_analysis = self.feedback_manager.apply_known_corrections(analysis)
        
        if corrected_analysis != analysis:
            print("\n✨ 過去の学習内容を反映しました")
        
        # フィードバックオプションを表示
        print("\n修正したい項目を選択してください:")
        print("1. 人物情報の修正")
        print("2. ワークフローの修正")
        print("3. その他の修正")
        print("4. 修正なし（完了）")
        
        while True:
            choice = input("\n選択 (1-4): ").strip()
            
            if choice == '1':
                corrected_analysis = self._correct_persons(corrected_analysis)
            elif choice == '2':
                corrected_analysis = self._correct_workflows(corrected_analysis)
            elif choice == '3':
                print("その他の修正は手動で行ってください")
            elif choice == '4':
                break
            else:
                print("無効な選択です")
        
        return corrected_analysis
    
    def _correct_persons(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """人物情報を修正"""
        persons = analysis.get('identified_persons', [])
        if not persons:
            print("人物情報がありません")
            return analysis
        
        print("\n現在の人物リスト:")
        for i, person in enumerate(persons):
            print(f"{i+1}. {person['name']} - {person.get('role', '?')} ({person.get('department', '?')})")
        
        idx = input("\n修正する人物の番号 (0でキャンセル): ").strip()
        try:
            idx = int(idx)
            if idx == 0:
                return analysis
            if 1 <= idx <= len(persons):
                original = persons[idx-1].copy()
                
                # 修正内容を入力
                print(f"\n{original['name']}の情報を修正します")
                new_name = input(f"名前 [{original['name']}]: ").strip() or original['name']
                new_role = input(f"役割 [{original.get('role', '')}]: ").strip() or original.get('role', '')
                new_dept = input(f"部署 [{original.get('department', '')}]: ").strip() or original.get('department', '')
                
                # 更新
                persons[idx-1].update({
                    'name': new_name,
                    'role': new_role,
                    'department': new_dept
                })
                
                # 学習データとして記録
                self.feedback_manager.record_entity_correction(
                    original, persons[idx-1], 
                    f"User correction for {original['name']}"
                )
                
                print("✅ 修正を記録しました")
        except (ValueError, IndexError):
            print("無効な選択です")
        
        return analysis
    
    def _correct_workflows(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """ワークフロー情報を修正"""
        workflows = analysis.get('workflows', [])
        if not workflows:
            print("ワークフロー情報がありません")
            return analysis
        
        print("\n現在のワークフロー:")
        for i, wf in enumerate(workflows):
            print(f"{i+1}. {wf['name']}")
        
        # 同様の修正処理...
        return analysis


def create_feedback_enhanced_analyzer():
    """フィードバック学習機能付きアナライザーを作成"""
    from scripts.claude_integration import ClaudeCodeAnalyzer
    
    class FeedbackEnhancedAnalyzer(ClaudeCodeAnalyzer):
        def __init__(self):
            super().__init__()
            self.feedback_manager = FeedbackManager()
            self.feedback_collector = InteractiveFeedbackCollector(self.feedback_manager)
        
        def analyze_with_feedback(self, file_path: Path) -> Dict[str, Any]:
            """フィードバック学習を適用した分析"""
            # 基本分析
            analysis = self.analyze_with_claude(file_path)
            
            # 既知の修正を適用
            analysis = self.feedback_manager.apply_known_corrections(analysis)
            
            # 対話的改善
            final_analysis = self.feedback_collector.collect_feedback(analysis)
            
            return final_analysis
        
        def show_learning_report(self):
            """学習内容を表示"""
            print(self.feedback_manager.generate_feedback_report())
    
    return FeedbackEnhancedAnalyzer()


if __name__ == "__main__":
    # テスト実行
    analyzer = create_feedback_enhanced_analyzer()
    analyzer.show_learning_report()