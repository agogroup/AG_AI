import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml
import json


def generate_id(prefix: str, value: str) -> str:
    """プレフィックス付きのユニークIDを生成
    
    Args:
        prefix: IDのプレフィックス（例: 'p' for person, 'a' for activity）
        value: ハッシュ化する値
    
    Returns:
        生成されたID（例: 'p_a1b2c3d4'）
    """
    hash_object = hashlib.md5(value.encode())
    return f"{prefix}_{hash_object.hexdigest()[:8]}"


def normalize_email(email: str) -> str:
    """メールアドレスを正規化
    
    Args:
        email: メールアドレス
    
    Returns:
        正規化されたメールアドレス
    """
    return email.lower().strip()


def extract_domain(email: str) -> str:
    """メールアドレスからドメインを抽出
    
    Args:
        email: メールアドレス
    
    Returns:
        ドメイン名
    """
    return email.split('@')[-1].lower()


def parse_datetime(date_string: str) -> datetime:
    """日時文字列をdatetimeオブジェクトに変換
    
    Args:
        date_string: 日時文字列
    
    Returns:
        datetimeオブジェクト
    """
    # 複数のフォーマットを試行
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%Y/%m/%d"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"日時文字列 '{date_string}' を解析できません")


def sanitize_filename(filename: str) -> str:
    """ファイル名として使用できるように文字列をサニタイズ
    
    Args:
        filename: 元のファイル名
    
    Returns:
        サニタイズされたファイル名
    """
    # 使用できない文字を置換
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 連続するスペースやアンダースコアを単一に
    filename = re.sub(r'[\s_]+', '_', filename)
    # 先頭と末尾の空白文字を削除
    return filename.strip()


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """YAMLファイルを読み込む
    
    Args:
        file_path: YAMLファイルのパス
    
    Returns:
        読み込んだデータ
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_json(data: Any, file_path: Path) -> None:
    """データをJSONファイルに保存
    
    Args:
        data: 保存するデータ
        file_path: 保存先のパス
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def extract_tags_from_content(content: str) -> List[str]:
    """コンテンツからタグを抽出
    
    Args:
        content: テキストコンテンツ
    
    Returns:
        抽出されたタグのリスト
    """
    # ハッシュタグを抽出
    hashtags = re.findall(r'#(\w+)', content)
    
    # 括弧内のキーワードを抽出
    keywords = re.findall(r'【(.+?)】', content)
    keywords.extend(re.findall(r'\[(.+?)\]', content))
    
    # 重複を除去して小文字に統一
    tags = list(set([tag.lower() for tag in hashtags + keywords]))
    
    return tags


def mask_personal_info(text: str, patterns: Dict[str, str]) -> str:
    """個人情報をマスキング
    
    Args:
        text: 元のテキスト
        patterns: マスキングパターンの辞書
    
    Returns:
        マスキング済みテキスト
    """
    masked_text = text
    
    # メールアドレスのマスキング
    if 'email' in patterns:
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        masked_text = re.sub(email_pattern, patterns['email'], masked_text)
    
    # 電話番号のマスキング
    if 'phone' in patterns:
        phone_patterns = [
            r'\d{3}-\d{4}-\d{4}',  # 090-1234-5678
            r'\d{2,4}-\d{2,4}-\d{4}',  # 03-1234-5678
            r'\(\d{2,4}\)\d{2,4}-\d{4}',  # (03)1234-5678
        ]
        for pattern in phone_patterns:
            masked_text = re.sub(pattern, patterns['phone'], masked_text)
    
    return masked_text


def calculate_similarity(text1: str, text2: str) -> float:
    """2つのテキストの類似度を計算（簡易版）
    
    Args:
        text1: テキスト1
        text2: テキスト2
    
    Returns:
        類似度（0.0〜1.0）
    """
    # 単語に分割
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    # Jaccard係数を計算
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)


def ensure_directory(path: Path) -> None:
    """ディレクトリが存在しない場合は作成
    
    Args:
        path: ディレクトリパス
    """
    path.mkdir(parents=True, exist_ok=True)