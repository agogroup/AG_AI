#!/bin/bash
# Notion同期の自動実行設定スクリプト

echo "🚀 Notion同期の自動実行設定"
echo "================================"

# プロジェクトディレクトリの確認
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_ENV="$PROJECT_DIR/venv/bin/python"
SYNC_SCRIPT="$PROJECT_DIR/notion_sync.py"

echo "📁 プロジェクトディレクトリ: $PROJECT_DIR"

# 仮想環境の確認
if [ ! -f "$PYTHON_ENV" ]; then
    echo "❌ 仮想環境が見つかりません: $PYTHON_ENV"
    exit 1
fi

# スクリプトの確認
if [ ! -f "$SYNC_SCRIPT" ]; then
    echo "❌ 同期スクリプトが見つかりません: $SYNC_SCRIPT"
    exit 1
fi

echo ""
echo "利用可能な同期頻度オプション:"
echo "1. 毎日 1回（朝9時）"
echo "2. 毎日 2回（朝9時・夕方18時）"
echo "3. 平日のみ（朝9時）"
echo "4. 毎時間（営業時間内：9-18時）"
echo "5. カスタム設定"
echo "6. 現在の設定を表示"
echo ""

read -p "選択してください (1-6): " choice

case $choice in
    1)
        # 毎日朝9時
        CRON_ENTRY="0 9 * * * cd $PROJECT_DIR && $PYTHON_ENV $SYNC_SCRIPT 1 >> logs/notion_sync.log 2>&1"
        echo "設定: 毎日朝9時に前日の議事録を同期"
        ;;
    2)
        # 毎日2回
        CRON_ENTRY1="0 9 * * * cd $PROJECT_DIR && $PYTHON_ENV $SYNC_SCRIPT 1 >> logs/notion_sync.log 2>&1"
        CRON_ENTRY2="0 18 * * * cd $PROJECT_DIR && $PYTHON_ENV $SYNC_SCRIPT 1 >> logs/notion_sync.log 2>&1"
        echo "設定: 毎日朝9時・夕方18時に前日の議事録を同期"
        ;;
    3)
        # 平日のみ
        CRON_ENTRY="0 9 * * 1-5 cd $PROJECT_DIR && $PYTHON_ENV $SYNC_SCRIPT 1 >> logs/notion_sync.log 2>&1"
        echo "設定: 平日（月-金）朝9時に前日の議事録を同期"
        ;;
    4)
        # 毎時間（営業時間内）
        CRON_ENTRY="0 9-18 * * * cd $PROJECT_DIR && $PYTHON_ENV $SYNC_SCRIPT 1 >> logs/notion_sync.log 2>&1"
        echo "設定: 営業時間内（9-18時）毎時間、前日の議事録を同期"
        ;;
    5)
        echo "カスタム設定（cron形式で入力）:"
        echo "例: '0 */4 * * *' = 4時間毎"
        echo "例: '0 9,13,17 * * 1-5' = 平日の9時,13時,17時"
        read -p "cron形式で入力: " custom_cron
        CRON_ENTRY="$custom_cron cd $PROJECT_DIR && $PYTHON_ENV $SYNC_SCRIPT 1 >> logs/notion_sync.log 2>&1"
        echo "設定: カスタム - $custom_cron"
        ;;
    6)
        echo "現在のcron設定:"
        crontab -l | grep notion_sync || echo "❌ Notion同期のcronジョブは設定されていません"
        exit 0
        ;;
    *)
        echo "❌ 無効な選択です"
        exit 1
        ;;
esac

echo ""
echo "🔧 crontabに設定を追加しますか? (y/n)"
read -p "実行: " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    # ログディレクトリを作成
    mkdir -p "$PROJECT_DIR/logs"
    
    # 現在のcrontabを取得
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    if [ -n "$CRON_ENTRY2" ]; then
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY2") | crontab -
    fi
    
    echo "✅ crontabに設定を追加しました"
    echo ""
    echo "📝 現在の設定:"
    crontab -l | grep notion_sync
    echo ""
    echo "💡 ログ確認: tail -f $PROJECT_DIR/logs/notion_sync.log"
    echo "🛑 設定削除: crontab -e"
else
    echo "❌ 設定をキャンセルしました"
fi 