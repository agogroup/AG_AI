import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime

from scripts.models import Person, Activity, Document, ActivityType
from scripts.exceptions import DataLoadError, DataValidationError
from scripts.utils import (
    generate_id, normalize_email, parse_datetime, 
    extract_tags_from_content, load_yaml
)


logger = logging.getLogger(__name__)


class DataLoader:
    """生データの読み込みと前処理を行うクラス"""
    
    def __init__(self, config_path: Path = Path("config/settings.yaml")):
        """
        Args:
            config_path: 設定ファイルのパス
        """
        self.config = load_yaml(config_path)
        self.persons: Dict[str, Person] = {}
        self.activities: List[Activity] = []
        self.documents: List[Document] = []
        
    def load_emails(self, path: Union[str, Path]) -> List[Dict[str, Any]]:
        """メールデータを読み込む
        
        Args:
            path: メールデータのパスまたはディレクトリ
            
        Returns:
            読み込んだメールデータのリスト
        """
        path = Path(path)
        emails = []
        
        try:
            if path.is_file():
                emails.extend(self._load_email_file(path))
            elif path.is_dir():
                for file_path in path.glob("**/*"):
                    if file_path.suffix.lower() in ['.csv', '.json', '.txt']:
                        emails.extend(self._load_email_file(file_path))
            else:
                raise DataLoadError(f"パスが見つかりません: {path}")
                
            logger.info(f"{len(emails)}件のメールを読み込みました")
            return emails
            
        except Exception as e:
            raise DataLoadError(f"メールの読み込みに失敗しました: {str(e)}")
    
    def _load_email_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """個別のメールファイルを読み込む"""
        emails = []
        
        if file_path.suffix.lower() == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    emails.append(self._normalize_email_data(row))
                    
        elif file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    emails.extend([self._normalize_email_data(item) for item in data])
                else:
                    emails.append(self._normalize_email_data(data))
                    
        elif file_path.suffix.lower() == '.txt':
            # 簡易的なテキストパーサー（実際のフォーマットに応じて調整）
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                emails.append({
                    'content': content,
                    'timestamp': datetime.now().isoformat(),
                    'file_path': str(file_path)
                })
                
        return emails
    
    def _normalize_email_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """メールデータを正規化"""
        normalized = {
            'id': data.get('id') or generate_id('email', str(data)),
            'from': normalize_email(data.get('from', data.get('sender', ''))),
            'to': self._parse_recipients(data.get('to', data.get('recipients', ''))),
            'cc': self._parse_recipients(data.get('cc', '')),
            'subject': data.get('subject', ''),
            'content': data.get('content', data.get('body', '')),
            'timestamp': self._parse_timestamp(data.get('timestamp', data.get('date', ''))),
            'attachments': data.get('attachments', [])
        }
        
        # タグの抽出
        normalized['tags'] = extract_tags_from_content(
            f"{normalized['subject']} {normalized['content']}"
        )
        
        return normalized
    
    def _parse_recipients(self, recipients: Union[str, List[str]]) -> List[str]:
        """受信者リストをパース"""
        if isinstance(recipients, list):
            return [normalize_email(r) for r in recipients if r]
        elif isinstance(recipients, str):
            # カンマ区切りまたはセミコロン区切りを想定
            return [normalize_email(r.strip()) for r in recipients.replace(';', ',').split(',') if r.strip()]
        return []
    
    def _parse_timestamp(self, timestamp: Any) -> datetime:
        """タイムスタンプをパース"""
        if isinstance(timestamp, datetime):
            return timestamp
        elif isinstance(timestamp, str):
            try:
                return parse_datetime(timestamp)
            except ValueError:
                logger.warning(f"タイムスタンプの解析に失敗: {timestamp}")
                return datetime.now()
        else:
            return datetime.now()
    
    def load_documents(self, path: Union[str, Path]) -> List[Dict[str, Any]]:
        """文書データを読み込む
        
        Args:
            path: 文書データのパスまたはディレクトリ
            
        Returns:
            読み込んだ文書データのリスト
        """
        path = Path(path)
        documents = []
        
        try:
            if path.is_file():
                documents.append(self._load_document_file(path))
            elif path.is_dir():
                for file_path in path.glob("**/*"):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        documents.append(self._load_document_file(file_path))
            else:
                raise DataLoadError(f"パスが見つかりません: {path}")
                
            logger.info(f"{len(documents)}件の文書を読み込みました")
            return documents
            
        except Exception as e:
            raise DataLoadError(f"文書の読み込みに失敗しました: {str(e)}")
    
    def _load_document_file(self, file_path: Path) -> Dict[str, Any]:
        """個別の文書ファイルを読み込む"""
        stat = file_path.stat()
        
        document = {
            'id': generate_id('doc', str(file_path)),
            'title': file_path.stem,
            'path': str(file_path),
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
            'size': stat.st_size,
            'extension': file_path.suffix
        }
        
        # テキストファイルの場合は内容も読み込む
        if file_path.suffix.lower() in ['.txt', '.md', '.csv', '.json']:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    document['content'] = f.read()
                    document['tags'] = extract_tags_from_content(document['content'])
            except Exception as e:
                logger.warning(f"ファイル内容の読み込みに失敗: {file_path} - {str(e)}")
                document['content'] = None
                document['tags'] = []
        else:
            document['content'] = None
            document['tags'] = []
            
        return document
    
    def preprocess(self, data_type: str, raw_data: List[Dict[str, Any]]) -> None:
        """データの前処理とモデルへの変換
        
        Args:
            data_type: データタイプ（'email', 'document', 'log'）
            raw_data: 生データのリスト
        """
        if data_type == 'email':
            self._preprocess_emails(raw_data)
        elif data_type == 'document':
            self._preprocess_documents(raw_data)
        elif data_type == 'log':
            self._preprocess_logs(raw_data)
        else:
            raise DataValidationError(f"不明なデータタイプ: {data_type}")
    
    def _preprocess_emails(self, emails: List[Dict[str, Any]]) -> None:
        """メールデータの前処理"""
        for email_data in emails:
            # 送信者のPersonオブジェクトを取得または作成
            sender_email = email_data['from']
            if sender_email and sender_email not in self.persons:
                self.persons[sender_email] = Person(
                    id=generate_id('p', sender_email),
                    name=self._extract_name_from_email(sender_email),
                    department="未分類",
                    role="未設定",
                    email=sender_email
                )
            
            # Activityオブジェクトを作成
            activity = Activity(
                id=email_data['id'],
                type=ActivityType.EMAIL,
                timestamp=email_data['timestamp'],
                content=f"件名: {email_data['subject']}\n\n{email_data['content']}",
                tags=email_data['tags']
            )
            
            # 参加者を追加
            if sender_email and sender_email in self.persons:
                activity.add_participant(self.persons[sender_email])
                self.persons[sender_email].add_activity(activity)
            
            # 受信者を処理
            all_recipients = email_data['to'] + email_data['cc']
            for recipient_email in all_recipients:
                if recipient_email and recipient_email not in self.persons:
                    self.persons[recipient_email] = Person(
                        id=generate_id('p', recipient_email),
                        name=self._extract_name_from_email(recipient_email),
                        department="未分類",
                        role="未設定",
                        email=recipient_email
                    )
                
                if recipient_email and recipient_email in self.persons:
                    activity.add_participant(self.persons[recipient_email])
                    self.persons[recipient_email].add_activity(activity)
            
            # 協働者の関係を更新
            participants = [p for p in activity.participants]
            for i, person1 in enumerate(participants):
                for person2 in participants[i+1:]:
                    person1.add_collaborator(person2)
                    person2.add_collaborator(person1)
            
            self.activities.append(activity)
    
    def _preprocess_documents(self, documents: List[Dict[str, Any]]) -> None:
        """文書データの前処理"""
        for doc_data in documents:
            document = Document(
                id=doc_data['id'],
                title=doc_data['title'],
                path=doc_data['path'],
                content=doc_data.get('content'),
                created_at=doc_data['created_at'],
                modified_at=doc_data['modified_at'],
                tags=doc_data.get('tags', [])
            )
            
            self.documents.append(document)
            
            # 文書に関連するActivityを作成
            if document.content:
                activity = Activity(
                    id=generate_id('a', f"doc_{document.id}"),
                    type=ActivityType.DOCUMENT,
                    timestamp=document.modified_at,
                    content=f"文書: {document.title}",
                    tags=document.tags
                )
                activity.related_documents.append(document)
                self.activities.append(activity)
    
    def _preprocess_logs(self, logs: List[Dict[str, Any]]) -> None:
        """ログデータの前処理（今後実装）"""
        # TODO: ログデータの前処理ロジックを実装
        pass
    
    def _extract_name_from_email(self, email: str) -> str:
        """メールアドレスから名前を推測"""
        local_part = email.split('@')[0]
        # ドットやアンダースコアを空白に置換
        name = local_part.replace('.', ' ').replace('_', ' ')
        # 各単語の先頭を大文字に
        return name.title()
    
    def get_summary(self) -> Dict[str, Any]:
        """読み込んだデータのサマリーを取得"""
        return {
            'persons': len(self.persons),
            'activities': len(self.activities),
            'documents': len(self.documents),
            'email_activities': len([a for a in self.activities if a.type == ActivityType.EMAIL]),
            'document_activities': len([a for a in self.activities if a.type == ActivityType.DOCUMENT])
        }