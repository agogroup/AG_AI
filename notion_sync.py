#!/usr/bin/env python3
"""
AGOグループ Notion議事録同期ツール（シンプル版）
- 複雑な自動分析なし
- Claudeとの対話ベース分析用にデータ準備のみ
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# プロジェクトルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from scripts.notion_connector import NotionConnector
    NOTION_AVAILABLE = True
except ImportError:
    print("❌ notion-clientがインストールされていません")
    print("実行: pip install notion-client")
    sys.exit(1)


def main():
    """メイン処理 - NotionからAGOグループの議事録を同期"""
    
    print("=" * 60)
    print("🚀 AGOグループ Notion議事録同期ツール")
    print("=" * 60)
    
    # 環境変数チェック
    token = os.environ.get('NOTION_INTEGRATION_TOKEN')
    db_id = os.environ.get('NOTION_DATABASE_ID')
    
    if not token:
        print("❌ 環境変数 NOTION_INTEGRATION_TOKEN が設定されていません")
        print("\n設定方法:")
        print("  export NOTION_INTEGRATION_TOKEN='ntn_...'")
        return 1
        
    if not db_id:
        print("❌ 環境変数 NOTION_DATABASE_ID が設定されていません")  
        print("\n設定方法:")
        print("  export NOTION_DATABASE_ID='...'")
        return 1
    
    # 同期日数の設定（デフォルト：7日）
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("❌ 引数は数値で指定してください")
            print("使用例: python notion_sync.py 7")
            return 1
    else:
        days = 7
    
    print(f"📅 過去{days}日間の議事録を同期します...")
    print()
    
    try:
        # Notion接続
        connector = NotionConnector()
        
        # 最近の議事録を取得・保存
        saved_files = connector.sync_recent_minutes(db_id, days=days)
        
        if saved_files:
            print(f"✅ {len(saved_files)}件の議事録を同期しました")
            print(f"📁 保存先: {Path('data/00_new').absolute()}")
            print()
            print("💾 同期されたファイル:")
            for i, file_path in enumerate(saved_files, 1):
                print(f"  {i:2d}. {file_path.name}")
                
            print()
            print("💡 次のステップ:")
            print("  - Claudeとの対話で議事録の内容について質問・分析")
            print("  - 必要に応じて業務改善提案を受ける")
            
        else:
            print("⚠️ 同期する議事録がありませんでした")
            print(f"   （過去{days}日間のデータを検索）")
            
        print()
        print("=" * 60)
        print("🎯 Claude対話準備完了！")
        print("   議事録について何でもお聞きください。")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"❌ 同期エラー: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 