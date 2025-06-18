# 📊 AGOグループ データワークフロー管理

## 推奨データ管理構造

```
data/
├── 00_new/          # 🆕 新規データ投入（ここに入れる）
├── 01_analyzed/     # ✅ 分析済みデータ
│   ├── 2025-01-13/  # 処理日ごとに整理
│   └── 2025-01-14/
├── 02_archive/      # 📦 アーカイブ（6ヶ月以上前）
└── analysis_log.json # 📝 処理履歴
```

## 🔄 ワークフロー

### 1. データ投入
```bash
# 新しいデータは必ず 00_new へ
cp ~/Downloads/新しいLINE.txt data/00_new/
```

### 2. 分析実行
```bash
python analyze.py
# システムが自動的に 00_new 内のファイルを処理
```

### 3. 自動整理
分析完了後、システムが自動的に：
- 処理済みファイルを日付フォルダへ移動
- analysis_log.json に記録

### 4. 定期アーカイブ
```bash
# 6ヶ月以上前のデータを自動アーカイブ
python archive_old_data.py
```

## 📝 処理履歴の管理

### analysis_log.json の構造
```json
{
  "processed_files": [
    {
      "filename": "[LINE]営業チーム.txt",
      "original_path": "data/00_new/[LINE]営業チーム.txt",
      "processed_date": "2025-01-13 14:30:00",
      "moved_to": "data/01_analyzed/2025-01-13/",
      "analysis_results": "output/intelligent_analysis/営業チーム_analysis.json",
      "file_hash": "a1b2c3d4e5f6",
      "status": "completed"
    }
  ]
}
```

## 🚨 重複チェック機能

### ファイルハッシュによる重複防止
```python
def check_duplicate(file_path):
    """既に処理済みかチェック"""
    file_hash = calculate_hash(file_path)
    
    with open('data/analysis_log.json', 'r') as f:
        log = json.load(f)
    
    for record in log['processed_files']:
        if record['file_hash'] == file_hash:
            return True, record['processed_date']
    
    return False, None
```

## 💡 メリット

1. **明確な状態管理**
   - 新規: 00_new にあるもの
   - 処理済み: 01_analyzed にあるもの
   - 古い: 02_archive にあるもの

2. **処理履歴の追跡**
   - いつ処理したか
   - どの分析結果か
   - 重複処理の防止

3. **容量管理**
   - 古いデータの自動アーカイブ
   - 必要に応じて削除可能

## 🛠️ 実装スクリプト

### data_manager.py
```python
#!/usr/bin/env python3
"""データ管理ヘルパー"""

import os
import shutil
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class DataManager:
    def __init__(self):
        self.new_dir = Path("data/00_new")
        self.analyzed_dir = Path("data/01_analyzed")
        self.archive_dir = Path("data/02_archive")
        self.log_file = Path("data/analysis_log.json")
        
        # ディレクトリ作成
        for dir in [self.new_dir, self.analyzed_dir, self.archive_dir]:
            dir.mkdir(parents=True, exist_ok=True)
            
        # ログファイル初期化
        if not self.log_file.exists():
            self.log_file.write_text('{"processed_files": []}')
    
    def get_new_files(self):
        """未処理ファイルのリストを取得"""
        return list(self.new_dir.glob("*"))
    
    def move_to_analyzed(self, file_path, analysis_result_path):
        """処理済みファイルを移動"""
        today = datetime.now().strftime("%Y-%m-%d")
        dest_dir = self.analyzed_dir / today
        dest_dir.mkdir(exist_ok=True)
        
        # ファイル移動
        dest_path = dest_dir / file_path.name
        shutil.move(str(file_path), str(dest_path))
        
        # ログ更新
        self._update_log(file_path, dest_path, analysis_result_path)
        
    def archive_old_files(self, days=180):
        """古いファイルをアーカイブ"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for date_dir in self.analyzed_dir.iterdir():
            if date_dir.is_dir():
                dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                if dir_date < cutoff_date:
                    shutil.move(str(date_dir), str(self.archive_dir))
                    print(f"Archived: {date_dir.name}")
```

## 🎯 運用ルール

1. **新規データは必ず `00_new` へ**
2. **分析後は自動で `01_analyzed/日付/` へ**
3. **6ヶ月後に自動で `02_archive` へ**
4. **1年後にアーカイブから削除検討**

これで、どのデータが処理済みか一目瞭然になります！