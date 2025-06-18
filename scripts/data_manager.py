#!/usr/bin/env python3
"""
データ管理ヘルパー
新規・処理済み・アーカイブの自動管理
"""
import os
import shutil
import json
import hashlib
from datetime import datetime, timedelta

# date_utilsのインポート（相対/絶対インポートの両方に対応）
try:
    from .date_utils import get_today, get_now
except ImportError:
    from date_utils import get_today, get_now
from pathlib import Path
from typing import List, Tuple, Optional


class DataManager:
    """データのライフサイクルを管理するクラス"""
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.new_dir = self.base_dir / "00_new"
        self.analyzed_dir = self.base_dir / "01_analyzed"
        self.archive_dir = self.base_dir / "02_archive"
        self.log_file = self.base_dir / "analysis_log.json"
        
        # ディレクトリ作成
        for dir_path in [self.new_dir, self.analyzed_dir, self.archive_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # ログファイル初期化
        if not self.log_file.exists():
            self._init_log_file()
    
    def _init_log_file(self):
        """ログファイルを初期化"""
        initial_log = {
            "processed_files": [],
            "last_cleanup": get_now(),
            "statistics": {
                "total_processed": 0,
                "total_archived": 0
            }
        }
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(initial_log, f, ensure_ascii=False, indent=2)
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのハッシュ値を計算"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_new_files(self) -> List[Path]:
        """未処理ファイルのリストを取得"""
        files = []
        for ext in ['*.txt', '*.json', '*.csv', '*.log']:
            files.extend(self.new_dir.glob(ext))
        return sorted(files)
    
    def check_duplicate(self, file_path: Path) -> Tuple[bool, Optional[str]]:
        """ファイルが既に処理済みかチェック"""
        file_hash = self.calculate_file_hash(file_path)
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log = json.load(f)
        
        for record in log['processed_files']:
            if record.get('file_hash') == file_hash:
                return True, record.get('processed_date')
        
        return False, None
    
    def move_to_analyzed(self, file_path: Path, analysis_result_path: Optional[str] = None):
        """処理済みファイルを日付フォルダに移動"""
        # 重複チェック
        is_duplicate, processed_date = self.check_duplicate(file_path)
        if is_duplicate:
            print(f"⚠️  既に処理済みです: {file_path.name} (処理日: {processed_date})")
            return False
        
        # 移動先ディレクトリ作成
        today = get_today()
        dest_dir = self.analyzed_dir / today
        dest_dir.mkdir(exist_ok=True)
        
        # ファイル移動
        dest_path = dest_dir / file_path.name
        if dest_path.exists():
            # 同名ファイルが存在する場合はタイムスタンプを付加
            timestamp = datetime.now().strftime("%H%M%S")
            dest_path = dest_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
        
        shutil.move(str(file_path), str(dest_path))
        
        # ログ更新
        self._update_log(file_path, dest_path, analysis_result_path)
        
        print(f"✅ 処理完了: {file_path.name} → {dest_path.relative_to(self.base_dir)}")
        return True
    
    def _update_log(self, original_path: Path, dest_path: Path, analysis_result_path: Optional[str]):
        """処理履歴をログに記録"""
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log = json.load(f)
        
        # 新しいレコード作成
        record = {
            "filename": original_path.name,
            "original_path": str(original_path),
            "processed_date": get_now(),
            "moved_to": str(dest_path),
            "analysis_results": analysis_result_path,
            "file_hash": self.calculate_file_hash(dest_path),
            "file_size": dest_path.stat().st_size,
            "status": "completed"
        }
        
        log['processed_files'].append(record)
        log['statistics']['total_processed'] += 1
        
        # ログ保存
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
    
    def archive_old_files(self, days: int = 180):
        """指定日数以上前のファイルをアーカイブ"""
        cutoff_date = datetime.now() - timedelta(days=days)
        archived_count = 0
        
        for date_dir in self.analyzed_dir.iterdir():
            if date_dir.is_dir() and '-' in date_dir.name:
                try:
                    dir_date = datetime.strptime(date_dir.name, "%Y-%m-%d")
                    if dir_date < cutoff_date:
                        dest = self.archive_dir / date_dir.name
                        shutil.move(str(date_dir), str(dest))
                        archived_count += 1
                        print(f"📦 アーカイブ: {date_dir.name}")
                except ValueError:
                    # 日付形式でないディレクトリはスキップ
                    continue
        
        if archived_count > 0:
            # ログ更新
            with open(self.log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
            log['statistics']['total_archived'] += archived_count
            log['last_cleanup'] = get_now()
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ {archived_count}個のフォルダをアーカイブしました")
    
    def get_statistics(self):
        """処理統計を表示"""
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log = json.load(f)
        
        stats = log['statistics']
        print("\n📊 データ処理統計")
        print("=" * 40)
        print(f"総処理ファイル数: {stats['total_processed']}")
        print(f"アーカイブ済み: {stats['total_archived']}")
        print(f"最終クリーンアップ: {log['last_cleanup'][:10]}")
        
        # 現在の状況
        new_files = len(self.get_new_files())
        analyzed_dirs = len(list(self.analyzed_dir.iterdir()))
        archive_dirs = len(list(self.archive_dir.iterdir()))
        
        print(f"\n現在の状況:")
        print(f"  未処理: {new_files}ファイル")
        print(f"  処理済み: {analyzed_dirs}日分")
        print(f"  アーカイブ: {archive_dirs}日分")
    
    def cleanup_duplicates(self):
        """重複ファイルをクリーンアップ"""
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log = json.load(f)
        
        # ハッシュ値でグループ化
        hash_map = {}
        for record in log['processed_files']:
            file_hash = record.get('file_hash')
            if file_hash:
                if file_hash not in hash_map:
                    hash_map[file_hash] = []
                hash_map[file_hash].append(record)
        
        # 重複を検出
        duplicates_found = 0
        for file_hash, records in hash_map.items():
            if len(records) > 1:
                print(f"\n⚠️  重複検出: {records[0]['filename']}")
                for record in records[1:]:
                    print(f"  - {record['processed_date']}: {record['moved_to']}")
                duplicates_found += 1
        
        if duplicates_found == 0:
            print("✅ 重複ファイルは見つかりませんでした")


def main():
    """メイン実行関数"""
    import sys
    
    dm = DataManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "status":
            dm.get_statistics()
        
        elif command == "archive":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 180
            dm.archive_old_files(days)
        
        elif command == "cleanup":
            dm.cleanup_duplicates()
        
        elif command == "list":
            files = dm.get_new_files()
            if files:
                print(f"\n📁 未処理ファイル ({len(files)}個):")
                for f in files:
                    print(f"  - {f.name}")
            else:
                print("✅ 未処理ファイルはありません")
        
        else:
            print(f"❌ 不明なコマンド: {command}")
            print("\n使用方法:")
            print("  python data_manager.py status    # 統計表示")
            print("  python data_manager.py list      # 未処理一覧")
            print("  python data_manager.py archive   # アーカイブ実行")
            print("  python data_manager.py cleanup   # 重複チェック")
    
    else:
        # デフォルトは統計表示
        dm.get_statistics()


if __name__ == "__main__":
    main()