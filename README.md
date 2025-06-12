# AGOグループ業務プロファイリングシステム

収集済み業務データから「誰が」「どのような業務を」行っているかを可視化するプロファイリングシステム

## 機能

- 人物プロファイリング（業務頻度、協働ネットワーク、専門領域）
- 業務フロー抽出（パターン認識、依存関係分析）
- 部門間連携分析
- Obsidian用Markdownファイル生成

## セットアップ

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# 日本語モデルのダウンロード
python -m spacy download ja_core_news_sm
```

## 使用方法

```bash
# メインスクリプトの実行
python main.py

# 特定の処理のみ実行
python scripts/extractors/person_extractor.py
python scripts/analyzers/workflow_analyzer.py
```

## ディレクトリ構造

```
├── data/                   # データディレクトリ
│   ├── raw/               # 生データ
│   └── processed/         # 処理済みデータ
├── scripts/               # 処理スクリプト
│   ├── extractors/        # データ抽出
│   ├── analyzers/         # 分析処理
│   └── generators/        # 出力生成
├── output/                # 出力ディレクトリ
├── config/                # 設定ファイル
└── tests/                 # テストコード
```