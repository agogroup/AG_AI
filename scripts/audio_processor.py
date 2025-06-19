#!/usr/bin/env python3
"""
音声処理モジュール
Whisperを使用した音声ファイルの文字起こし機能
"""
import os
import sys
import time
import json
import torch
import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

try:
    import whisper
except ImportError:
    print("⚠️  whisperがインストールされていません。以下のコマンドでインストールしてください:")
    print("    pip install openai-whisper")
    sys.exit(1)

# date_utilsのインポート
try:
    from .date_utils import get_now
except ImportError:
    from date_utils import get_now


class AudioProcessor:
    """音声ファイルを処理するクラス"""
    
    def __init__(self, model_size: str = "turbo", device: Optional[str] = None):
        """
        初期化
        
        Args:
            model_size: Whisperモデルのサイズ（tiny, base, small, medium, large, turbo）
            device: 使用デバイス（None, cuda, cpu, mps）
            
        注意:
            デフォルトは'turbo'モデル（Large V3 Turbo - 高精度で6倍高速）
            MPSデバイス対応（M1/M2 Mac GPU最適化）
        """
        self.model_size = model_size
        
        # デバイスの自動選択とMPS対応（フォールバック機能付き）
        if device is None:
            # MPSが利用可能か試行、失敗時はCPUにフォールバック
            if torch.backends.mps.is_available():
                self.device = "mps"  # M1/M2 Mac GPU最適化（実際のテストは後で実行）
            elif torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
        else:
            self.device = device
            
        print(f"🔧 Whisperモデル初期化中... (モデル: {model_size}, デバイス: {self.device})")
        
        # モデルのロード（デバイスフォールバック対応）
        try:
            self.model = whisper.load_model(model_size, device=self.device)
            print(f"✅ Whisperモデル（{model_size}）のロード完了 - デバイス: {self.device}")
        except Exception as e:
            # MPSで失敗した場合、CPUにフォールバック
            if self.device == "mps":
                print(f"⚠️  MPS使用中にエラー発生、CPUにフォールバック中...")
                try:
                    self.device = "cpu"
                    self.model = whisper.load_model(model_size, device=self.device)
                    print(f"✅ Whisperモデル（{model_size}）のロード完了 - デバイス: {self.device} (フォールバック)")
                except Exception as fallback_error:
                    print(f"❌ CPUフォールバックも失敗: {fallback_error}")
                    raise
            else:
                print(f"❌ モデルのロードに失敗しました: {e}")
                raise
    
    def transcribe_audio(self, audio_path: Path, language: str = "ja") -> Dict:
        """
        音声ファイルを文字起こし
        
        Args:
            audio_path: 音声ファイルパス
            language: 言語コード（ja=日本語, en=英語, auto=自動検出）
        
        Returns:
            文字起こし結果の辞書
        """
        start_time = time.time()
        
        # ファイルサイズ確認
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        print(f"\n🎵 音声ファイル処理開始: {audio_path.name}")
        print(f"   サイズ: {file_size_mb:.1f} MB")
        
        try:
            # 最適化された文字起こし設定
            options = {
                "beam_size": 2,           # ビームサーチで精度向上
                "temperature": 0.0,       # 確定的デコード
                "best_of": 1,            # 高速化のため1回のみ
                "patience": 1.0          # デコード忍耐度
            }
            
            # 言語固定設定（精度大幅向上）
            if language != "auto":
                options["language"] = language
            
            # 文字起こし実行（最適化設定）
            print(f"   🚀 最適化文字起こし中... ({self.model_size}モデル + ビームサーチ)")
            result = self.model.transcribe(str(audio_path), **options)
            
            # 処理時間計算
            processing_time = time.time() - start_time
            
            # 音声の長さを推定（セグメントから）
            if result.get("segments"):
                audio_duration = result["segments"][-1]["end"]
            else:
                audio_duration = 0
            
            # 結果をまとめる
            transcription_result = {
                "text": result["text"],
                "language": result.get("language", language),
                "segments": result.get("segments", []),
                "metadata": {
                    "audio_file": audio_path.name,
                    "audio_size_mb": round(file_size_mb, 2),
                    "audio_duration_sec": round(audio_duration, 2),
                    "processing_time_sec": round(processing_time, 2),
                    "transcription_date": get_now(),
                    "model_used": self.model_size,
                    "device": self.device,
                    "char_count": len(result["text"]),
                    "detected_language": result.get("language", "unknown")
                }
            }
            
            # 処理完了メッセージ
            duration_min = int(audio_duration // 60)
            duration_sec = int(audio_duration % 60)
            print(f"✅ 文字起こし完了 ({duration_min}分{duration_sec}秒 → {len(result['text'])}文字)")
            print(f"   処理時間: {processing_time:.1f}秒")
            
            return transcription_result
            
        except Exception as e:
            print(f"❌ 文字起こしエラー: {e}")
            raise
    
    def save_transcription(self, result: Dict, output_dir: Path, base_filename: str):
        """
        文字起こし結果を保存
        
        Args:
            result: 文字起こし結果
            output_dir: 出力ディレクトリ
            base_filename: ベースファイル名（拡張子なし）
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # テキストファイル保存
        text_path = output_dir / f"{base_filename}_transcription.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            # ヘッダー情報
            f.write(f"【音声ファイル文字起こし】\n")
            f.write(f"ファイル名: {result['metadata']['audio_file']}\n")
            f.write(f"音声長さ: {result['metadata']['audio_duration_sec']}秒\n")
            f.write(f"文字起こし日時: {result['metadata']['transcription_date']}\n")
            f.write(f"使用モデル: Whisper {result['metadata']['model_used']}\n")
            f.write(f"検出言語: {result['metadata']['detected_language']}\n")
            f.write("=" * 60 + "\n\n")
            
            # 本文
            f.write(result['text'])
        
        # JSONファイル保存（詳細情報付き）
        json_path = output_dir / f"{base_filename}_transcription.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"📄 保存完了:")
        print(f"   - テキスト: {text_path.relative_to(output_dir.parent.parent)}")
        print(f"   - 詳細情報: {json_path.relative_to(output_dir.parent.parent)}")
        
        return text_path, json_path
    
    def estimate_processing_time(self, audio_path: Path) -> float:
        """
        処理時間の推定
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            推定処理時間（秒）
        """
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        
        # モデルサイズによる処理速度の目安（MB/秒）
        # 実測値に基づく推定（2025年6月実績 + Turbo対応）
        speed_estimates = {
            "tiny": 8.0,     # 実測: 高速だが精度やや劣る
            "base": 4.0,     # 実測: 速度と精度のバランス最適
            "small": 2.0,    # 実測: 高精度、やや重い
            "medium": 0.8,   # 実測: 2分タイムアウトリスク
            "large": 0.4,    # 実測: 非常に重い
            "turbo": 24.0    # 新実装: Large V2精度で6倍高速
        }
        
        speed = speed_estimates.get(self.model_size, 1.0)
        
        # GPU最適化によるさらなる高速化
        if self.device == "mps":       # M1/M2 Mac GPU
            speed *= 2.5
        elif self.device == "cuda":    # NVIDIA GPU
            speed *= 3
            
        return file_size_mb / speed
    
    def check_audio_quality(self, audio_path: Path) -> str:
        """
        音声ファイルの品質を推定してモデルサイズを推奨
        
        Args:
            audio_path: 音声ファイルパス
            
        Returns:
            推奨モデルサイズ
        """
        file_size_mb = audio_path.stat().st_size / (1024 * 1024)
        
        # ファイル名から品質を推定
        filename_lower = audio_path.name.lower()
        
        # 会議録音の場合
        if any(keyword in filename_lower for keyword in ['会議', 'meeting', 'zoom', 'teams', '録音']):
            return "medium"  # ノイズが多い可能性
        
        # インタビューの場合
        if any(keyword in filename_lower for keyword in ['interview', 'インタビュー', '対談']):
            return "small"  # 比較的クリア
        
        # ファイルサイズから推定（Claude Code環境最適化）
        if file_size_mb > 50:   # 大きいファイル（50MB超）
            return "tiny"       # タイムアウト回避優先
        elif file_size_mb > 20: # 中程度ファイル（20-50MB）
            return "base"       # バランス重視
        elif file_size_mb < 5:  # 小さいファイル（5MB未満）
            return "small"      # 高精度可能
        else:                   # 標準ファイル（5-20MB）
            return "base"       # デフォルト推奨


def process_audio_file(audio_path: Path, output_dir: Path, 
                      model_size: Optional[str] = None,
                      language: str = "ja") -> Tuple[Path, Dict]:
    """
    音声ファイルを処理するヘルパー関数
    
    Args:
        audio_path: 音声ファイルパス
        output_dir: 出力ディレクトリ
        model_size: モデルサイズ（Noneの場合は自動選択）
        language: 言語コード
        
    Returns:
        (テキストファイルパス, 文字起こし結果)
    """
    # モデルサイズの自動選択
    if model_size is None:
        processor_temp = AudioProcessor(model_size="tiny")  # 品質チェック用
        model_size = processor_temp.check_audio_quality(audio_path)
        print(f"🤖 自動選択されたモデル: {model_size}")
    
    # 音声処理実行
    processor = AudioProcessor(model_size=model_size)
    
    # 処理時間推定
    estimated_time = processor.estimate_processing_time(audio_path)
    if estimated_time > 60:
        print(f"⏱️  推定処理時間: {int(estimated_time // 60)}分{int(estimated_time % 60)}秒")
    else:
        print(f"⏱️  推定処理時間: {int(estimated_time)}秒")
    
    # 文字起こし実行
    result = processor.transcribe_audio(audio_path, language=language)
    
    # 結果保存
    base_filename = audio_path.stem
    text_path, json_path = processor.save_transcription(result, output_dir, base_filename)
    
    return text_path, result


def main():
    """テスト用メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python audio_processor.py <音声ファイル>")
        print("オプション:")
        print("  --model <size>    モデルサイズ (tiny/base/small/medium/large)")
        print("  --lang <code>     言語コード (ja/en/auto)")
        sys.exit(1)
    
    audio_file = Path(sys.argv[1])
    if not audio_file.exists():
        print(f"❌ ファイルが見つかりません: {audio_file}")
        sys.exit(1)
    
    # オプション解析
    model_size = None
    language = "ja"
    
    for i, arg in enumerate(sys.argv):
        if arg == "--model" and i + 1 < len(sys.argv):
            model_size = sys.argv[i + 1]
        elif arg == "--lang" and i + 1 < len(sys.argv):
            language = sys.argv[i + 1]
    
    # 出力ディレクトリ
    output_dir = Path("data/01_analyzed") / datetime.now().strftime("%Y-%m-%d")
    
    # 処理実行
    try:
        text_path, result = process_audio_file(
            audio_file, output_dir, model_size, language
        )
        print(f"\n✨ 処理完了！")
        print(f"文字数: {result['metadata']['char_count']}")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()