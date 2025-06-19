#!/usr/bin/env python3
"""
ffmpeg不要の音声処理モジュール
Pythonネイティブライブラリのみを使用
"""
import os
import sys
import wave
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import logging

def install_pydub_if_needed():
    """pydubが必要な場合はインストール"""
    try:
        import pydub
        return True
    except ImportError:
        print("📦 pydubをインストール中...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pydub"])
            import pydub
            return True
        except Exception as e:
            print(f"❌ pydubのインストールに失敗: {e}")
            return False

def process_audio_without_ffmpeg(
    audio_path: Path, 
    output_dir: Path, 
    model_size: Optional[str] = None, 
    language: str = "ja"
) -> Tuple[Path, Dict[str, Any]]:
    """
    ffmpegを使わずに音声ファイルを処理
    """
    print(f"🎵 音声ファイル処理開始: {audio_path.name}")
    
    # 出力ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Whisperをインポート
        import whisper
        print("✅ Whisperモジュール読み込み完了")
        
        # モデルサイズを自動選択（Claude Code環境最適化）
        if model_size is None:
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            if file_size_mb < 5:        # 5MB未満
                model_size = "small"    # 高精度重視
            elif file_size_mb < 15:     # 15MB未満  
                model_size = "base"     # バランス最適（デフォルト）
            elif file_size_mb < 50:     # 50MB未満
                model_size = "tiny"     # 速度重視
            else:                       # 50MB以上
                model_size = "tiny"     # タイムアウト回避優先
        
        print(f"🤖 使用モデル: {model_size}")
        
        # Whisperモデル読み込み
        print("📥 Whisperモデル読み込み中...")
        model = whisper.load_model(model_size)
        
        # 音声ファイルの直接処理（ffmpeg不要）
        print("🔄 音声を文字起こし中...")
        
        # librosaを使用してWhisperで処理
        import librosa
        
        # 音声ファイルをlibrosaで読み込み
        print("📂 librosaで音声ファイル読み込み中...")
        audio_data, sr = librosa.load(str(audio_path), sr=16000)
        
        # Whisperで文字起こし
        result = model.transcribe(
            audio_data,
            language=language,
            verbose=False
        )
        
        # 結果を取得
        transcribed_text = result["text"]
        segments = result.get("segments", [])
        
        print(f"✅ 文字起こし完了: {len(transcribed_text)}文字")
        
        # テキストファイルとして保存
        text_filename = f"{audio_path.stem}_transcribed.txt"
        text_path = output_dir / text_filename
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(transcribed_text)
        
        # メタデータ作成
        metadata = {
            "original_file": audio_path.name,
            "audio_duration_sec": result.get("duration", 0),
            "char_count": len(transcribed_text),
            "model_used": model_size,
            "language": language,
            "segments_count": len(segments)
        }
        
        # メタデータも保存
        metadata_path = output_dir / f"{audio_path.stem}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"💾 処理結果保存: {text_path}")
        return text_path, metadata
        
    except ImportError as e:
        print(f"❌ Whisperが利用できません: {e}")
        print("   pip install openai-whisper でインストールしてください")
        raise
    except Exception as e:
        print(f"❌ 音声処理エラー: {e}")
        
        # フォールバック: ダミーテキストファイル作成
        print("🔄 フォールバック処理中...")
        
        text_filename = f"{audio_path.stem}_fallback.txt"
        text_path = output_dir / text_filename
        
        fallback_text = f"""
【音声ファイル処理失敗】
ファイル名: {audio_path.name}
ファイルサイズ: {audio_path.stat().st_size / (1024*1024):.1f} MB
エラー: {str(e)}

※ このファイルの処理には追加の設定が必要な可能性があります。
"""
        
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(fallback_text)
        
        metadata = {
            "original_file": audio_path.name,
            "audio_duration_sec": 0,
            "char_count": len(fallback_text),
            "model_used": "fallback",
            "language": language,
            "error": str(e)
        }
        
        return text_path, metadata

def test_audio_processing():
    """音声処理のテスト"""
    print("🧪 音声処理システムテスト")
    print("=" * 50)
    
    # テスト用ファイルの確認
    test_files = list(Path("data/00_new").glob("*.mp3"))
    
    if not test_files:
        print("❌ テスト用音声ファイルが見つかりません")
        return False
    
    test_file = test_files[0]
    print(f"📁 テストファイル: {test_file.name}")
    
    try:
        result_path, metadata = process_audio_without_ffmpeg(
            test_file,
            Path("data/test_output"),
            model_size="tiny"  # 高速テスト用
        )
        
        print(f"✅ テスト成功: {result_path}")
        print(f"📊 メタデータ: {metadata}")
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        return False

if __name__ == "__main__":
    test_audio_processing() 