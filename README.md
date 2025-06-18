# AGO Group インテリジェント業務分析システム

## 🎯 概要
AGO Groupの業務データ（メール、LINE、文書など）をLLMで解析し、人物・ワークフロー・ビジネスインサイトを自動的に抽出するシステムです。データ変換不要で、生データをそのまま投入して分析できます。

## ✨ 特徴
- **データ変換不要**: LINE、メール、文書をそのまま投入
- **文脈を理解**: AIが内容を読んで関係性を把握
- **対話的改善**: 解析結果をその場で修正・改善
- **瞬時に分析**: 数秒で結果を表示
- **プライバシー保護**: ローカル実行で機密情報を保護

## 🚀 クイックスタート

### 1. 環境セットアップ
```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. データの準備

超簡単！`data/00_new/`フォルダにファイルを入れるだけ。

#### 対応データ形式
- **メール**: .pst, .msg, .mbox, .eml, .txt
- **文書**: .docx, .doc, .pdf, .txt, .md, .xlsx, .xls, .pptx, .ppt  
- **チャット**: LINE (.txt), Slack (.json), Teams/Zoom (.csv)

#### 使い方
```bash
# どんなファイルでもdata/00_new/に入れるだけ
cp ~/Downloads/[LINE]営業チーム.txt data/00_new/
cp ~/Documents/メール履歴.mbox data/00_new/
cp ~/Desktop/会議メモ.pdf data/00_new/

# 複数ファイルを一括投入もOK
cp ~/Desktop/分析したいファイル/* data/00_new/
```

**ポイント**: フォルダ分けは不要！AIが自動的にファイルの種類を判別します。

### 3. 実行

#### 基本的な分析
```bash
python analyze.py
```

#### スマート分析（学習機能付き）
```bash
# 過去のフィードバックを記憶して精度向上
python analyze_smart.py
```

#### Claude Code統合版（API不要）
```bash
# この会話内でClaude Codeが直接分析
python analyze_claude.py
```

#### フィードバック学習のデモ
```bash
# 学習機能の動作確認
python analyze_smart.py --demo
```

#### 高度な分析（抽象化学習付き）
```bash
# パターン認識と予防的警告機能付き
python analyze_advanced.py

# 抽象化学習のデモ
python analyze_advanced.py --demo
```

### 4. 結果の確認・修正
分析結果が表示されたら、間違いがあれば対話的に修正できます：
```
=== 解析結果 ===
【識別された人物】
- 山田太郎（営業部長）← これ違う？教えてください
- 田中花子（経理）

> 山田太郎は開発部のエンジニアです
```

### 5. 使用例

#### 例1: LINEトーク履歴の分析
1. LINEからトーク履歴をエクスポート（.txt形式）
2. `data/00_new/`に配置
3. `python analyze.py`を実行
4. 画面の指示に従って分析（処理後は自動的に`data/01_analyzed/日付/`に移動）

#### 例2: 複数ファイルの一括分析
1. 全てのファイルを`data/00_new/`にそのまま配置
2. `python analyze.py`を実行
3. "all"を選択して全ファイル分析
4. AIが文脈を理解して関係性を抽出
5. 処理済みファイルは自動的に日付フォルダに整理される

## 📊 出力される情報
- **人物相関図**: 誰が誰と仕事しているか
- **業務フロー**: どんな手順で仕事が進んでいるか
- **重要な発見**: AIが見つけた興味深いパターン
- **プロジェクト概要**: 何が行われているか

結果は`output/intelligent_analysis/`フォルダにJSON形式で保存されます。

## 📂 プロジェクト構造
```
AG_AI/
├── analyze.py              # メインエントリーポイント
├── scripts/
│   ├── __init__.py
│   ├── llm_analyzer.py    # LLM解析エンジン
│   ├── data_manager.py    # データライフサイクル管理
│   ├── feedback_manager.py # フィードバック学習
│   └── abstract_learner.py # 抽象化学習
├── data/
│   ├── 00_new/            # 🆕 新規データ投入（ここに入れる）
│   ├── 01_analyzed/       # ✅ 分析済みデータ（日付別）
│   ├── 02_archive/        # 📦 アーカイブ（6ヶ月以上前）
│   └── analysis_log.json  # 📝 処理履歴
├── output/
│   └── intelligent_analysis/  # 解析結果
├── logs/                  # 実行ログ
└── requirements.txt       # 依存関係
```

## 💡 従来システムとの違い
| 従来 | 新システム |
|------|-----------|
| CSV作成が必要 | そのまま投入 |
| 形式が固定 | 何でも理解 |
| 文脈を無視 | 文脈を理解 |
| 修正が大変 | 対話で改善 |

## 📚 詳細ドキュメント
- [ユーザーマニュアル](USER_MANUAL.md) - 詳細な使い方ガイド
- [システム設計書](docs/SYSTEM_DESIGN.md) - 技術的な設計詳細
- [日付処理ガイド](DATE_HANDLING_GUIDE.md) - 🆕 日付の正しい扱い方
- [コーディングガイドライン](CODING_GUIDELINES.md) - 開発規約

## 🛠️ 技術スタック
- Python 3.8+
- LLM API（OpenAI/Claude）対応準備
- JSON（データ保存）
- 将来的な拡張：
  - OpenAI API
  - Claude API
  - ローカルLLM

## ⚠️ 注意事項
- 現在はプロトタイプ版のため、LLM解析はシミュレーションです
- 実際のLLM APIを使用する場合は、APIキーの設定が必要です
- 機密情報を含むデータは、ローカル環境でのみ処理してください

## ❓ トラブルシューティング

### "ModuleNotFoundError"が出る場合
```bash
# 仮想環境が有効化されているか確認
which python  # Mac/Linux
where python  # Windows

# 再度パッケージをインストール
pip install -r requirements.txt
```

### ファイルが見つからない場合
- `data/00_new/`フォルダの存在を確認
- ファイルの拡張子が対応形式か確認
- 既に処理済みの場合は`data/01_analyzed/`を確認

### 文字化けする場合
- ファイルのエンコーディングがUTF-8であることを確認
- Windowsの場合は、メモ帳で開いて「UTF-8」で保存し直す

## 📞 サポート
問題が発生した場合：
1. エラーログを確認: `logs/`フォルダ
2. [トラブルシューティング](USER_MANUAL.md#トラブルシューティング)を参照
3. GitHubのIssueで報告

## ライセンス
Proprietary - AGO Group Internal Use Only