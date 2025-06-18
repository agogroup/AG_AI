# 📅 日付処理ガイド - 同じミスを防ぐために

## 🎯 なぜこのガイドが必要か

2025年6月13日、データ移行作業で「2025-01-13」という間違った日付を使用してしまいました。
このミスを防ぐため、システム的な対策を実装しました。

## 🛡️ 実装した対策

### 1. **date_utils.py** - 共通ユーティリティ
```python
from scripts.date_utils import get_today, get_now

# 常にこれを使う
current_date = get_today()      # "2025-06-13"
current_datetime = get_now()    # "2025-06-13T14:30:00.123456"
```

### 2. **check_dates.py** - 自動チェックツール
```bash
# プロジェクト全体をチェック
python scripts/check_dates.py '**/*.py'

# 特定のファイルをチェック
python scripts/check_dates.py scripts/new_feature.py
```

### 3. **Git pre-commitフック** - コミット時の自動検証
```bash
# フックを有効化
git config core.hooksPath .githooks
```

## 📝 開発者向けクイックリファレンス

### ❌ やってはいけないこと
```python
# ダメな例
folder = "2025-06-13"
record["date"] = "2025-06-13T14:00:00"
path = f"data/01_analyzed/2025-06-13/"
```

### ✅ 正しい方法
```python
from scripts.date_utils import get_today, get_now

# 良い例
folder = get_today()
record["date"] = get_now()
path = f"data/01_analyzed/{get_today()}/"
```

## 🔧 セットアップ

### 1. 必要なファイルの確認
- [ ] `scripts/date_utils.py` が存在する
- [ ] `scripts/check_dates.py` が存在する
- [ ] `.githooks/pre-commit` が存在する

### 2. Git フックの設定
```bash
# プロジェクトディレクトリで実行
git config core.hooksPath .githooks
```

### 3. 動作確認
```bash
# テスト実行
python scripts/check_dates.py scripts/*.py
```

## 🚨 エラーが出たら

### ImportError: date_utils
```python
# 以下のように条件付きインポートを使用
try:
    from .date_utils import get_today
except ImportError:
    from date_utils import get_today
```

### Git commitが失敗する
```bash
# 一時的にフックを無効化（緊急時のみ）
git commit --no-verify

# ただし、後で必ず修正すること！
```

## 📊 効果測定

定期的に以下を確認：
```bash
# 月次チェック
python scripts/check_dates.py '**/*.py' > date_check_report.txt
```

## 🎓 教訓

1. **ハードコーディングは避ける** - 特に日付は危険
2. **既存のツールを使う** - date_utils.pyを活用
3. **自動化で防ぐ** - 人の注意力に頼らない
4. **チームで共有** - 全員がこのガイドを読む

---

このガイドは、実際のミスから学んだ教訓をもとに作成されました。
同じミスを繰り返さないよう、チーム全員で守りましょう。