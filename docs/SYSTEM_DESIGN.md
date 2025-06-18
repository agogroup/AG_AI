# AGOグループインテリジェント業務分析システム設計書

## 1. システム概要

### 1.1 目的
AGOグループの業務データをLLM（大規模言語モデル）で分析し、「誰が」「どのような業務を」行っているかを自動的に理解・可視化するインテリジェントシステムの構築

### 1.2 スコープ
- 生データのLLMによる自動分析（データ変換不要）
- 文脈を理解した人物・業務フローの抽出
- 対話的な結果修正・改善機能
- JSON形式での結果出力
- フィードバック学習による精度向上
- 抽象化学習によるパターン認識と予防

## 2. システムアーキテクチャ

### 2.1 全体構成
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  生データ        │ ──> │ LLM分析        │ ──> │ インテリジェント  │
│ (Raw Data)      │     │ エンジン         │     │ 分析結果       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │                        │
         │                  対話的修正                   │
         └───────────────────────────────────────────┘
```

### 2.2 ディレクトリ構造
```
AG_AI/
├── analyze.py            # メインエントリーポイント
├── bin/                  # 実行ファイル
│   ├── analyze.py
│   ├── analyze_smart.py
│   ├── analyze_claude.py
│   └── analyze_advanced.py
├── scripts/              # モジュール
│   ├── __init__.py
│   ├── llm_analyzer.py   # LLM解析エンジン
│   ├── feedback_manager.py
│   ├── abstract_learner.py
│   ├── data_manager.py   # データライフサイクル管理
│   └── claude_integration.py
├── data/
│   ├── 00_new/           # 🆕 新規データ投入
│   ├── 01_analyzed/      # ✅ 分析済み（日付別）
│   ├── 02_archive/       # 📦 アーカイブ
│   ├── feedback/         # 学習データ
│   └── analysis_log.json # 📝 処理履歴
├── output/
│   └── intelligent_analysis/  # LLM分析結果（JSON）
├── logs/                 # 実行ログ
└── requirements.txt      # 依存関係
```

## 3. データモデル

### 3.1 LLM分析結果の構造

```json
{
  "summary": "分析対象データの概要",
  "entities": {
    "persons": [
      {
        "name": "人物名",
        "role": "役割/職位",
        "organization": "所属組織",
        "activities": ["活動内容"],
        "relationships": ["関係者"]
      }
    ],
    "workflows": [
      {
        "name": "ワークフロー名",
        "steps": ["ステップ"],
        "participants": ["参加者"]
      }
    ]
  },
  "insights": [
    {
      "type": "発見の種類",
      "description": "説明",
      "importance": "high/medium/low"
    }
  ],
  "confidence_score": 0.85
}
```

## 4. LLM分析機能

### 4.1 データ理解
- **文脈認識**: テキストの文脈から人物や役割を理解
- **関係性抽出**: 会話ややり取りから人物間の関係を把握
- **業務パターン認識**: 繰り返される業務の流れを検出
- **重要情報抽出**: ビジネス上重要な情報を自動識別

### 4.2 対話的改善
- **結果の確認**: 分析結果をユーザーに提示
- **誤りの修正**: ユーザーからのフィードバックを受け付け
- **情報の追加**: 不足情報をユーザーから取得
- **再分析**: 修正内容を反映した再分析

### 4.3 出力生成
- **構造化データ**: JSON形式での結果出力
- **可視化データ**: 関係性マップやフロー図の生成
- **インサイト**: AIが発見した重要なパターンや改善点

## 5. 実装アプローチ

### 5.1 現在の実装（プロトタイプ）
```python
# LLMシミュレーター
class LLMAnalyzer:
    def analyze_file(self, file_path: str) -> Dict[str, Any]
    def extract_entities(self, text: str) -> Dict[str, List]
    def identify_workflows(self, text: str) -> List[Dict]
    def generate_insights(self, analysis: Dict) -> List[Dict]
```

### 5.2 将来の拡張（API連携）
```python
# 実際のLLM API連携
class RealLLMAnalyzer:
    def __init__(self, api_key: str, model: str)
    def analyze_with_openai(self, text: str) -> Dict
    def analyze_with_claude(self, text: str) -> Dict
    def analyze_with_local_llm(self, text: str) -> Dict
```

### 5.3 対話的改善機能
```python
# インタラクティブセッション
class InteractiveSession:
    def display_results(self, analysis: Dict) -> None
    def collect_feedback(self) -> str
    def update_analysis(self, analysis: Dict, feedback: str) -> Dict
    def save_final_results(self, analysis: Dict) -> None
```

## 6. 出力形式

### 6.1 JSON出力
分析結果はJSON形式で`output/intelligent_analysis/`に保存：

```json
{
  "file_path": "data/00_new/LINE_営業チーム.txt",
  "analysis_date": "2024-01-15T10:30:00",
  "summary": "営業チームのLINEグループでの業務連絡",
  "entities": {
    "persons": [
      {
        "name": "山田太郎",
        "role": "営業部エンジニア",
        "activities": ["顧客対応", "提案書作成"],
        "relationships": ["田中花子", "鈴木一郎"]
      }
    ],
    "workflows": [
      {
        "name": "提案プロセス",
        "steps": ["顧客ヒアリング", "提案書作成", "レビュー", "提出"],
        "participants": ["山田太郎", "田中花子"]
      }
    ]
  },
  "insights": [
    {
      "type": "collaboration",
      "description": "山田さんと田中さんの連携が頻繁",
      "importance": "high"
    }
  ],
  "confidence_score": 0.85
}
```

### 6.2 将来の拡張
- Obsidian形式での出力
- グラフ可視化
- ダッシュボード生成

## 7. 技術スタック

### 7.1 開発環境
- **言語**: Python 3.8+
- **LLM**: プロトタイプ（シミュレーター）
- **将来的なAPI**: OpenAI, Claude, ローカルLLM

### 7.2 主要ライブラリ
```python
# requirements.txt
json                   # JSON処理
# 将来的な追加:
# openai               # OpenAI API
# anthropic            # Claude API
# transformers         # ローカルLLM
```

## 8. 学習機能

### 8.1 フィードバック学習
- **目的**: 個別の修正を記憶し、同じ間違いを防ぐ
- **実装**: `scripts/feedback_manager.py`
- **データ保存**: `data/feedback/knowledge_base.json`
- **機能**:
  - 人物情報の修正記録
  - ワークフローの修正記録
  - 次回分析時の自動適用

### 8.2 抽象化学習
- **目的**: パターンを抽出し、類似の間違いを予防
- **実装**: `scripts/abstract_learner.py`
- **データ保存**: `data/feedback/abstract_knowledge.json`
- **機能**:
  - 名前パターンの認識（省略形→フルネーム）
  - 役職パターンの認識（過小評価→実際の役職）
  - 組織パターンの認識（所属の誤認識）
  - 予防的警告の生成

### 8.3 学習プロセス
```
具体的な修正
    ↓
パターン抽出（抽象化）
    ↓
ルール生成
    ↓
新規分析への適用
    ↓
予防的警告
```

## 9. データ管理システム

### 9.1 データライフサイクル
- **新規データ**: `data/00_new/` に投入
- **分析実行**: 自動的に処理
- **処理済み**: `data/01_analyzed/日付/` に自動移動
- **アーカイブ**: 6ヶ月後に `data/02_archive/` へ

### 9.2 重複チェック
- ファイルハッシュによる重複検出
- 処理履歴の追跡（`analysis_log.json`）
- 警告表示とスキップ機能

### 9.3 データ管理コマンド
```bash
# 状況確認
python scripts/data_manager.py status

# 未処理ファイル一覧
python scripts/data_manager.py list

# アーカイブ実行
python scripts/data_manager.py archive

# 重複チェック
python scripts/data_manager.py cleanup
```

## 10. 今後の拡張

### 10.1 実際のLLM API連携
- OpenAI GPT-4の統合
- Anthropic Claudeの統合
- ローカルLLMのサポート

### 10.2 高度な分析機能
- 感情分析
- トレンド分析
- 異常検知

### 10.3 出力形式の拡充
- Obsidian形式での出力
- グラフ可視化（D3.js、Mermaid）
- Excel/PDFレポート

## 11. セキュリティ考慮事項
- 個人情報のマスキング機能
- アクセス権限の管理
- センシティブ情報の暗号化

## 12. まとめ

このLLMベースのインテリジェント業務分析システムにより：
- データ変換不要で生データを直接分析
- AIが文脈を理解して人物や業務を抽出
- 対話的に結果を修正・改善
- フィードバック学習で同じ間違いを防止
- 抽象化学習で類似の間違いも予防
- 将来的には実際のLLM APIと連携してより高度な分析が可能