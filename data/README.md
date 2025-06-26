# AGO Profiling System - ディレクトリ構造ガイド

## 概要
このドキュメントは、AGO Profiling Systemの新しいディレクトリ構造と移行スケジュールについて説明します。

## ディレクトリ構造

### 新構造（Phase 2以降）
```
data/
├── raw/                    # 生データ格納
│   └── documents/         
│       └── current/       # 最新の未処理ドキュメント
│
├── processed/             # 処理済みデータ
│   ├── analyzed/         # 分析済みファイル（日付別）
│   │   └── YYYY-MM-DD/   
│   └── markdown/         # Markdown形式のファイル
│
└── feedback/             # フィードバックデータ
    └── knowledge_base.json
```

### 旧構造（並行運用中）
```
data/
├── 00_new/              # 新規ファイル（現在も使用中）
├── 01_analyzed/         # 分析済みファイル（現在も使用中）
└── 03_extraction/       # 抽出データ
```

## ファイル命名規則

### 新構造での命名規則
- **生データ**: `source_YYYYMMDD_description.ext`
  - 例: `notion_20250626_公式LINE改善会議.txt`
  
- **分析済み**: `YYYYMMDD_HH_description_analyzed.json`
  - 例: `20250626_14_公式LINE改善会議_analyzed.json`

- **Markdown**: `title_YYYYMMDD.md`
  - 例: `公式LINE改善会議_20250626.md`

## 移行スケジュール

### Phase 2（2025年6月26日〜）- 並行運用
- 新旧両方のディレクトリ構造を維持
- 自動同期スクリプトが1時間ごとに実行
- `00_new/`の新規ファイルは`raw/documents/current/`へコピー
- `01_analyzed/`の新規ファイルは`processed/analyzed/YYYY-MM-DD/`へコピー

### Phase 3（予定）- 完全移行
- 新構造への完全移行
- 旧ディレクトリの廃止
- すべてのツールとスクリプトの更新

## 自動化ツール

### sync_to_new_structure.py
- 旧構造から新構造への自動同期
- 実行間隔: 1時間ごと
- ログ: `/logs/sync_log.txt`

### monitor_migration.py
- 移行進捗の監視
- 日次レポート生成
- 出力: `/reports/migration_report_YYYY-MM-DD.json`

## 注意事項

1. **業務継続性**
   - 移行期間中も既存の業務フローは変更なし
   - `00_new/`と`01_analyzed/`への操作は従来通り

2. **データ整合性**
   - 同期は「コピー」のみ（移動はしない）
   - 重複ファイルは自動的にスキップ

3. **エラー対応**
   - エラーはすべてログに記録
   - 重大なエラーの場合は即座に停止

## サポート
移行に関する質問や問題は、システム管理者にお問い合わせください。