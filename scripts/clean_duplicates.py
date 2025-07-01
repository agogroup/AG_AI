#!/usr/bin/env python3
"""
重複したNotionファイルの検出・削除スクリプト
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
import hashlib


def calculate_file_hash(filepath: Path) -> str:
    """ファイルのハッシュ値を計算"""
    hash_sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


def find_duplicate_files(directory: Path) -> Dict[str, List[Path]]:
    """重複ファイルを検出"""
    file_hashes = {}
    
    for filepath in directory.glob("notion_*.txt"):
        if filepath.is_file():
            file_hash = calculate_file_hash(filepath)
            if file_hash not in file_hashes:
                file_hashes[file_hash] = []
            file_hashes[file_hash].append(filepath)
    
    # 重複があるもののみ返す
    duplicates = {hash_val: files for hash_val, files in file_hashes.items() if len(files) > 1}
    return duplicates


def find_naming_pattern_duplicates(directory: Path) -> List[Tuple[Path, Path]]:
    """ファイル名パターンによる重複を検出（_1.txt付きとなし）"""
    files = list(directory.glob("notion_*.txt"))
    duplicates = []
    
    for file in files:
        if file.name.endswith("_1.txt"):
            # _1.txtを除いた名前で同名ファイルを探す
            base_name = file.name[:-6] + ".txt"  # _1.txtを.txtに変更
            base_file = directory / base_name
            if base_file.exists():
                duplicates.append((file, base_file))
    
    return duplicates


def clean_duplicates(directory: Path, dry_run: bool = True) -> Dict[str, int]:
    """重複ファイルをクリーンアップ"""
    stats = {
        "content_duplicates": 0,
        "naming_duplicates": 0,
        "total_removed": 0
    }
    
    print(f"🔍 重複ファイル検索中: {directory}")
    
    # 1. 内容による重複チェック
    content_duplicates = find_duplicate_files(directory)
    if content_duplicates:
        print(f"\n📄 内容が同じファイル: {len(content_duplicates)}グループ")
        for i, (hash_val, files) in enumerate(content_duplicates.items(), 1):
            print(f"\n  グループ {i} ({len(files)}件):")
            # 最初のファイルを残し、残りを削除対象にする
            files_sorted = sorted(files, key=lambda x: x.name)
            keep_file = files_sorted[0]
            remove_files = files_sorted[1:]
            
            print(f"    ✅ 保持: {keep_file.name}")
            for remove_file in remove_files:
                print(f"    ❌ 削除対象: {remove_file.name}")
                if not dry_run:
                    remove_file.unlink()
                    print(f"       → 削除完了")
                stats["content_duplicates"] += 1
    
    # 2. ファイル名パターンによる重複チェック
    naming_duplicates = find_naming_pattern_duplicates(directory)
    if naming_duplicates:
        print(f"\n📝 ファイル名パターンによる重複: {len(naming_duplicates)}ペア")
        for i, (numbered_file, base_file) in enumerate(naming_duplicates, 1):
            print(f"\n  ペア {i}:")
            print(f"    📄 {base_file.name} ({base_file.stat().st_size} bytes)")
            print(f"    📄 {numbered_file.name} ({numbered_file.stat().st_size} bytes)")
            
            # 内容を比較
            if base_file.read_text(encoding='utf-8') == numbered_file.read_text(encoding='utf-8'):
                print(f"    ✅ 内容が同じ → {numbered_file.name}を削除")
                if not dry_run:
                    numbered_file.unlink()
                    print(f"       → 削除完了")
                stats["naming_duplicates"] += 1
            else:
                print(f"    ⚠️  内容が異なる → 手動確認が必要")
    
    stats["total_removed"] = stats["content_duplicates"] + stats["naming_duplicates"]
    return stats


def main():
    """メイン処理"""
    notion_dir = Path("data/sources/notion")
    
    if not notion_dir.exists():
        print(f"❌ ディレクトリが存在しません: {notion_dir}")
        return 1
    
    print("=" * 60)
    print("🧹 Notion議事録重複ファイル クリーンアップツール")
    print("=" * 60)
    
    # ドライランで重複を確認
    print("\n【ドライラン】重複ファイルの検出...")
    stats_dry = clean_duplicates(notion_dir, dry_run=True)
    
    if stats_dry["total_removed"] == 0:
        print("\n✅ 重複ファイルは見つかりませんでした")
        return 0
    
    print(f"\n📊 重複ファイル統計:")
    print(f"  - 内容による重複: {stats_dry['content_duplicates']}件")
    print(f"  - 命名による重複: {stats_dry['naming_duplicates']}件")
    print(f"  - 削除対象合計: {stats_dry['total_removed']}件")
    
    # 実行確認
    print(f"\n🔧 {stats_dry['total_removed']}件のファイルを削除しますか？")
    response = input("実行する場合は 'yes' を入力: ").strip().lower()
    
    if response == 'yes':
        print("\n🗑️  重複ファイルを削除中...")
        stats_real = clean_duplicates(notion_dir, dry_run=False)
        
        print(f"\n✅ クリーンアップ完了!")
        print(f"  - 削除されたファイル: {stats_real['total_removed']}件")
        
        # 残存ファイル数を確認
        remaining_files = len(list(notion_dir.glob("notion_*.txt")))
        print(f"  - 残存ファイル: {remaining_files}件")
        
    else:
        print("\n❌ クリーンアップをキャンセルしました")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 