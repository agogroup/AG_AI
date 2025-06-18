#!/usr/bin/env python3
"""
スマート分析システム - フィードバック学習機能付き
過去の修正を記憶し、分析精度を向上させる
"""
import sys
from pathlib import Path
from datetime import datetime
import json
from typing import Dict, Any

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.feedback_manager import create_feedback_enhanced_analyzer
from scripts.data_manager import DataManager


class SmartBusinessAnalyzer:
    """フィードバック学習機能を持つスマートアナライザー"""
    
    def __init__(self):
        self.analyzer = create_feedback_enhanced_analyzer()
        self.data_manager = DataManager()
        
    def run_analysis(self):
        """メイン分析処理"""
        print("🧠 AGO Group スマート業務分析システム")
        print("=" * 60)
        print("過去の学習内容を活用して、より正確な分析を行います")
        print("=" * 60)
        
        # 学習内容を表示
        print("\n📚 現在の学習内容:")
        self.analyzer.show_learning_report()
        
        # ファイル選択 - 新しいデータ管理システムを使用
        raw_files = self.data_manager.get_new_files()
        if not raw_files:
            print("\n❌ data/00_new/ にファイルが見つかりません")
            print("\n使い方：")
            print("1. data/00_new/ フォルダに分析したいファイルを入れてください")
            return
        
        print(f"\n\n📁 {len(raw_files)}個のファイルが見つかりました")
        for i, file in enumerate(raw_files, 1):
            print(f"{i}. {file.name}")
        
        choice = input("\n分析するファイル番号: ")
        try:
            selected_file = raw_files[int(choice) - 1]
        except (ValueError, IndexError):
            print("❌ 無効な選択です")
            return
        
        # フィードバック学習を適用した分析
        print(f"\n\n🔍 {selected_file.name} を分析中...")
        analysis = self.analyzer.analyze_with_feedback(selected_file)
        
        # 結果を保存
        self._save_analysis(selected_file, analysis)
        
        print("\n✅ 分析完了！学習内容は次回の分析に活用されます")
    
    def _save_analysis(self, file_path: Path, analysis: Dict[str, Any]):
        """分析結果を保存し、ファイルを処理済みフォルダに移動"""
        output_dir = Path("output/smart_analysis")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{file_path.stem}_analysis.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 分析結果を保存: {output_file}")
        
        # データ管理システムで処理済みフォルダに移動
        self.data_manager.move_to_analyzed(
            file_path,
            str(output_file)
        )


def demo_feedback_learning():
    """フィードバック学習のデモ"""
    print("🎓 フィードバック学習機能のデモ")
    print("=" * 60)
    
    from scripts.feedback_manager import FeedbackManager
    
    fm = FeedbackManager()
    
    # サンプル修正を記録
    print("\n1️⃣ 誤った分析:")
    print("   菅野龍太 - プロジェクトマネージャー (AGOグループ)")
    
    print("\n2️⃣ ユーザーが修正:")
    print("   菅野隆太 - 代表取締役社長 (AGOグループ)")
    
    # 修正を記録
    fm.record_entity_correction(
        original={"name": "菅野龍太", "role": "プロジェクトマネージャー"},
        corrected={"name": "菅野隆太", "role": "代表取締役社長", "department": "AGOグループ"},
        context="ユーザーフィードバック"
    )
    
    print("\n3️⃣ 次回以降の分析:")
    print("   ✨ 自動的に「菅野隆太 - 代表取締役社長」として認識")
    
    # 学習内容を表示
    print("\n" + fm.generate_feedback_report())


def main():
    """メイン実行関数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo_feedback_learning()
    else:
        analyzer = SmartBusinessAnalyzer()
        try:
            analyzer.run_analysis()
        except KeyboardInterrupt:
            print("\n\n⚠️ 分析を中断しました")
        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()