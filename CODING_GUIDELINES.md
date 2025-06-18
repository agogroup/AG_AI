# 🔧 AGO Group コーディングガイドライン

## 📅 日付・時刻の取り扱い

### ❌ してはいけないこと

```python
# 悪い例：ハードコーディングされた日付
record = {
    "date": "2025-06-13",
    "processed_at": "2025-06-13T14:00:00"
}

# 悪い例：手動でフォーマット
folder_name = "2025-06-13"
```

### ✅ 正しい方法

```python
# 良い例：date_utilsを使用
from scripts.date_utils import get_today, get_now

record = {
    "date": get_today(),            # 2025-06-13
    "processed_at": get_now()       # 2025-06-13T14:30:00.123456
}

# 良い例：動的に生成
folder_name = get_today()
```

## 🔍 コードレビューチェックリスト

### 日付関連
- [ ] ハードコーディングされた日付がないか？
- [ ] `datetime.now()` より `date_utils` を使っているか？
- [ ] 未来の日付や古すぎる日付がないか？

### ファイルパス関連
- [ ] 日付を含むパスは動的に生成されているか？
- [ ] 絶対パスではなく相対パスを使っているか？

### データ処理関連
- [ ] タイムスタンプは適切に記録されているか？
- [ ] ログに正しい日時が記録されているか？

## 🛠️ 開発時の確認方法

### 1. ハードコーディング検出スクリプト

```bash
# 日付のハードコーディングをチェック
python scripts/check_dates.py *.py
```

### 2. 環境日付の確認

```python
# スクリプトの冒頭で確認
from scripts.date_utils import get_today
print(f"実行日: {get_today()}")
```

### 3. テスト時の日付固定

```bash
# テスト用に日付を固定
export AGO_CURRENT_DATE="2025-06-13"
python test_script.py
```

## 📝 移行ガイド

既存のコードを更新する場合：

```python
# Before
"processed_date": datetime.now().isoformat()
folder = f"data/{datetime.now().strftime('%Y-%m-%d')}"

# After
from scripts.date_utils import get_now, get_today

"processed_date": get_now()
folder = f"data/{get_today()}"
```

## ⚠️ 注意事項

1. **マイグレーションスクリプト**
   - 一時的なスクリプトでも日付はハードコーディングしない
   - 必ず `date_utils` を使用する

2. **ドキュメント内の日付**
   - ドキュメントに具体的な日付を書く場合は要注意
   - 「最終更新日」などは自動生成を検討

3. **ログファイル**
   - ログのタイムスタンプは必ず動的に生成
   - ローテーション時も `date_utils` を使用

## 🔄 定期チェック

毎週月曜日に以下を確認：
1. 新しいコードに日付のハードコーディングがないか
2. `date_utils` が正しく使われているか
3. ログファイルの日付が正しいか