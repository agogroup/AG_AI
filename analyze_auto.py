#!/usr/bin/env python3
"""
自動分析スクリプト（インタラクティブ入力なし）
"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from bin.analyze import IntelligentBusinessAnalyzer
from scripts.data_manager import DataManager

def auto_analyze():
    """全ファイルを自動的に分析"""
    print("🚀 AGO Group インテリジェント業務分析システム（自動モード）\n")
    
    analyzer = IntelligentBusinessAnalyzer()
    analyzer.auto_mode = True  # 自動モードを有効化
    dm = DataManager()
    
    # ファイルタイプ別に取得
    files_by_type = dm.get_new_files_by_type()
    total_files = sum(len(files) for files in files_by_type.values())
    
    if total_files == 0:
        print("📂 data/00_new/ にファイルが見つかりません")
        return
    
    print(f"🔍 {total_files}個のファイルを自動分析します\n")
    
    # 全ファイルを収集
    all_files = []
    
    if files_by_type['audio']:
        print(f"🎵 音声ファイル: {len(files_by_type['audio'])}個")
        for file in files_by_type['audio']:
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   - {file.name} ({size_mb:.1f} MB)")
            all_files.append(file)
    
    if files_by_type['text']:
        print(f"📄 テキストファイル: {len(files_by_type['text'])}個")
        for file in files_by_type['text']:
            print(f"   - {file.name}")
            all_files.append(file)
    
    print("\n" + "=" * 50 + "\n")
    
    # 全ファイルを分析（フィードバックなし）
    for i, file in enumerate(all_files, 1):
        print(f"[{i}/{total_files}] {file.name} を処理中...")
        try:
            analyzer._analyze_single_file(file)
            print(f"✅ {file.name} の分析完了\n")
        except Exception as e:
            print(f"❌ {file.name} の処理中にエラー: {e}\n")
            continue
    
    # サマリー表示
    analyzer._show_summary()
    
    print("\n✨ 自動分析が完了しました！")
    print(f"📊 処理されたファイル: {len(analyzer.results)}個")
    print("📁 結果は output/intelligent_analysis/ に保存されました")

if __name__ == "__main__":
    try:
        auto_analyze()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()