#!/usr/bin/env python3
"""
Claude Code統合版 AGO Group インテリジェント業務分析システム
Claude Codeの能力を活用してリアルタイムで分析
"""
import os
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.claude_integration import ClaudeCodeAnalyzer


class ClaudeBusinessAnalyzer:
    """Claude Codeと連携してビジネスデータを分析"""
    
    def __init__(self):
        self.analyzer = ClaudeCodeAnalyzer()
        self.results = []
        
    def analyze_all_files(self):
        """data/raw内の全ファイルを分析"""
        raw_files = []
        raw_path = Path("data/raw")
        
        # 対応する拡張子
        extensions = ['*.txt', '*.md', '*.csv', '*.log', '*.json']
        
        for ext in extensions:
            raw_files.extend(raw_path.rglob(ext))
        
        if not raw_files:
            print("📂 data/raw/ にファイルが見つかりません")
            print("\n使い方：")
            print("1. data/raw/ フォルダに分析したいファイルを入れてください")
            print("   - LINEのトーク履歴")
            print("   - メールのテキスト")
            print("   - 議事録など")
            print("\n2. もう一度このスクリプトを実行してください")
            return
        
        print("🔍 Claude Code統合型 AGO Group インテリジェント業務分析システム")
        print("=" * 60)
        print(f"\n{len(raw_files)}個のファイルが見つかりました：\n")
        
        for i, file in enumerate(raw_files, 1):
            rel_path = file.relative_to(raw_path)
            print(f"{i}. 📄 {rel_path}")
        
        print("\n" + "=" * 60)
        print("\n💡 ヒント: Claude Codeが各ファイルの内容を読んで分析します")
        choice = input("\n分析するファイルを選択してください (番号 or 'all' で全て): ")
        
        if choice.lower() == 'all':
            for file in raw_files:
                self._analyze_single_file(file)
        else:
            try:
                selected = raw_files[int(choice) - 1]
                self._analyze_single_file(selected)
            except (ValueError, IndexError):
                print("❌ 無効な選択です")
                return
        
        self._show_summary()
    
    def _analyze_single_file(self, file_path: Path):
        """単一ファイルをClaude Codeで分析"""
        print(f"\n\n📊 {file_path.name} を分析中...\n")
        
        # Claude Code経由で分析
        analysis = self.analyzer.analyze_with_claude(file_path)
        
        # 対話的改善
        improved_analysis = self.analyzer.interactive_improvement(analysis)
        
        # 結果を保存
        self.results.append(improved_analysis)
        self._save_analysis(file_path, improved_analysis)
    
    def _save_analysis(self, file_path: Path, analysis: Dict[str, Any]):
        """解析結果を保存"""
        output_dir = Path("output/intelligent_analysis")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{file_path.stem}_analysis.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 解析結果を保存しました: {output_file}")
    
    def _show_summary(self):
        """全体のサマリーを表示"""
        if not self.results:
            return
        
        print("\n\n" + "=" * 60)
        print("📊 分析サマリー")
        print("=" * 60)
        
        # 全人物リスト
        all_persons = []
        for result in self.results:
            all_persons.extend(result.get('identified_persons', []))
        
        if all_persons:
            print("\n👥 識別された全人物:")
            unique_persons = {p['name']: p for p in all_persons}.values()
            for person in unique_persons:
                print(f"  • {person['name']} - {person['role']} ({person['department']})")
        
        # 主要なワークフロー
        all_workflows = []
        for result in self.results:
            all_workflows.extend(result.get('workflows', []))
        
        if all_workflows:
            print("\n🔄 検出されたワークフロー:")
            for wf in all_workflows[:3]:  # 最初の3つ
                print(f"  • {wf['name']}")
        
        print(f"\n✅ {len(self.results)}個のファイルの分析が完了しました")
        print("\n詳細は output/intelligent_analysis/ フォルダをご確認ください")


def show_instructions():
    """Claude Codeの使い方を表示"""
    print("\n" + "=" * 60)
    print("🤖 Claude Codeによる分析の仕組み")
    print("=" * 60)
    print("\n1. このスクリプトがファイルの内容を表示します")
    print("2. Claude（私）がその内容を読んで分析します")
    print("3. 分析結果が画面に表示されます")
    print("4. 間違いがあれば修正できます")
    print("\nAPI不要で、この会話の中で完結します！")
    

def main():
    """メイン実行関数"""
    print("🚀 Claude Code統合型 AGO Group インテリジェント業務分析システム 起動中...\n")
    
    show_instructions()
    
    analyzer = ClaudeBusinessAnalyzer()
    
    try:
        analyzer.analyze_all_files()
    except KeyboardInterrupt:
        print("\n\n⚠️  分析を中断しました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()