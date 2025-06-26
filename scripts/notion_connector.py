#!/usr/bin/env python3
"""
Notion Connector - NotionからAGOグループの議事録を取得
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from notion_client import Client
import hashlib


class NotionConnector:
    """Notionから議事録データを取得してAGAIシステムに統合するコネクター"""
    
    def __init__(self, integration_token: Optional[str] = None, custom_data_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            integration_token: Notion内部統合トークン（環境変数からも取得可能）
            custom_data_dir: カスタムデータ保存ディレクトリ（デフォルト: data/sources/notion）
        """
        self.token = integration_token or os.environ.get('NOTION_INTEGRATION_TOKEN')
        if not self.token:
            raise ValueError("Notion統合トークンが設定されていません")
        
        self.client = Client(auth=self.token)
        
        # Notion専用ディレクトリ（シンプルに単一ディレクトリ）
        if custom_data_dir:
            self.data_dir = Path(custom_data_dir)
        else:
            self.data_dir = Path("data/sources/notion")
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 処理済みディレクトリも作成
        self.processed_dir = self.data_dir.parent / "processed"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
    def get_database_pages(self, database_id: str, 
                          filter_params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        データベースから議事録ページを取得
        
        Args:
            database_id: NotionデータベースID
            filter_params: フィルター条件（日付範囲など）
            
        Returns:
            ページリスト
        """
        try:
            # デフォルトのクエリパラメータ
            query_params = {
                "database_id": database_id,
                "page_size": 100  # 最大100件
            }
            
            # フィルター条件がある場合は追加
            if filter_params:
                query_params["filter"] = filter_params
            
            # データベースをクエリ
            response = self.client.databases.query(**query_params)
            pages = response.get("results", [])
            
            # ページネーション対応
            while response.get("has_more"):
                query_params["start_cursor"] = response.get("next_cursor")
                response = self.client.databases.query(**query_params)
                pages.extend(response.get("results", []))
            
            return pages
            
        except Exception as e:
            print(f"❌ データベース取得エラー: {e}")
            return []
    
    def extract_page_content(self, page_id: str) -> str:
        """
        ページの本文を取得してテキスト化
        
        Args:
            page_id: NotionページID
            
        Returns:
            ページ内容のテキスト
        """
        try:
            # ページのブロックを取得
            blocks = []
            response = self.client.blocks.children.list(block_id=page_id)
            blocks.extend(response.get("results", []))
            
            # ページネーション対応
            while response.get("has_more"):
                response = self.client.blocks.children.list(
                    block_id=page_id, 
                    start_cursor=response.get("next_cursor")
                )
                blocks.extend(response.get("results", []))
            
            # ブロックからテキストを抽出
            content_lines = []
            for block in blocks:
                text = self._extract_text_from_block(block)
                if text:
                    content_lines.append(text)
            
            return "\n".join(content_lines)
            
        except Exception as e:
            print(f"❌ ページ内容取得エラー: {e}")
            return ""
    
    def _extract_text_from_block(self, block: Dict[str, Any]) -> str:
        """
        ブロックからテキストを抽出（内部メソッド）
        """
        block_type = block.get("type")
        if not block_type:
            return ""
        
        # 各ブロックタイプに応じた処理
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
            rich_texts = block.get(block_type, {}).get("rich_text", [])
        elif block_type == "bulleted_list_item":
            rich_texts = block.get("bulleted_list_item", {}).get("rich_text", [])
        elif block_type == "numbered_list_item":
            rich_texts = block.get("numbered_list_item", {}).get("rich_text", [])
        elif block_type == "to_do":
            rich_texts = block.get("to_do", {}).get("rich_text", [])
            checked = block.get("to_do", {}).get("checked", False)
            prefix = "[x] " if checked else "[ ] "
            text = self._extract_text_from_rich_text(rich_texts)
            return prefix + text if text else ""
        else:
            # その他のブロックタイプ
            return ""
        
        return self._extract_text_from_rich_text(rich_texts)
    
    def _extract_text_from_rich_text(self, rich_texts: List[Dict]) -> str:
        """
        リッチテキストからプレーンテキストを抽出
        """
        texts = []
        for rt in rich_texts:
            if rt.get("type") == "text":
                texts.append(rt.get("plain_text", ""))
        return "".join(texts)
    
    def save_meeting_minutes(self, page_id: str, title: str = None) -> Optional[Path]:
        """
        議事録をファイルとして保存
        
        Args:
            page_id: NotionページID
            title: ファイル名（省略時は自動生成）
            
        Returns:
            保存したファイルパス
        """
        try:
            # ページ情報を取得
            page = self.client.pages.retrieve(page_id=page_id)
            
            # タイトルを取得
            if not title:
                title_prop = page.get("properties", {}).get("title", {})
                if title_prop.get("title"):
                    title = title_prop["title"][0].get("plain_text", "無題")
                else:
                    # Name プロパティを探す
                    for prop_name, prop_value in page.get("properties", {}).items():
                        if prop_value.get("type") == "title":
                            title = prop_value.get("title", [{}])[0].get("plain_text", "無題")
                            break
                    else:
                        title = "無題"
            
            # 作成日時を取得
            created_time = page.get("created_time", "")
            if created_time:
                created_dt = datetime.fromisoformat(created_time.replace('Z', '+00:00'))
                date_str = created_dt.strftime("%Y%m%d")
            else:
                date_str = datetime.now().strftime("%Y%m%d")
            
            # ページ内容を取得
            content = self.extract_page_content(page_id)
            
            # メタデータを追加
            full_content = f"""=== Notion議事録 ===
タイトル: {title}
作成日時: {created_time}
ページID: {page_id}
URL: {page.get('url', '')}

=== 内容 ===
{content}
"""
            
            # ファイル名を生成（重複チェック付き）
            base_filename = f"notion_{date_str}_{self._safe_filename(title)}"
            filename = base_filename + ".txt"
            filepath = self.data_dir / filename
            
            # 重複する場合は番号を付ける
            counter = 1
            while filepath.exists():
                filename = f"{base_filename}_{counter}.txt"
                filepath = self.data_dir / filename
                counter += 1
            
            # ファイルに保存
            filepath.write_text(full_content, encoding='utf-8')
            print(f"✅ 議事録を保存しました: {filepath}")
            
            return filepath
            
        except Exception as e:
            print(f"❌ 議事録保存エラー: {e}")
            return None
    
    def _safe_filename(self, filename: str) -> str:
        """安全なファイル名に変換"""
        # 使用できない文字を置換
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # 長さ制限
        if len(filename) > 50:
            filename = filename[:50]
        return filename
    
    def sync_recent_minutes(self, database_id: str, days: int = 7) -> List[Path]:
        """
        最近の議事録を同期
        
        Args:
            database_id: NotionデータベースID
            days: 何日前までの議事録を取得するか
            
        Returns:
            保存したファイルパスのリスト
        """
        try:
            # シンプルにデータベース内容を全取得（フィルターなし）
            pages = self.get_database_pages(database_id)
            print(f"📄 {len(pages)}件の議事録を取得しました")
            
            # 各ページを保存
            saved_files = []
            for page in pages:
                # 重複チェック
                if not self.check_duplicate(page["id"]):
                    filepath = self.save_meeting_minutes(page["id"])
                    if filepath:
                        saved_files.append(filepath)
                else:
                    print(f"⏩ スキップ（処理済み）: {page['id']}")
            
            return saved_files
            
        except Exception as e:
            print(f"❌ データベース取得エラー: {e}")
            return []
    
    def check_duplicate(self, page_id: str) -> bool:
        """
        重複チェック（既に処理済みかどうか）
        
        Args:
            page_id: NotionページID
            
        Returns:
            True: 既に処理済み、False: 未処理
        """
        # analysis_log.jsonをチェック
        log_file = Path("data/analysis_log.json")
        if log_file.exists():
            try:
                log_data = json.loads(log_file.read_text(encoding='utf-8'))
                # Notionページとして記録されているか確認
                for entry in log_data:
                    if entry.get("source") == "notion" and entry.get("page_id") == page_id:
                        return True
            except Exception:
                pass
        
        return False


# 使用例
if __name__ == "__main__":
    # 環境変数から設定を読み込み
    # export NOTION_INTEGRATION_TOKEN="secret_..."
    # export NOTION_DATABASE_ID="..."
    
    connector = NotionConnector()
    
    # データベースIDを環境変数から取得
    db_id = os.environ.get("NOTION_DATABASE_ID")
    if db_id:
        # 最近7日間の議事録を同期
        saved_files = connector.sync_recent_minutes(db_id, days=7)
        print(f"\n💾 {len(saved_files)}件の議事録を保存しました") 