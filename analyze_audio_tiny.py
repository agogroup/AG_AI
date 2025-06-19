#!/usr/bin/env python3
"""
音声ファイル分析専用スクリプト（tinyモデル使用）
"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from scripts.data_manager import DataManager
from scripts.audio_processor import process_audio_file
from datetime import datetime

def analyze_audio_files():
    """音声ファイルのみを分析"""
    print("🎵 音声ファイル専用分析（tinyモデル）\n")
    
    dm = DataManager()
    files_by_type = dm.get_new_files_by_type()
    
    if not files_by_type['audio']:
        print("音声ファイルが見つかりません")
        return
    
    audio_files = files_by_type['audio']
    print(f"🎵 {len(audio_files)}個の音声ファイルを処理します\n")
    
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path("data/01_analyzed") / today
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] {audio_file.name} を処理中...")
        size_mb = audio_file.stat().st_size / (1024 * 1024)
        print(f"   ファイルサイズ: {size_mb:.1f} MB")
        
        try:
            # tinyモデルを強制使用（高速処理）
            text_path, result = process_audio_file(
                audio_file, 
                output_dir, 
                model_size="tiny",  # 最軽量モデル
                language="ja"
            )
            
            print(f"✅ 文字起こし完了")
            print(f"   文字数: {result['metadata']['char_count']}")
            print(f"   処理時間: {result['metadata']['processing_time_sec']}秒\n")
            
            # ファイルを移動
            dm.move_to_analyzed(audio_file, str(text_path))
            
        except Exception as e:
            print(f"❌ エラー: {e}\n")
            continue
    
    print("✨ 音声処理完了！")

if __name__ == "__main__":
    try:
        analyze_audio_files()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()