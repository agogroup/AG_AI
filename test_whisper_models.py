import whisper
import time
import os

def test_model_switching():
    """モデル切り替えコストを測定"""
    print("🔍 Whisperモデル切り替えコスト測定")
    print("=" * 50)
    
    models = ['tiny', 'base', 'small', 'medium']
    results = {}
    
    for model_name in models:
        print(f'\n📦 {model_name.upper()} モデル')
        print("-" * 20)
        
        # ロード時間測定
        start = time.time()
        model = whisper.load_model(model_name)
        load_time = time.time() - start
        
        # モデルファイルサイズを取得
        model_dir = os.path.expanduser('~/.cache/whisper')
        file_size = 0
        if os.path.exists(model_dir):
            for file in os.listdir(model_dir):
                if model_name in file:
                    file_path = os.path.join(model_dir, file)
                    file_size = os.path.getsize(file_path) / 1024 / 1024
                    break
        
        # パラメータ数
        param_count = sum(p.numel() for p in model.parameters())
        
        results[model_name] = {
            'file_size': file_size,
            'load_time': load_time,
            'param_count': param_count
        }
        
        print(f"ファイルサイズ: {file_size:.1f} MB")
        print(f"ロード時間: {load_time:.2f} 秒")
        print(f"パラメータ数: {param_count:,}")
        
        # メモリを解放
        del model
    
    # 結果サマリー
    print("\n📊 切り替えコストサマリー")
    print("=" * 50)
    print("モデル  | ファイル  | ロード時間 | パラメータ数")
    print("-------|---------|-----------|-------------")
    for name, data in results.items():
        print(f"{name:7} | {data['file_size']:6.1f}MB | {data['load_time']:8.2f}s | {data['param_count']:11,}")

if __name__ == "__main__":
    test_model_switching() 