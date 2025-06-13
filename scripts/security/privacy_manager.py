import logging
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from cryptography.fernet import Fernet
import json
import yaml

from scripts.models import Person, Activity, Document
from scripts.exceptions import ProfilingSystemError
from scripts.utils import load_yaml, ensure_directory, load_json_file, save_json_file


logger = logging.getLogger(__name__)


class PrivacyError(ProfilingSystemError):
    """プライバシー関連のエラー"""
    pass


class PrivacyManager:
    """個人情報保護とプライバシー管理を行うクラス"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path: プライバシー設定ファイルのパス
        """
        self.config_path = config_path or Path("config/privacy_config.yaml")
        self.config = self._load_config()
        self.masking_rules = self.config.get('masking_rules', {})
        self.sensitive_fields = set(self.config.get('sensitive_fields', []))
        self.encryption_enabled = self.config.get('encryption', {}).get('enabled', False)
        
        # 暗号化キーの初期化
        self._init_encryption()
        
        # マスキングカウンター（統計用）
        self.masking_stats = {
            'email': 0,
            'phone': 0,
            'name': 0,
            'address': 0,
            'custom': 0
        }
        
    def _load_config(self) -> Dict[str, Any]:
        """プライバシー設定を読み込む"""
        if self.config_path.exists():
            try:
                return load_yaml(self.config_path)
            except Exception as e:
                logger.warning(f"設定ファイルの読み込みに失敗しました: {e}")
        
        # デフォルト設定を返す
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """デフォルトのプライバシー設定を返す"""
        return {
            'masking_rules': {
                'email': {
                    'enabled': True,
                    'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    'replacement': '***@***.***'
                },
                'phone': {
                    'enabled': True,
                    'patterns': [
                        r'\d{3}-\d{4}-\d{4}',
                        r'\d{2,4}-\d{2,4}-\d{4}',
                        r'\(\d{2,4}\)\d{2,4}-\d{4}',
                        r'\+\d{1,3}\s?\d{1,4}\s?\d{1,4}\s?\d{4}'
                    ],
                    'replacement': '***-****-****'
                },
                'address': {
                    'enabled': True,
                    'keywords': ['住所', '〒', '都道府県'],
                    'replacement': '[住所は削除されました]'
                },
                'credit_card': {
                    'enabled': True,
                    'pattern': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
                    'replacement': '****-****-****-****'
                }
            },
            'sensitive_fields': [
                'password', 'secret', 'token', 'api_key', 
                'private_key', 'ssn', 'social_security'
            ],
            'encryption': {
                'enabled': False,
                'key_path': 'config/.encryption_key'
            },
            'access_control': {
                'enabled': True,
                'default_level': 'read',
                'levels': ['none', 'read', 'write', 'admin']
            }
        }
    
    def _init_encryption(self) -> None:
        """暗号化の初期化"""
        if not self.encryption_enabled:
            self.cipher = None
            return
        
        key_path = Path(self.config['encryption']['key_path'])
        
        if key_path.exists():
            # 既存のキーを読み込む
            with open(key_path, 'rb') as f:
                key = f.read()
        else:
            # 新しいキーを生成
            key = Fernet.generate_key()
            ensure_directory(key_path.parent)
            with open(key_path, 'wb') as f:
                f.write(key)
            # キーファイルのパーミッションを制限
            key_path.chmod(0o600)
        
        self.cipher = Fernet(key)
    
    def mask_person_data(self, person: Person) -> Person:
        """人物データの個人情報をマスキング
        
        Args:
            person: マスキング対象の人物
            
        Returns:
            マスキングされた人物データ（新しいインスタンス）
        """
        # 基本情報をコピー（循環参照を避けるため手動でコピー）
        masked_data = {
            'id': person.id,
            'name': person.name,
            'department': person.department,
            'role': person.role,
            'email': person.email,
            'skills': person.skills.copy() if person.skills else [],
            'metrics': person.metrics
        }
        
        # 名前のマスキング
        if self.masking_rules.get('name', {}).get('enabled', False):
            masked_data['name'] = self._mask_name(person.name)
        
        # メールアドレスのマスキング
        if self.masking_rules.get('email', {}).get('enabled', True):
            masked_data['email'] = self._mask_email(person.email)
        
        # 活動内容のマスキング（活動は含めない - 循環参照を避けるため）
        masked_data['activities'] = []
        masked_data['collaborators'] = []
        
        # 新しいPersonインスタンスを作成
        masked_person = Person(**masked_data)
        
        # 活動を個別に追加
        for activity in person.activities:
            masked_activity = self.mask_activity_data(activity)
            masked_person.add_activity(masked_activity)
        
        return masked_person
    
    def mask_activity_data(self, activity: Activity) -> Activity:
        """活動データの個人情報をマスキング
        
        Args:
            activity: マスキング対象の活動
            
        Returns:
            マスキングされた活動データ（新しいインスタンス）
        """
        # 基本情報をコピー（循環参照を避けるため手動でコピー）
        masked_data = {
            'id': activity.id,
            'type': activity.type,
            'timestamp': activity.timestamp,
            'content': self.mask_text(activity.content),
            'tags': self._filter_sensitive_tags(activity.tags),
            'participants': [],  # 参加者は含めない（循環参照を避けるため）
            'related_documents': []
        }
        
        # 新しいActivityインスタンスを作成
        return Activity(**masked_data)
    
    def mask_text(self, text: str) -> str:
        """テキスト内の個人情報をマスキング
        
        Args:
            text: マスキング対象のテキスト
            
        Returns:
            マスキングされたテキスト
        """
        masked_text = text
        
        # メールアドレスのマスキング
        email_rule = self.masking_rules.get('email', {})
        if email_rule.get('enabled', True) and 'pattern' in email_rule:
            pattern = email_rule['pattern']
            replacement = email_rule.get('replacement', '***@***.***')
            count = len(re.findall(pattern, masked_text))
            masked_text = re.sub(pattern, replacement, masked_text)
            self.masking_stats['email'] += count
        
        # 電話番号のマスキング
        phone_rule = self.masking_rules.get('phone', {})
        if phone_rule.get('enabled', True) and 'patterns' in phone_rule:
            for pattern in phone_rule['patterns']:
                count = len(re.findall(pattern, masked_text))
                masked_text = re.sub(
                    pattern, 
                    phone_rule.get('replacement', '***-****-****'), 
                    masked_text
                )
                self.masking_stats['phone'] += count
        
        # 住所のマスキング
        address_rule = self.masking_rules.get('address', {})
        if address_rule.get('enabled', True) and 'keywords' in address_rule:
            for keyword in address_rule['keywords']:
                if keyword in masked_text:
                    # キーワードを含む行をマスキング
                    lines = masked_text.split('\n')
                    masked_lines = []
                    for line in lines:
                        if keyword in line:
                            masked_lines.append(
                                address_rule.get('replacement', '[住所は削除されました]')
                            )
                            self.masking_stats['address'] += 1
                        else:
                            masked_lines.append(line)
                    masked_text = '\n'.join(masked_lines)
        
        # クレジットカード番号のマスキング
        cc_rule = self.masking_rules.get('credit_card', {})
        if cc_rule.get('enabled', True) and 'pattern' in cc_rule:
            pattern = cc_rule['pattern']
            replacement = cc_rule.get('replacement', '****-****-****-****')
            # 特別な処理: 最初と最後の数字を残す
            matches = re.finditer(pattern, masked_text)
            for match in matches:
                original = match.group()
                # ハイフンを除去して数字のみ取得
                digits_only = re.sub(r'[^\d]', '', original)
                if len(digits_only) >= 16:
                    # 最初の数字と最後の4桁を残す
                    masked_cc = f"{digits_only[0]}***-****-****-{digits_only[-4:]}"
                    masked_text = masked_text.replace(original, masked_cc)
                else:
                    masked_text = masked_text.replace(original, replacement)
                self.masking_stats['custom'] += 1
        
        # カスタムパターンのマスキング
        for rule_name, rule in self.masking_rules.items():
            if rule_name in ['email', 'phone', 'address', 'credit_card']:
                continue
            if rule.get('enabled', False) and 'pattern' in rule:
                pattern = rule['pattern']
                replacement = rule.get('replacement', '[MASKED]')
                count = len(re.findall(pattern, masked_text))
                masked_text = re.sub(pattern, replacement, masked_text)
                self.masking_stats['custom'] += count
        
        return masked_text
    
    def _mask_name(self, name: str) -> str:
        """名前をマスキング"""
        if self.masking_rules.get('name', {}).get('partial', False):
            # 部分マスキング（姓のみ表示）
            parts = name.split()
            if len(parts) >= 2:
                return f"{parts[0]} ***"
            else:
                return "***"
        else:
            # 完全マスキング
            self.masking_stats['name'] += 1
            return "***"
    
    def _mask_email(self, email: str) -> str:
        """メールアドレスをマスキング"""
        if '@' in email:
            if self.masking_rules.get('email', {}).get('partial', False):
                # 部分マスキング（ドメインのみ表示）
                local, domain = email.split('@')
                return f"***@{domain}"
            else:
                # 完全マスキング
                return self.masking_rules['email']['replacement']
        return email
    
    def _filter_sensitive_tags(self, tags: List[str]) -> List[str]:
        """センシティブなタグをフィルタリング"""
        filtered_tags = []
        for tag in tags:
            tag_lower = tag.lower()
            is_sensitive = any(
                sensitive in tag_lower 
                for sensitive in self.sensitive_fields
            )
            if not is_sensitive:
                filtered_tags.append(tag)
        return filtered_tags
    
    def encrypt_data(self, data: Any) -> str:
        """データを暗号化
        
        Args:
            data: 暗号化するデータ
            
        Returns:
            暗号化された文字列
            
        Raises:
            PrivacyError: 暗号化が無効または失敗した場合
        """
        if not self.encryption_enabled or not self.cipher:
            raise PrivacyError("暗号化が有効になっていません")
        
        try:
            # データをJSON文字列に変換
            json_data = json.dumps(data, ensure_ascii=False, default=str)
            # バイト列に変換して暗号化
            encrypted = self.cipher.encrypt(json_data.encode('utf-8'))
            # Base64エンコードされた文字列として返す
            return encrypted.decode('ascii')
        except Exception as e:
            raise PrivacyError(f"データの暗号化に失敗しました: {str(e)}")
    
    def decrypt_data(self, encrypted_data: str) -> Any:
        """暗号化されたデータを復号化
        
        Args:
            encrypted_data: 暗号化された文字列
            
        Returns:
            復号化されたデータ
            
        Raises:
            PrivacyError: 復号化が無効または失敗した場合
        """
        if not self.encryption_enabled or not self.cipher:
            raise PrivacyError("暗号化が有効になっていません")
        
        try:
            # Base64デコードして復号化
            decrypted = self.cipher.decrypt(encrypted_data.encode('ascii'))
            # JSON文字列からデータに変換
            json_data = decrypted.decode('utf-8')
            return json.loads(json_data)
        except Exception as e:
            raise PrivacyError(f"データの復号化に失敗しました: {str(e)}")
    
    def check_access_permission(self, user_level: str, required_level: str) -> bool:
        """アクセス権限をチェック
        
        Args:
            user_level: ユーザーのアクセスレベル
            required_level: 必要なアクセスレベル
            
        Returns:
            アクセスが許可されるかどうか
        """
        if not self.config.get('access_control', {}).get('enabled', True):
            return True
        
        levels = self.config['access_control']['levels']
        
        try:
            user_index = levels.index(user_level)
            required_index = levels.index(required_level)
            return user_index >= required_index
        except ValueError:
            logger.warning(f"無効なアクセスレベル: user={user_level}, required={required_level}")
            return False
    
    def anonymize_id(self, original_id: str, salt: Optional[str] = None) -> str:
        """IDを匿名化（ハッシュ化）
        
        Args:
            original_id: 元のID
            salt: ソルト（省略時は設定から取得）
            
        Returns:
            匿名化されたID
        """
        if salt is None:
            salt = self.config.get('anonymization', {}).get('salt', 'default_salt')
        
        # SHA256でハッシュ化
        combined = f"{original_id}{salt}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return hash_obj.hexdigest()[:16]  # 16文字に短縮
    
    def get_masking_report(self) -> Dict[str, Any]:
        """マスキング統計レポートを取得
        
        Returns:
            マスキング統計情報
        """
        total_masked = sum(self.masking_stats.values())
        
        return {
            'total_masked': total_masked,
            'by_type': self.masking_stats.copy(),
            'masking_rules': {
                rule: config.get('enabled', False)
                for rule, config in self.masking_rules.items()
            },
            'encryption_enabled': self.encryption_enabled
        }
    
    def save_config(self, config: Dict[str, Any], path: Optional[Path] = None) -> None:
        """プライバシー設定を保存
        
        Args:
            config: 保存する設定
            path: 保存先のパス（省略時はデフォルトパス）
        """
        save_path = path or self.config_path
        ensure_directory(save_path.parent)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        # 設定をリロード
        self.config = config
        self.masking_rules = config.get('masking_rules', {})
        self.sensitive_fields = set(config.get('sensitive_fields', []))
        self.encryption_enabled = config.get('encryption', {}).get('enabled', False)