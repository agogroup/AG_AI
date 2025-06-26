#!/usr/bin/env python3
"""
Notion データ移行スクリプト
既存の00_newディレクトリ内のNotionデータを新しい専用ディレクトリに移行
"""

import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def migrate_notion_data():
    """既存のNotionデータを新しいディレクトリ構造に移行"""
    
    # ディレクトリパス
    old_dir = Path("data/00_new")
    new_notion_dir = Path("data/sources/notion")
    analysis_log = Path("data/analysis_log.json")
    
    # 新しいディレクトリを作成
    new_notion_dir.mkdir(parents=True, exist_ok=True)
    
    # 移行対象ファイルを特定（notion_で始まるファイル）
    notion_files = list(old_dir.glob("notion_*.txt"))
    
    if not notion_files:
        print("❌ 移行対象のNotionファイルが見つかりません")
        return
    
    print(f"📁 {len(notion_files)}個のNotionファイルを移行します...")
    
    # 移行実行
    migrated_files = []
    for file_path in notion_files:
        try:
            # 新しい場所にコピー
            new_path = new_notion_dir / file_path.name
            shutil.copy2(file_path, new_path)
            
            # 元ファイルを削除
            file_path.unlink()
            
            migrated_files.append({
                "old_path": str(file_path),
                "new_path": str(new_path),
                "migrated_at": datetime.now().isoformat()
            })
            
            print(f"✅ 移行完了: {file_path.name}")
            
        except Exception as e:
            print(f"❌ 移行エラー: {file_path.name} - {e}")
    
    # 移行ログを更新
    if analysis_log.exists():
        with open(analysis_log, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # 移行記録を追加
        if 'notion_migration' not in log_data:
            log_data['notion_migration'] = []
        
        log_data['notion_migration'].extend(migrated_files)
        log_data['last_migration'] = datetime.now().isoformat()
        
        with open(analysis_log, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 移行完了: {len(migrated_files)}個のファイルを移行しました")
    print(f"📂 新しい保存先: {new_notion_dir}")
    print(f"📊 詳細ログ: {analysis_log}")

def verify_migration():
    """移行結果を確認"""
    old_dir = Path("data/00_new")
    new_dir = Path("data/sources/notion")
    
    old_notion_files = list(old_dir.glob("notion_*.txt"))
    new_notion_files = list(new_dir.glob("notion_*.txt"))
    
    print(f"📊 移行前の00_new内Notionファイル数: {len(old_notion_files)}")
    print(f"📊 移行後のnotion内ファイル数: {len(new_notion_files)}")
    
    if old_notion_files:
        print("⚠️  まだ移行されていないファイルがあります:")
        for file_path in old_notion_files:
            print(f"  - {file_path.name}")
    else:
        print("✅ 全てのNotionファイルが正常に移行されました")

if __name__ == "__main__":
    print("=== Notion データ移行スクリプト ===")
    print("既存の00_newディレクトリ内のNotionデータを新しい専用ディレクトリに移行します\n")
    
    migrate_notion_data()
    verify_migration()
    
    print("\n=== 移行後の推奨ディレクトリ構造 ===")
    print("""
data/
├── 00_new/              # 🆕 手動投入データ専用（健全性維持）
├── 01_analyzed/         # ✅ 分析済みデータ
├── 02_archive/          # 📦 アーカイブ
└── sources/             # 📡 外部データソース専用
    └── notion/          # 🟡 Notionデータ（処理状況はanalysis_log.jsonで管理）
""") 