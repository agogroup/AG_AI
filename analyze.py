#!/usr/bin/env python3
"""
AGOグループ インテリジェント業務分析システム - エントリーポイント
"""
import os
import sys

# プロジェクトのルートディレクトリをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
from pathlib import Path

# Notion連携の確認
try:
    from scripts.notion_connector import NotionConnector
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False

from bin.analyze import main as analyze_main


def main():
    """メイン処理 - コマンドライン引数を処理してNotionとの統合を管理"""
    
    # コマンドライン引数のパーサーを作成
    parser = argparse.ArgumentParser(
        description='AGOグループ インテリジェント業務分析システム',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    # Notion同期オプション
    parser.add_argument(
        '--notion-sync',
        action='store_true',
        help='Notionから最新の議事録を同期してから分析'
    )
    
    parser.add_argument(
        '--notion-days',
        type=int,
        default=7,
        help='Notion同期時に取得する日数（デフォルト: 7日）'
    )
    
    parser.add_argument(
        '--notion-only',
        action='store_true',
        help='Notion同期のみ実行（分析は行わない）'
    )
    
    # 引数を解析
    args = parser.parse_args()
    
    # Notion同期の実行
    if args.notion_sync or args.notion_only:
        if not NOTION_AVAILABLE:
            print("❌ Notion連携にはnotion-clientのインストールが必要です")
            print("   実行: pip install notion-client")
            return 1
        
        print("🔄 Notionから議事録を同期中...")
        print("=" * 50)
        
        try:
            # 環境変数チェック
            if not os.environ.get('NOTION_INTEGRATION_TOKEN'):
                print("❌ 環境変数 NOTION_INTEGRATION_TOKEN が設定されていません")
                print("\n設定方法:")
                print("  export NOTION_INTEGRATION_TOKEN='secret_...'")
                print("\n詳細は https://developers.notion.com/docs/getting-started を参照")
                return 1
                
            if not os.environ.get('NOTION_DATABASE_ID'):
                print("❌ 環境変数 NOTION_DATABASE_ID が設定されていません")
                print("\n設定方法:")
                print("  export NOTION_DATABASE_ID='...'")
                print("\nデータベースIDはNotionページのURLから取得できます")
                return 1
            
            # Notion同期実行
            connector = NotionConnector()
            db_id = os.environ.get('NOTION_DATABASE_ID')
            saved_files = connector.sync_recent_minutes(db_id, days=args.notion_days)
            
            if saved_files:
                print(f"\n✅ {len(saved_files)}件の議事録を同期しました")
                print("\n📁 保存先: data/00_new/")
                print("\n保存されたファイル:")
                for f in saved_files:
                    print(f"   - {f.name}")
            else:
                print("\n⚠️ 同期する議事録がありませんでした")
                print(f"   （過去{args.notion_days}日間のデータを検索）")
        
        except Exception as e:
            print(f"\n❌ Notion同期エラー: {e}")
            return 1
        
        print("\n" + "=" * 50)
        
        # --notion-onlyの場合は分析をスキップ
        if args.notion_only:
            print("\n✅ Notion同期が完了しました")
            return 0
    
    # 通常の分析処理を実行
    print("\n🚀 分析処理を開始します...\n")
    analyze_main()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())