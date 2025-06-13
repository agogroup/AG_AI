import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from scripts.security.privacy_manager import PrivacyManager, PrivacyError
from scripts.models import Person, Activity, ActivityType
import yaml


class TestPrivacyManager:
    
    @pytest.fixture
    def temp_config_dir(self):
        """テスト用の一時設定ディレクトリを作成"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def privacy_manager(self, temp_config_dir):
        """PrivacyManagerのインスタンスを作成"""
        config_path = Path(temp_config_dir) / "privacy_config.yaml"
        return PrivacyManager(config_path=config_path)
    
    @pytest.fixture
    def custom_config(self, temp_config_dir):
        """カスタム設定を持つPrivacyManagerを作成"""
        config_path = Path(temp_config_dir) / "custom_privacy_config.yaml"
        config = {
            'masking_rules': {
                'email': {'enabled': True, 'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'replacement': '***@***.***'},
                'phone': {'enabled': True, 'patterns': [r'\d{3}-\d{4}-\d{4}'], 'replacement': '***-****-****'},
                'name': {'enabled': True, 'partial': True}
            },
            'encryption': {'enabled': True, 'key_path': str(Path(temp_config_dir) / '.encryption_key')},
            'access_control': {'enabled': True, 'levels': ['none', 'read', 'write', 'admin']}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        return PrivacyManager(config_path=config_path)
    
    @pytest.fixture
    def sample_person(self):
        """サンプルの人物データを作成"""
        person = Person(
            id='p001',
            name='山田太郎',
            department='営業部',
            role='課長',
            email='yamada.taro@example.com'
        )
        
        activity = Activity(
            id='a001',
            type=ActivityType.EMAIL,
            timestamp=datetime.now(),
            content='山田太郎です。090-1234-5678までご連絡ください。',
            tags=['連絡先', 'password123']
        )
        activity.add_participant(person)
        person.add_activity(activity)
        
        return person
    
    def test_privacy_manager_initialization(self, privacy_manager):
        """PrivacyManagerの初期化テスト"""
        assert privacy_manager.config is not None
        assert 'masking_rules' in privacy_manager.config
        assert privacy_manager.encryption_enabled == False  # デフォルトは無効
        assert len(privacy_manager.sensitive_fields) > 0
    
    def test_mask_text_email(self, privacy_manager):
        """メールアドレスのマスキングテスト"""
        text = "連絡先: yamada@example.com または tanaka@company.co.jp"
        masked = privacy_manager.mask_text(text)
        
        assert "yamada@example.com" not in masked
        assert "tanaka@company.co.jp" not in masked
        assert "***@***.***" in masked
        assert privacy_manager.masking_stats['email'] == 2
    
    def test_mask_text_phone(self, privacy_manager):
        """電話番号のマスキングテスト"""
        text = "電話: 090-1234-5678 または 03-1234-5678"
        masked = privacy_manager.mask_text(text)
        
        assert "090-1234-5678" not in masked
        assert "03-1234-5678" not in masked
        assert "***-****-****" in masked
        assert privacy_manager.masking_stats['phone'] >= 2
    
    def test_mask_text_address(self, privacy_manager):
        """住所のマスキングテスト"""
        text = "住所: 東京都千代田区丸の内1-1-1"
        masked = privacy_manager.mask_text(text)
        
        assert "東京都千代田区" not in masked
        assert "[住所は削除されました]" in masked
        assert privacy_manager.masking_stats['address'] == 1
    
    def test_mask_text_credit_card(self, privacy_manager):
        """クレジットカード番号のマスキングテスト"""
        text = "カード番号: 1234-5678-9012-3456"
        masked = privacy_manager.mask_text(text)
        
        assert "1234-5678-9012-3456" not in masked
        # デフォルトでは最初と最後の数字を残す
        assert "1***-****-****-3456" in masked
    
    def test_mask_person_data(self, privacy_manager, sample_person):
        """人物データのマスキングテスト"""
        masked_person = privacy_manager.mask_person_data(sample_person)
        
        assert masked_person.id == sample_person.id
        assert masked_person.email == "***@***.***"
        assert len(masked_person.activities) == len(sample_person.activities)
        
        # 活動内容もマスキングされているか確認
        masked_activity = masked_person.activities[0]
        assert "090-1234-5678" not in masked_activity.content
        assert "***-****-****" in masked_activity.content
    
    def test_mask_activity_data(self, privacy_manager):
        """活動データのマスキングテスト"""
        activity = Activity(
            id='a002',
            type=ActivityType.MEETING,
            timestamp=datetime.now(),
            content='会議参加者: yamada@example.com, 電話: 090-1234-5678',
            tags=['meeting', 'api_key_12345']
        )
        
        masked_activity = privacy_manager.mask_activity_data(activity)
        
        assert "yamada@example.com" not in masked_activity.content
        assert "090-1234-5678" not in masked_activity.content
        assert "***@***.***" in masked_activity.content
        assert "***-****-****" in masked_activity.content
        
        # センシティブなタグが除去されているか
        assert 'meeting' in masked_activity.tags
        assert 'api_key_12345' not in masked_activity.tags
    
    def test_mask_name_partial(self, custom_config):
        """名前の部分マスキングテスト"""
        name = "山田 太郎"
        masked = custom_config._mask_name(name)
        
        assert masked == "山田 ***"
        assert custom_config.masking_stats['name'] == 0  # 部分マスキングはカウントされない
    
    def test_mask_email_partial(self, privacy_manager):
        """メールアドレスの部分マスキングテスト"""
        # 部分マスキングを有効化
        privacy_manager.masking_rules['email']['partial'] = True
        
        email = "yamada@example.com"
        masked = privacy_manager._mask_email(email)
        
        assert masked == "***@example.com"
    
    def test_filter_sensitive_tags(self, privacy_manager):
        """センシティブなタグのフィルタリングテスト"""
        tags = ['normal', 'password123', 'api_key_xyz', 'secret_data', 'public']
        filtered = privacy_manager._filter_sensitive_tags(tags)
        
        assert 'normal' in filtered
        assert 'public' in filtered
        assert 'password123' not in filtered
        assert 'api_key_xyz' not in filtered
        assert 'secret_data' not in filtered
    
    def test_encryption_decryption(self, custom_config):
        """暗号化・復号化のテスト"""
        # 暗号化が有効な設定を使用
        test_data = {
            'name': '山田太郎',
            'email': 'yamada@example.com',
            'sensitive': 'secret_information'
        }
        
        # 暗号化
        encrypted = custom_config.encrypt_data(test_data)
        assert isinstance(encrypted, str)
        assert encrypted != str(test_data)
        
        # 復号化
        decrypted = custom_config.decrypt_data(encrypted)
        assert decrypted == test_data
    
    def test_encryption_disabled(self, privacy_manager):
        """暗号化が無効な場合のテスト"""
        with pytest.raises(PrivacyError):
            privacy_manager.encrypt_data({'test': 'data'})
        
        with pytest.raises(PrivacyError):
            privacy_manager.decrypt_data('encrypted_string')
    
    def test_check_access_permission(self, privacy_manager):
        """アクセス権限チェックのテスト"""
        # アクセスレベル: none < read < write < admin
        
        # adminユーザーは全てのレベルにアクセス可能
        assert privacy_manager.check_access_permission('admin', 'none') == True
        assert privacy_manager.check_access_permission('admin', 'read') == True
        assert privacy_manager.check_access_permission('admin', 'write') == True
        assert privacy_manager.check_access_permission('admin', 'admin') == True
        
        # readユーザーはread以下にアクセス可能
        assert privacy_manager.check_access_permission('read', 'none') == True
        assert privacy_manager.check_access_permission('read', 'read') == True
        assert privacy_manager.check_access_permission('read', 'write') == False
        assert privacy_manager.check_access_permission('read', 'admin') == False
        
        # 無効なレベル
        assert privacy_manager.check_access_permission('invalid', 'read') == False
    
    def test_anonymize_id(self, privacy_manager):
        """ID匿名化のテスト"""
        original_id = "user_12345"
        
        # 同じIDとソルトは同じハッシュを生成
        hash1 = privacy_manager.anonymize_id(original_id)
        hash2 = privacy_manager.anonymize_id(original_id)
        assert hash1 == hash2
        assert len(hash1) == 16
        
        # 異なるIDは異なるハッシュを生成
        hash3 = privacy_manager.anonymize_id("user_67890")
        assert hash3 != hash1
        
        # 異なるソルトは異なるハッシュを生成
        hash4 = privacy_manager.anonymize_id(original_id, salt="different_salt")
        assert hash4 != hash1
    
    def test_get_masking_report(self, privacy_manager):
        """マスキングレポート取得のテスト"""
        # いくつかのマスキング操作を実行
        privacy_manager.mask_text("email: test@example.com")
        privacy_manager.mask_text("phone: 090-1234-5678")
        
        report = privacy_manager.get_masking_report()
        
        assert 'total_masked' in report
        assert report['total_masked'] > 0
        assert 'by_type' in report
        assert report['by_type']['email'] == 1
        assert report['by_type']['phone'] == 1
        assert 'masking_rules' in report
        assert 'encryption_enabled' in report
    
    def test_save_and_load_config(self, temp_config_dir):
        """設定の保存と読み込みテスト"""
        config_path = Path(temp_config_dir) / "test_config.yaml"
        manager = PrivacyManager(config_path=config_path)
        
        # カスタム設定を作成
        custom_config = {
            'masking_rules': {
                'email': {'enabled': False},
                'custom_pattern': {
                    'enabled': True,
                    'pattern': r'ID:\s*\d+',
                    'replacement': 'ID: [MASKED]'
                }
            },
            'sensitive_fields': ['custom_field'],
            'encryption': {'enabled': True, 'key_path': 'custom_key_path'}
        }
        
        # 設定を保存
        manager.save_config(custom_config)
        
        # 新しいインスタンスで設定を読み込む
        new_manager = PrivacyManager(config_path=config_path)
        
        assert new_manager.masking_rules['email']['enabled'] == False
        assert 'custom_pattern' in new_manager.masking_rules
        assert 'custom_field' in new_manager.sensitive_fields
        assert new_manager.encryption_enabled == True
    
    def test_custom_pattern_masking(self, temp_config_dir):
        """カスタムパターンのマスキングテスト"""
        config_path = Path(temp_config_dir) / "custom_pattern_config.yaml"
        config = {
            'masking_rules': {
                'employee_id': {
                    'enabled': True,
                    'pattern': r'EMP\d{6}',
                    'replacement': 'EMP******'
                }
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        manager = PrivacyManager(config_path=config_path)
        
        text = "従業員ID: EMP123456 の情報"
        masked = manager.mask_text(text)
        
        assert "EMP123456" not in masked
        assert "EMP******" in masked
        assert manager.masking_stats['custom'] == 1