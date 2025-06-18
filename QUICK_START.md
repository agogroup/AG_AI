# 🚀 AGO Group インテリジェント分析システム - クイックスタート

3分で始められる！

## 1️⃣ データを入れる
```bash
# 新規フォルダにファイルをコピー
cp ~/Downloads/*.txt data/00_new/
```

## 2️⃣ 分析を実行
```bash
python analyze.py
```

## 3️⃣ 結果を確認
分析結果は以下に保存されます：
- `output/intelligent_analysis/` - 分析結果
- `data/01_analyzed/日付/` - 処理済みファイル

## 📊 データ管理状況の確認
```bash
# 処理状況を確認
python scripts/data_manager.py status

# 未処理ファイル一覧
python scripts/data_manager.py list

# 6ヶ月以上前のファイルをアーカイブ
python scripts/data_manager.py archive
```

## 💡 ポイント
- 処理済みファイルは自動的に日付フォルダに整理
- 同じファイルを2回処理しようとすると警告
- `data/analysis_log.json`で処理履歴を確認可能

詳しい使い方は[USER_MANUAL.md](USER_MANUAL.md)を参照してください。