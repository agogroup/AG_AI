# 実行ファイルディレクトリ

このディレクトリには、システムの主要な実行ファイルが格納されています。

## ファイル一覧

- `analyze.py` - 基本的な分析システム
- `analyze_smart.py` - フィードバック学習機能付き分析
- `analyze_claude.py` - Claude Code統合版（API不要）
- `analyze_advanced.py` - 抽象化学習機能付き高度な分析

## 使用方法

ルートディレクトリから以下のコマンドで実行：

```bash
python analyze.py
python analyze_smart.py
python analyze_advanced.py
python analyze_claude.py
```

ルートディレクトリにある同名のファイルは、これらのスクリプトへのエントリーポイントです。