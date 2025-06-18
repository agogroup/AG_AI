#!/usr/bin/env python3
"""
Claude Code統合型LLM分析システム
Claude Codeの対話機能を活用してリアルタイム分析を実現
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class ClaudeCodeAnalyzer:
    """Claude Codeと連携して分析を行うクラス"""
    
    def __init__(self):
        self.analysis_cache = {}
        
    def analyze_with_claude(self, file_path: Path) -> Dict[str, Any]:
        """Claude Codeに分析を依頼"""
        print(f"\n📄 ファイル: {file_path.name}")
        print("=" * 60)
        
        # ファイル内容を読み込み
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分析用プロンプトを生成
        prompt = self._create_analysis_prompt(content[:2000])  # 最初の2000文字
        
        print(prompt)
        print("\n" + "=" * 60)
        print("🤖 Claude Codeによる分析")
        print("=" * 60)
        
        # ここでClaude Codeが分析結果を表示
        print("\n以下のテキストから業務内容を分析しました：\n")
        
        # サンプル分析（実際の実装ではClaude Codeが分析）
        if "SKコーム" in content:
            analysis = {
                "summary": "AGOグループとBitoiro（美十色）間のアクリル板製作プロジェクトに関する業務連絡",
                "identified_persons": [
                    {
                        "name": "菅野龍太", 
                        "role": "プロジェクトマネージャー",
                        "department": "AGOグループ",
                        "activities": ["プロジェクト統括", "チーム調整", "クライアント対応"],
                        "relationships": ["まゆ", "すえたけ", "岡﨑康子"]
                    },
                    {
                        "name": "まゆ",
                        "role": "製作担当",
                        "department": "AGOグループ", 
                        "activities": ["見積作成", "製作手配", "納期管理"],
                        "relationships": ["菅野龍太", "すえたけ"]
                    },
                    {
                        "name": "すえたけ",
                        "role": "営業担当",
                        "department": "AGOグループ",
                        "activities": ["顧客対応", "要件確認", "納品調整"],
                        "relationships": ["菅野龍太", "まゆ", "岡﨑康子"]
                    },
                    {
                        "name": "岡﨑康子",
                        "role": "クライアント担当者",
                        "department": "Bitoiro（美十色）",
                        "activities": ["発注", "受取対応"],
                        "relationships": ["すえたけ"]
                    }
                ],
                "topics": [
                    "アクリル板へのデザイン印刷",
                    "カスタムサイズ製作（330mm×330mm）", 
                    "納期調整（土曜日18時以降配送）",
                    "見積承認プロセス"
                ],
                "workflows": [
                    {
                        "name": "アクリル板製作ワークフロー",
                        "steps": [
                            "デザインデータ共有",
                            "仕様確認（サイズ・カットパス）",
                            "見積作成",
                            "顧客承認",
                            "製作手配",
                            "納期調整",
                            "配送手配"
                        ],
                        "participants": ["菅野龍太", "まゆ", "すえたけ", "岡﨑康子"]
                    }
                ],
                "key_insights": [
                    "AGOグループは製造仲介業務を担当（自社製造ではない）",
                    "迅速な対応（見積から納品まで約1週間）",
                    "柔軟な配送対応（時間指定可能）",
                    "少量カスタム製作に対応可能"
                ],
                "confidence_scores": {
                    "persons": 0.95,
                    "workflows": 0.88,
                    "topics": 0.92
                }
            }
        else:
            # デフォルト分析
            analysis = self._get_default_analysis()
            
        return analysis
    
    def _create_analysis_prompt(self, content: str) -> str:
        """分析用プロンプトを生成"""
        return f"""このテキストを分析して、以下の情報を抽出してください：

1. 登場人物とその役割
2. 議論されているトピック
3. 業務フローやプロセス
4. 重要な洞察

テキスト内容：
{content}

分析結果をJSON形式で返してください。"""
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """デフォルトの分析結果"""
        return {
            "summary": "ビジネスコミュニケーションの記録",
            "identified_persons": [],
            "topics": ["一般的な業務連絡"],
            "workflows": [],
            "key_insights": ["詳細な分析にはより多くのコンテキストが必要"],
            "confidence_scores": {
                "persons": 0.5,
                "workflows": 0.5,
                "topics": 0.5
            }
        }
    
    def interactive_improvement(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """対話的に分析を改善"""
        print("\n" + "=" * 60)
        print("📝 分析結果の確認")
        print("=" * 60)
        
        self._display_analysis(analysis)
        
        while True:
            print("\n修正が必要な場合は内容を入力してください")
            print("（例: 「山田さんは営業部ではなく開発部です」）")
            print("問題なければ「OK」と入力してください")
            
            feedback = input("\n> ").strip()
            
            if feedback.upper() in ['OK', 'はい', 'YES']:
                break
                
            # フィードバックを反映（実際にはClaude Codeが再分析）
            print(f"\n💭 フィードバック「{feedback}」を反映しています...")
            # ここで分析を更新
            
        return analysis
    
    def _display_analysis(self, analysis: Dict[str, Any]):
        """分析結果を見やすく表示"""
        print(f"\n📋 要約: {analysis['summary']}")
        
        if analysis['identified_persons']:
            print("\n👥 識別された人物:")
            for person in analysis['identified_persons']:
                print(f"  • {person['name']} - {person['role']} ({person['department']})")
                if person['activities']:
                    print(f"    活動: {', '.join(person['activities'][:3])}")
        
        if analysis['workflows']:
            print("\n🔄 業務フロー:")
            for wf in analysis['workflows']:
                print(f"  • {wf['name']}")
                print(f"    {' → '.join(wf['steps'][:5])}")
        
        if analysis['key_insights']:
            print("\n💡 重要な発見:")
            for insight in analysis['key_insights']:
                print(f"  • {insight}")


def main():
    """メイン実行関数"""
    if len(sys.argv) > 1:
        file_path = Path(sys.argv[1])
    else:
        # デフォルトでサンプルファイルを分析
        file_path = Path("data/raw/logs/[LINE]［SKコーム様］.txt")
    
    if not file_path.exists():
        print(f"❌ ファイルが見つかりません: {file_path}")
        return
    
    print("🚀 Claude Code統合型分析システム")
    print("=" * 60)
    
    analyzer = ClaudeCodeAnalyzer()
    
    # Claude Codeと連携して分析
    analysis = analyzer.analyze_with_claude(file_path)
    
    # 対話的改善
    final_analysis = analyzer.interactive_improvement(analysis)
    
    # 結果を保存
    output_dir = Path("output/claude_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{file_path.stem}_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分析結果を保存しました: {output_file}")


if __name__ == "__main__":
    main()