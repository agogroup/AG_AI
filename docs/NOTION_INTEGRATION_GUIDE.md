# NotionとAGAIシステムの統合ガイド

## 概要

AGOグループの議事録をNotionで管理している場合、AGAIシステムと統合することで、自動的に議事録を取得・分析できます。

## 主な機能

- ✅ **自動同期**: Notionデータベースから最新の議事録を自動取得
- ✅ **日本語対応**: 日本語の議事録を正確に処理
- ✅ **重複防止**: 既に処理済みの議事録はスキップ
- ✅ **メタデータ保持**: 作成日時、URL等の情報を保持

## セットアップ手順

### 1. 必要なパッケージのインストール

```bash
pip install notion-client
```

### 2. Notion内部統合の作成

1. [Notion開発者ページ](https://www.notion.so/my-integrations)にアクセス
2. 「新しいインテグレーション」をクリック
3. 名前を入力（例：「AGAI議事録連携」）
4. ワークスペースを選択
5. 「送信」をクリック

### 3. 統合トークンの取得

作成した統合の「内部インテグレーショントークン」をコピーします。

```
secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 4. データベースへの接続を追加

Notionで議事録を管理しているデータベースを開き：

1. 右上の「...」をクリック
2. 「接続を追加」を選択
3. 作成した統合を選択
4. 「確認」をクリック

### 5. データベースIDの取得

データベースのURLから取得します：

```
https://www.notion.so/workspace/[データベースID]?v=xxxxx
                                  ^^^^^^^^^^^^^^^^
                                  この部分がデータベースID
```

### 6. 環境変数の設定

以下の環境変数を設定します：

```bash
# Notion統合トークン
export NOTION_INTEGRATION_TOKEN='secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# データベースID
export NOTION_DATABASE_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
```

`.bashrc`や`.zshrc`に追加して永続化することを推奨します。

## 使用方法

### 基本的な使い方

最新7日間の議事録を同期して分析：

```bash
python analyze.py --notion-sync
```

### オプション

#### 同期期間の指定

過去30日間の議事録を同期：

```bash
python analyze.py --notion-sync --notion-days 30
```

#### 同期のみ実行（分析なし）

```bash
python analyze.py --notion-only
```

### 実行例

```bash
$ python analyze.py --notion-sync

🔄 Notionから議事録を同期中...
==================================================
📄 3件の議事録を取得しました

✅ 3件の議事録を同期しました

📁 保存先: data/00_new/

保存されたファイル:
   - notion_20250118_AGOグループ定例会議.txt
   - notion_20250115_新規プロジェクトキックオフ.txt
   - notion_20250112_月次レビュー会議.txt

==================================================

🚀 分析処理を開始します...

🔍 AGO Group インテリジェント業務分析システム
==================================================
```

## ファイル形式

同期された議事録は以下の形式で保存されます：

```
=== Notion議事録 ===
タイトル: AGOグループ定例会議
作成日時: 2025-01-18T10:00:00.000Z
ページID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
URL: https://www.notion.so/AGOグループ定例会議-xxxxxxxxxxxx

=== 内容 ===
[議事録の本文]
```

## トラブルシューティング

### エラー: "notion_client.errors.APIResponseError"

**原因**: 統合がデータベースに接続されていない

**解決方法**: 
1. Notionデータベースの「接続を追加」から統合を追加
2. データベースIDが正しいか確認

### エラー: "環境変数が設定されていません"

**原因**: 必要な環境変数が未設定

**解決方法**:
```bash
# 環境変数を確認
echo $NOTION_INTEGRATION_TOKEN
echo $NOTION_DATABASE_ID

# 設定されていない場合は設定
export NOTION_INTEGRATION_TOKEN='secret_xxx'
export NOTION_DATABASE_ID='xxx'
```

### 文字数制限エラー

**原因**: 議事録が15,000文字を超えている

**解決方法**: 
- 長い議事録は自動的に分割されます
- 必要に応じて手動で分割してください

## 注意事項

- **レート制限**: 3リクエスト/秒の制限があります
- **文字数制限**: 1ページあたり15,000文字まで
- **子ページ**: 子ページは別途取得が必要です
- **プライバシー**: 統合トークンは機密情報として扱ってください

## 高度な使用法

### Pythonスクリプトから直接使用

```python
from scripts.notion_connector import NotionConnector

# コネクターを初期化
connector = NotionConnector()

# 特定のページを取得
page_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
filepath = connector.save_meeting_minutes(page_id, title="重要会議")

# カスタムフィルターで取得
filter_params = {
    "property": "タグ",
    "multi_select": {
        "contains": "重要"
    }
}
pages = connector.get_database_pages(database_id, filter_params)
```

## 関連ドキュメント

- [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md) - システム全体の設計
- [DATA_WORKFLOW.md](../DATA_WORKFLOW.md) - データ処理フロー
- [Notion API公式ドキュメント](https://developers.notion.com/) 