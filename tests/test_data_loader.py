import pytest
import json
import csv
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from scripts.data_loader import DataLoader
from scripts.models import ActivityType
from scripts.exceptions import DataLoadError


class TestDataLoader:
    
    @pytest.fixture
    def temp_dir(self):
        """テスト用の一時ディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def data_loader(self):
        """DataLoaderのインスタンスを作成"""
        return DataLoader()
    
    @pytest.fixture
    def sample_email_csv(self, temp_dir):
        """サンプルのメールCSVファイルを作成"""
        csv_path = temp_dir / "emails.csv"
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['from', 'to', 'cc', 'subject', 'content', 'timestamp'])
            writer.writeheader()
            writer.writerow({
                'from': 'yamada@example.com',
                'to': 'tanaka@example.com;suzuki@example.com',
                'cc': 'sato@example.com',
                'subject': '会議の件',
                'content': '明日の会議についてご連絡します。',
                'timestamp': '2024-01-15 10:30:00'
            })
            writer.writerow({
                'from': 'tanaka@example.com',
                'to': 'yamada@example.com',
                'cc': '',
                'subject': 'Re: 会議の件',
                'content': '了解しました。',
                'timestamp': '2024-01-15 11:00:00'
            })
        return csv_path
    
    @pytest.fixture
    def sample_email_json(self, temp_dir):
        """サンプルのメールJSONファイルを作成"""
        json_path = temp_dir / "emails.json"
        emails = [
            {
                'sender': 'sato@example.com',
                'recipients': ['yamada@example.com'],
                'subject': '資料送付',
                'body': '資料を添付します。',
                'date': '2024-01-16T09:00:00'
            }
        ]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(emails, f, ensure_ascii=False)
        return json_path
    
    @pytest.fixture
    def sample_documents(self, temp_dir):
        """サンプルの文書ファイルを作成"""
        # テキストファイル
        txt_path = temp_dir / "report.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write("月次レポート\n\n売上は前月比10%増加しました。#売上 #レポート")
        
        # Markdownファイル
        md_path = temp_dir / "notes.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# 会議メモ\n\n## 議題\n- 新規プロジェクト\n- 予算配分\n\n【重要】来月までに決定")
        
        return temp_dir
    
    def test_load_emails_csv(self, data_loader, sample_email_csv):
        """CSVファイルからのメール読み込みテスト"""
        emails = data_loader.load_emails(sample_email_csv)
        
        assert len(emails) == 2
        assert emails[0]['from'] == 'yamada@example.com'
        assert emails[0]['to'] == ['tanaka@example.com', 'suzuki@example.com']
        assert emails[0]['cc'] == ['sato@example.com']
        assert emails[0]['subject'] == '会議の件'
        assert isinstance(emails[0]['timestamp'], datetime)
    
    def test_load_emails_json(self, data_loader, sample_email_json):
        """JSONファイルからのメール読み込みテスト"""
        emails = data_loader.load_emails(sample_email_json)
        
        assert len(emails) == 1
        assert emails[0]['from'] == 'sato@example.com'
        assert emails[0]['to'] == ['yamada@example.com']
        assert emails[0]['subject'] == '資料送付'
    
    def test_load_emails_directory(self, data_loader, sample_email_csv, sample_email_json):
        """ディレクトリからのメール読み込みテスト"""
        emails = data_loader.load_emails(sample_email_csv.parent)
        
        # CSVとJSONの両方が読み込まれる
        assert len(emails) == 3
    
    def test_load_emails_invalid_path(self, data_loader):
        """無効なパスでのエラーテスト"""
        with pytest.raises(DataLoadError):
            data_loader.load_emails("/non/existent/path")
    
    def test_load_documents(self, data_loader, sample_documents):
        """文書ファイルの読み込みテスト"""
        documents = data_loader.load_documents(sample_documents)
        
        assert len(documents) == 2
        
        # テキストファイルの確認
        txt_doc = next(d for d in documents if d['title'] == 'report')
        assert txt_doc['extension'] == '.txt'
        assert '月次レポート' in txt_doc['content']
        assert '売上' in txt_doc['tags']
        assert 'レポート' in txt_doc['tags']
        
        # Markdownファイルの確認
        md_doc = next(d for d in documents if d['title'] == 'notes')
        assert md_doc['extension'] == '.md'
        assert '会議メモ' in md_doc['content']
        assert '重要' in md_doc['tags']
    
    def test_preprocess_emails(self, data_loader, sample_email_csv):
        """メールデータの前処理テスト"""
        emails = data_loader.load_emails(sample_email_csv)
        data_loader.preprocess('email', emails)
        
        # Personオブジェクトの確認
        assert len(data_loader.persons) == 4  # yamada, tanaka, suzuki, sato
        assert 'yamada@example.com' in data_loader.persons
        assert 'tanaka@example.com' in data_loader.persons
        
        # Activityオブジェクトの確認
        assert len(data_loader.activities) == 2
        assert all(a.type == ActivityType.EMAIL for a in data_loader.activities)
        
        # 協働者の関係確認
        yamada = data_loader.persons['yamada@example.com']
        tanaka = data_loader.persons['tanaka@example.com']
        assert tanaka in yamada.collaborators
        assert yamada in tanaka.collaborators
    
    def test_preprocess_documents(self, data_loader, sample_documents):
        """文書データの前処理テスト"""
        documents = data_loader.load_documents(sample_documents)
        data_loader.preprocess('document', documents)
        
        # Documentオブジェクトの確認
        assert len(data_loader.documents) == 2
        
        # 関連Activityの確認
        assert len(data_loader.activities) == 2
        assert all(a.type == ActivityType.DOCUMENT for a in data_loader.activities)
    
    def test_normalize_email_data(self, data_loader):
        """メールデータの正規化テスト"""
        raw_data = {
            'sender': 'Test.User@EXAMPLE.COM',
            'recipients': 'user1@example.com;user2@example.com',
            'subject': 'テスト',
            'body': 'テスト本文'
        }
        
        normalized = data_loader._normalize_email_data(raw_data)
        
        assert normalized['from'] == 'test.user@example.com'
        assert normalized['to'] == ['user1@example.com', 'user2@example.com']
        assert normalized['subject'] == 'テスト'
        assert normalized['content'] == 'テスト本文'
    
    def test_extract_name_from_email(self, data_loader):
        """メールアドレスからの名前抽出テスト"""
        assert data_loader._extract_name_from_email('taro.yamada@example.com') == 'Taro Yamada'
        assert data_loader._extract_name_from_email('tanaka_hanako@example.com') == 'Tanaka Hanako'
        assert data_loader._extract_name_from_email('suzuki@example.com') == 'Suzuki'
    
    def test_get_summary(self, data_loader, sample_email_csv, sample_documents):
        """サマリー取得テスト"""
        # メールとドキュメントを読み込んで前処理
        emails = data_loader.load_emails(sample_email_csv)
        data_loader.preprocess('email', emails)
        
        documents = data_loader.load_documents(sample_documents)
        data_loader.preprocess('document', documents)
        
        summary = data_loader.get_summary()
        
        assert summary['persons'] == 4
        # emails.csvファイルも文書として読み込まれるため、実際は5つのアクティビティ
        assert summary['activities'] == 5  # 2 emails + 3 documents (2 created + 1 csv)
        assert summary['documents'] == 3  # report.txt, notes.md, emails.csv
        assert summary['email_activities'] == 2
        assert summary['document_activities'] == 3