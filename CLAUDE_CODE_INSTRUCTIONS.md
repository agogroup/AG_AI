# CLAUDE CODE 自動実行指示書

## 基本方針
以下の操作は確認なしで自動実行してください。

## 自動実行を許可する操作

### ファイル操作
- すべてのファイルの読み取り
- src/, tests/, scripts/配下のファイル変更
- *.ts, *.tsx, *.js, *.jsx, *.py, *.md ファイルの作成・変更

### Git操作（自動実行）
- git status, diff, log, branch
- git add, commit
- git stash, stash pop

### 開発コマンド（自動実行）
- npm test, npm run build, npm run dev
- yarn test, yarn build, yarn dev
- pytest, jest, vitest
- tsc, eslint, prettier

### 確認が必要な操作
- git push, merge, rebase
- npm install (新規パッケージ)
- rm -rf, sudo コマンド
- .env, secrets関連のファイル

## 作業方針
- エラー時は自動的に3回までリトライ
- 説明は最小限、実行を優先
- 並列実行可能なタスクは並列化