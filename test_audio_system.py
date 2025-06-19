#!/usr/bin/env python3
"""
音声処理システムのテストスクリプト
音声ファイル対応の動作確認用
"""
import os
import sys
from pathlib import Path
import time

# プロジェクトルートをPythonパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from scripts.data_manager import DataManager
from scripts.audio_processor import AudioProcessor
from scripts.audio_processor_config import get_optimal_settings


def create_test_environment():
    """テスト環境をセットアップ"""
    print("🔧 テスト環境を準備中...")
    
    # テスト用ディレクトリ作成
    test_dir = Path("data/00_new")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # サンプルテキストファイル作成
    sample_text = test_dir / "sample_text.txt"
    with open(sample_text, 'w', encoding='utf-8') as f:
        f.write("これはテスト用のテキストファイルです。\n音声ファイルと一緒に処理されます。")
    
    print("✅ テスト環境の準備完了")
    print("\n📝 使い方:")
    print("1. 音声ファイル（.mp3, .wav等）を data/00_new/ に配置してください")
    print("2. その後、python analyze.py を実行してください")
    print("\n💡 ヒント: 音声ファイルがない場合は、以下のサンプルを試してください:")
    print("   - 会議の録音")
    print("   - インタビューの音声")
    print("   - プレゼンテーションの録画音声")


def test_file_detection():
    """ファイル検出機能のテスト"""
    print("\n" + "=" * 60)
    print("📂 ファイル検出テスト")
    print("=" * 60)
    
    dm = DataManager()
    files_by_type = dm.get_new_files_by_type()
    
    total_files = sum(len(files) for files in files_by_type.values())
    print(f"\n合計 {total_files} 個のファイルを検出:")
    
    if files_by_type['audio']:
        print(f"\n🎵 音声ファイル ({len(files_by_type['audio'])}個):")
        for file in files_by_type['audio']:
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"   - {file.name} ({size_mb:.1f} MB)")
            
            # 最適設定を表示
            settings = get_optimal_settings(file)
            print(f"     推奨モデル: {settings['model']}")
            print(f"     分割処理: {'必要' if settings['use_chunking'] else '不要'}")
    
    if files_by_type['text']:
        print(f"\n📄 テキストファイル ({len(files_by_type['text'])}個):")
        for file in files_by_type['text']:
            print(f"   - {file.name}")
    
    if total_files == 0:
        print("\n⚠️  ファイルが見つかりません")
        print("   data/00_new/ フォルダにファイルを配置してください")


def test_audio_processor():
    """音声処理機能のテスト"""
    print("\n" + "=" * 60)
    print("🎵 音声処理機能テスト")
    print("=" * 60)
    
    # Whisperモデルの確認
    try:
        import whisper
        print("\n✅ Whisperモジュールが正しくインストールされています")
        
        # 利用可能なモデルを表示
        print("\n📊 利用可能なWhisperモデル:")
        models = ["tiny", "base", "small", "medium", "large"]
        for model in models:
            print(f"   - {model}")
        
        # GPUの確認
        import torch
        if torch.cuda.is_available():
            print(f"\n🚀 GPU利用可能: {torch.cuda.get_device_name(0)}")
        else:
            print("\n💻 CPU モードで動作します")
            
    except ImportError as e:
        print(f"\n❌ Whisperのインストールが必要です:")
        print("   pip install openai-whisper")
        return


def test_processing_flow():
    """処理フロー全体のテスト"""
    print("\n" + "=" * 60)
    print("🔄 処理フロー統合テスト")
    print("=" * 60)
    
    dm = DataManager()
    files_by_type = dm.get_new_files_by_type()
    
    if files_by_type['audio']:
        print("\n音声ファイルの処理フローをシミュレート:")
        audio_file = files_by_type['audio'][0]
        
        print(f"\n1️⃣ ファイル検出: {audio_file.name}")
        print("2️⃣ ファイルタイプ判定: 音声ファイル")
        print("3️⃣ Whisper処理:")
        print("   - モデル選択")
        print("   - 文字起こし実行")
        print("   - テキスト保存")
        print("4️⃣ LLM解析:")
        print("   - 文字起こしテキストの分析")
        print("   - 人物・ワークフロー抽出")
        print("5️⃣ 結果保存:")
        print("   - JSON形式で保存")
        print("   - 処理済みフォルダへ移動")
        
        print("\n✅ 実際の処理は python analyze.py で実行してください")
    else:
        print("\n⚠️  音声ファイルが見つかりません")
        print("   処理フローのテストには音声ファイルが必要です")


def show_system_info():
    """システム情報を表示"""
    print("\n" + "=" * 60)
    print("💻 システム情報")
    print("=" * 60)
    
    # Python バージョン
    print(f"\nPython: {sys.version.split()[0]}")
    
    # 必要なモジュールの確認
    modules = {
        "whisper": "音声文字起こし",
        "torch": "深層学習フレームワーク",
        "torchaudio": "音声処理"
    }
    
    print("\n📦 モジュール状態:")
    for module, description in modules.items():
        try:
            __import__(module)
            print(f"✅ {module} - {description}")
        except ImportError:
            print(f"❌ {module} - {description} (要インストール)")
    
    # ディスク容量とメモリ情報
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        print(f"\n💾 空きディスク容量: {free_gb} GB")
        
        # メモリ情報
        import psutil
        memory = psutil.virtual_memory()
        print(f"💾 メモリ使用量: {memory.percent:.1f}% ({memory.available // (2**30)} GB 利用可能)")
        
        # CPUコア数
        cpu_count = psutil.cpu_count()
        print(f"⚡ CPUコア数: {cpu_count} コア")
        
    except ImportError:
        print("\n💡 詳細システム情報: pip install psutil でより詳しい情報を表示できます")
    except:
        pass


def main():
    """メイン実行関数"""
    print("🎯 AG_AI 音声処理システム テスト")
    print("=" * 60)
    
    # テスト実行
    create_test_environment()
    show_system_info()
    test_file_detection()
    test_audio_processor()
    test_processing_flow()
    
    print("\n" + "=" * 60)
    print("✨ テスト完了！")
    print("\n次のステップ:")
    print("1. 音声ファイルを data/00_new/ に配置")
    print("2. python analyze.py を実行")
    print("3. 音声が自動的に文字起こし → 分析されます")
    print("\n💡 ヒント: 初回実行時はWhisperモデルのダウンロードに時間がかかります")


if __name__ == "__main__":
    main()