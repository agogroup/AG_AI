#!/usr/bin/env python3
"""
日付処理の共通ユーティリティ
ハードコーディングを防ぎ、一貫性のある日付処理を提供
"""
import os
from datetime import datetime, timezone
from typing import Optional
import warnings


class DateUtils:
    """日付処理の共通クラス"""
    
    @staticmethod
    def get_current_date() -> str:
        """現在の日付を取得（YYYY-MM-DD形式）"""
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def get_current_datetime() -> str:
        """現在の日時を取得（ISO形式）"""
        return datetime.now().isoformat()
    
    @staticmethod
    def get_current_timestamp() -> str:
        """現在のタイムスタンプを取得（ファイル名用）"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @staticmethod
    def validate_date_string(date_str: str) -> bool:
        """日付文字列が妥当かチェック"""
        try:
            date_obj = datetime.fromisoformat(date_str.replace('T', ' ').split('.')[0])
            current = datetime.now()
            
            # 未来の日付や極端に古い日付は警告
            if date_obj > current:
                warnings.warn(f"未来の日付が指定されています: {date_str}")
                return False
            elif (current - date_obj).days > 365 * 5:  # 5年以上前
                warnings.warn(f"5年以上前の日付が指定されています: {date_str}")
                return False
                
            return True
        except:
            return False
    
    @staticmethod
    def get_env_date() -> Optional[str]:
        """環境変数から現在日付を取得（テスト用）"""
        return os.environ.get('AGO_CURRENT_DATE')


def check_hardcoded_dates(code: str) -> list:
    """コード内のハードコーディングされた日付を検出"""
    import re
    
    # よくある日付パターン
    patterns = [
        r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        r'\d{8}',               # YYYYMMDD
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO形式
    ]
    
    hardcoded_dates = []
    for pattern in patterns:
        matches = re.findall(pattern, code)
        for match in matches:
            # 2020年以降の日付っぽいものを検出
            if match.startswith(('2020', '2021', '2022', '2023', '2024', '2025')):
                hardcoded_dates.append(match)
    
    return hardcoded_dates


# 便利な関数をモジュールレベルでエクスポート
get_today = DateUtils.get_current_date
get_now = DateUtils.get_current_datetime
get_timestamp = DateUtils.get_current_timestamp


if __name__ == "__main__":
    # 使用例
    print(f"今日の日付: {get_today()}")
    print(f"現在の日時: {get_now()}")
    print(f"タイムスタンプ: {get_timestamp()}")
    
    # ハードコーディング検出例
    test_code = '''
    record = {
        "processed_date": "2025-01-13T14:00:00",
        "created": datetime.now()
    }
    '''
    
    hardcoded = check_hardcoded_dates(test_code)
    if hardcoded:
        print(f"\n⚠️  ハードコーディングされた日付を検出: {hardcoded}")