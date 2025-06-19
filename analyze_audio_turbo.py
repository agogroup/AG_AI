#!/usr/bin/env python3
"""
音声ファイル分析専用スクリプト（Whisper Large V3 Turbo使用）
音声解析精度・効率向上版
"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from scripts.data_manager import DataManager
from scripts.audio_processor import AudioProcessor
import time

def main():
    """改良版音声分析の実行"""
    print("🚀 音声ファイル専用分析（Turbo改良版）")
    
    dm = DataManager()
    
    # 音声ファイルのみを取得
    files = dm.get_new_files()
    audio_files = [f for f in files if f.suffix.lower() in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']]
    
    if not audio_files:
        print("📭 処理対象の音声ファイルがありません")
        return
    
    print(f"🎵 {len(audio_files)}個の音声ファイルを処理します")
    
    # 改良版AudioProcessorの初期化（Turboモデル + 最適化設定）
    try:
        processor = AudioProcessor(
            model_size="turbo",  # Large V3 Turbo（6倍高速 + Large V2精度）
            device=None          # 自動デバイス選択（MPS/CUDA/CPU）
        )
        print(f"✅ Whisper Large V3 Turbo モデル初期化完了")
        print(f"   デバイス: {processor.device}")
        
    except Exception as e:
        print(f"❌ Turboモデルが利用できません、smallモデルで代替実行")
        processor = AudioProcessor(model_size="small")
    
    # 各音声ファイルを処理
    start_time = time.time()
    
    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(audio_files)}] {audio_file.name} を処理中...")
        
        try:
            # 改良版文字起こし実行
            result = processor.transcribe_audio(
                audio_file,
                language="ja"  # 日本語固定（精度大幅向上）
            )
            
            # 結果保存（日付フォルダ自動生成）
            from datetime import datetime
            today_folder = datetime.now().strftime("%Y-%m-%d")
            output_dir = Path("data/01_analyzed") / today_folder
            text_path, json_path = processor.save_transcription(
                result, 
                output_dir, 
                audio_file.stem
            )
            
            # ファイル移動
            success = dm.move_to_analyzed_folder(audio_file)
            if success:
                print(f"✅ 処理完了: {audio_file.name} → {output_dir.name}/{audio_file.name}")
            
            # 性能統計表示
            metadata = result['metadata']
            duration_min = int(metadata['audio_duration_sec'] // 60)
            duration_sec = int(metadata['audio_duration_sec'] % 60)
            processing_ratio = metadata['processing_time_sec'] / metadata['audio_duration_sec'] if metadata['audio_duration_sec'] > 0 else 0
            
            print(f"📊 処理統計:")
            print(f"   音声長さ: {duration_min}分{duration_sec}秒")
            print(f"   処理時間: {metadata['processing_time_sec']:.1f}秒")
            print(f"   処理比率: {processing_ratio:.2f}倍速")
            print(f"   文字数: {metadata['char_count']:,}文字")
            print(f"   使用モデル: Whisper {metadata['model_used']}")
            print(f"   デバイス: {metadata['device']}")
            
        except Exception as e:
            print(f"❌ {audio_file.name} の処理中にエラー: {e}")
            continue
    
    # 全体統計
    total_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"🎯 改良版音声分析完了")
    print(f"📊 処理されたファイル: {len(audio_files)}個")
    print(f"⏱️  総処理時間: {total_time:.1f}秒")
    print(f"📁 結果は data/01_analyzed/{dm.get_today_folder()}/ に保存されました")

if __name__ == "__main__":
    main() 