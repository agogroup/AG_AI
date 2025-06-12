# Claude Code 自動モードの使用方法

## セットアップ完了後の使い方

### 方法1: エイリアスを使用
```bash
claude-auto  # 自動モードで起動
```

### 方法2: VS Code/Cursorから
- Ctrl+Shift+P → "Tasks: Run Task" → "Claude Code 自動モード"

### 方法3: 通常起動後に初期化
```bash
claude
# 起動後に以下を入力
cat CLAUDE_CODE_INSTRUCTIONS.md && cat .claude/init.md
```

## 設定の確認・変更
- 自動実行ルール: CLAUDE_CODE_INSTRUCTIONS.md
- プロジェクト設定: .claude/project.yaml
- エディタ連携: .vscode/tasks.json, .cursor/settings.json