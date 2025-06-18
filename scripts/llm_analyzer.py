#!/usr/bin/env python3
"""
LLMベースのインテリジェント分析システム
生データを直接解析し、インタラクティブに改善する
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """LLMを使用して生データを解析するクラス"""
    
    def __init__(self):
        self.analysis_history = []
        self.feedback_history = []
        
    def analyze_raw_text(self, text_path: Path) -> Dict[str, Any]:
        """生のテキストファイルを解析
        
        Args:
            text_path: 解析するテキストファイルのパス
            
        Returns:
            解析結果
        """
        with open(text_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # ここでLLMに解析を依頼する（実際の実装では API を使用）
        analysis = self._llm_analyze(content)
        
        # 解析履歴を保存
        self.analysis_history.append({
            'timestamp': datetime.now().isoformat(),
            'file': str(text_path),
            'analysis': analysis
        })
        
        return analysis
    
    def _llm_analyze(self, content: str) -> Dict[str, Any]:
        """LLMによる解析（プロトタイプ）"""
        # 実際の実装では、OpenAI API や Claude API を使用
        # ここでは解析結果の構造を示すサンプル
        
        analysis = {
            'summary': 'このテキストの要約',
            'identified_persons': [
                {
                    'name': '推定された人物名',
                    'role': '推定された役割',
                    'department': '推定された部署',
                    'activities': ['活動1', '活動2'],
                    'relationships': ['関係する人物']
                }
            ],
            'topics': ['議論されたトピック1', 'トピック2'],
            'workflows': [
                {
                    'name': '検出されたワークフロー',
                    'steps': ['ステップ1', 'ステップ2'],
                    'participants': ['参加者1', '参加者2']
                }
            ],
            'key_insights': [
                '重要な発見1',
                '重要な発見2'
            ],
            'confidence_scores': {
                'persons': 0.85,
                'workflows': 0.72,
                'topics': 0.90
            }
        }
        
        return analysis
    
    def present_analysis(self, analysis: Dict[str, Any]) -> str:
        """解析結果をわかりやすく提示"""
        presentation = []
        
        presentation.append("=== 解析結果 ===\n")
        
        # 要約
        presentation.append(f"【要約】\n{analysis['summary']}\n")
        
        # 識別された人物
        presentation.append("【識別された人物】")
        for person in analysis['identified_persons']:
            presentation.append(f"- {person['name']} ({person.get('role', '役割不明')})")
            if person.get('department'):
                presentation.append(f"  部署: {person['department']}")
            if person.get('activities'):
                presentation.append(f"  活動: {', '.join(person['activities'][:3])}")
        
        # 主要トピック
        presentation.append("\n【主要トピック】")
        for topic in analysis['topics']:
            presentation.append(f"- {topic}")
        
        # ワークフロー
        if analysis.get('workflows'):
            presentation.append("\n【検出されたワークフロー】")
            for wf in analysis['workflows']:
                presentation.append(f"- {wf['name']}")
                presentation.append(f"  ステップ: {' → '.join(wf['steps'])}")
        
        # 信頼度
        presentation.append("\n【解析の信頼度】")
        for key, score in analysis['confidence_scores'].items():
            presentation.append(f"- {key}: {score*100:.0f}%")
        
        presentation.append("\nこの解釈で正しいでしょうか？修正点があれば教えてください。")
        
        return "\n".join(presentation)
    
    def apply_feedback(self, analysis: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """ユーザーフィードバックを適用して解析を改善"""
        # フィードバックを記録
        self.feedback_history.append({
            'timestamp': datetime.now().isoformat(),
            'original_analysis': analysis,
            'feedback': feedback
        })
        
        # ここでLLMにフィードバックを伝えて再解析
        improved_analysis = self._improve_analysis_with_feedback(analysis, feedback)
        
        return improved_analysis
    
    def _improve_analysis_with_feedback(self, 
                                      original: Dict[str, Any], 
                                      feedback: str) -> Dict[str, Any]:
        """フィードバックに基づいて解析を改善"""
        # 実際の実装では、LLMにフィードバックを含めて再度解析を依頼
        # ここではサンプル実装
        
        improved = original.copy()
        
        # フィードバックに基づく簡単な改善例
        if "部署が違う" in feedback:
            # 部署情報を修正するロジック
            pass
        
        if "人物が抜けている" in feedback:
            # 人物を追加するロジック
            pass
        
        return improved
    
    def save_analysis_result(self, analysis: Dict[str, Any], output_path: Path):
        """解析結果を保存"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        logger.info(f"解析結果を保存しました: {output_path}")


class InteractiveAnalyzer:
    """対話的な分析を行うクラス"""
    
    def __init__(self):
        self.llm_analyzer = LLMAnalyzer()
        
    def analyze_file_interactively(self, file_path: Path):
        """ファイルを対話的に分析"""
        print(f"\n{file_path.name} を解析しています...\n")
        
        # 初回解析
        analysis = self.llm_analyzer.analyze_raw_text(file_path)
        
        # 結果を提示
        print(self.llm_analyzer.present_analysis(analysis))
        
        # フィードバックループ
        while True:
            feedback = input("\n修正点を入力してください（なければEnter、終了は'完了'）: ")
            
            if feedback.lower() in ['完了', 'done', 'ok']:
                break
            
            if feedback.strip():
                # フィードバックを適用
                analysis = self.llm_analyzer.apply_feedback(analysis, feedback)
                print("\n=== 改善された解析結果 ===")
                print(self.llm_analyzer.present_analysis(analysis))
        
        # 最終結果を保存
        output_path = Path("output/llm_analysis") / f"{file_path.stem}_analysis.json"
        self.llm_analyzer.save_analysis_result(analysis, output_path)
        
        print(f"\n解析結果を保存しました: {output_path}")
        
        return analysis


def main():
    """メイン実行関数"""
    analyzer = InteractiveAnalyzer()
    
    # data/raw 内のファイルを探索
    raw_files = []
    for ext in ['*.txt', '*.md', '*.csv']:
        raw_files.extend(Path("data/raw").rglob(ext))
    
    if not raw_files:
        print("data/raw にファイルが見つかりません。")
        return
    
    print("=== LLMベース インテリジェント分析システム ===")
    print("\n解析可能なファイル:")
    for i, file in enumerate(raw_files, 1):
        print(f"{i}. {file.relative_to('data/raw')}")
    
    choice = input("\n解析するファイルの番号を選択してください: ")
    
    try:
        selected_file = raw_files[int(choice) - 1]
        analyzer.analyze_file_interactively(selected_file)
    except (ValueError, IndexError):
        print("無効な選択です。")


if __name__ == "__main__":
    main()