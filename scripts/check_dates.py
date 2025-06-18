#!/usr/bin/env python3
"""
コード内のハードコーディングされた日付を検出するスクリプト
"""
import sys
import re
from pathlib import Path
from typing import List, Tuple
from datetime import datetime


def find_hardcoded_dates(file_path: Path) -> List[Tuple[int, str, str]]:
    """ファイル内のハードコーディングされた日付を検出"""
    
    # 日付パターン（2020年以降）
    patterns = [
        (r'202[0-9]-[0-1][0-9]-[0-3][0-9]', 'YYYY-MM-DD'),
        (r'202[0-9]/[0-1][0-9]/[0-3][0-9]', 'YYYY/MM/DD'),
        (r'202[0-9][0-1][0-9][0-3][0-9]', 'YYYYMMDD'),
        (r'202[0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]', 'ISO DateTime'),
    ]
    
    findings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            # コメント行はスキップ（簡易的な判定）
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
                
            # ドキュメント文字列内もスキップ（簡易的）
            if '"""' in line or "'''" in line:
                continue
                
            for pattern, format_name in patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    # 除外パターン（バージョン番号など）
                    if any(exclude in line for exclude in ['version', 'v202', '__202']):
                        continue
                        
                    findings.append((line_num, match, format_name))
                    
    except Exception as e:
        print(f"エラー: {file_path} - {e}")
        
    return findings


def check_files(file_patterns: List[str]) -> None:
    """指定されたファイルパターンをチェック"""
    
    total_issues = 0
    checked_files = 0
    
    for pattern in file_patterns:
        for file_path in Path('.').glob(pattern):
            if file_path.is_file() and file_path.suffix in ['.py', '.md', '.json']:
                checked_files += 1
                findings = find_hardcoded_dates(file_path)
                
                if findings:
                    print(f"\n📄 {file_path}")
                    print("=" * 60)
                    
                    for line_num, date_str, format_name in findings:
                        print(f"  行 {line_num}: {date_str} ({format_name})")
                        total_issues += 1
    
    print("\n" + "=" * 60)
    print(f"📊 チェック結果:")
    print(f"  - チェックしたファイル数: {checked_files}")
    print(f"  - 検出された日付: {total_issues}")
    
    if total_issues > 0:
        print("\n⚠️  ハードコーディングされた日付が見つかりました！")
        print("💡 対策: scripts/date_utils.py の関数を使用してください")
        sys.exit(1)
    else:
        print("\n✅ ハードコーディングされた日付は見つかりませんでした")


def check_single_file(file_path: str) -> bool:
    """単一ファイルをチェック（CI/CD用）"""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ ファイルが見つかりません: {file_path}")
        return False
        
    findings = find_hardcoded_dates(path)
    
    if findings:
        print(f"❌ {file_path} にハードコーディングされた日付があります:")
        for line_num, date_str, format_name in findings:
            print(f"  行 {line_num}: {date_str} ({format_name})")
        return False
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python scripts/check_dates.py <ファイルパターン>")
        print("  例: python scripts/check_dates.py '**/*.py'")
        print("  例: python scripts/check_dates.py scripts/*.py bin/*.py")
        sys.exit(1)
    
    if len(sys.argv) == 2 and Path(sys.argv[1]).is_file():
        # 単一ファイルチェック
        success = check_single_file(sys.argv[1])
        sys.exit(0 if success else 1)
    else:
        # 複数ファイルチェック
        check_files(sys.argv[1:])