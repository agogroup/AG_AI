#!/usr/bin/env python3
"""
音声処理設定ファイル
音声ファイル処理の最適化設定とエラーハンドリング
"""
from pathlib import Path
from typing import Dict, List, Optional
import os

# Whisperモデル設定
WHISPER_MODELS = {
    "tiny": {"size_mb": 39, "speed_factor": 10.0, "quality": "低"},
    "base": {"size_mb": 74, "speed_factor": 5.0, "quality": "中"},
    "small": {"size_mb": 244, "speed_factor": 2.5, "quality": "中高"},
    "medium": {"size_mb": 769, "speed_factor": 1.0, "quality": "高"},
    "large": {"size_mb": 1550, "speed_factor": 0.5, "quality": "最高"}
}

# デフォルトモデル選択ルール
MODEL_SELECTION_RULES = {
    "meeting": {  # 会議録音
        "keywords": ["会議", "meeting", "zoom", "teams", "録音", "ミーティング"],
        "recommended_model": "medium",
        "reason": "会議録音は背景ノイズが多いため、高精度モデル推奨"
    },
    "interview": {  # インタビュー
        "keywords": ["interview", "インタビュー", "対談", "取材"],
        "recommended_model": "small",
        "reason": "インタビューは比較的クリアな音声のため、中程度のモデルで十分"
    },
    "presentation": {  # プレゼンテーション
        "keywords": ["presentation", "プレゼン", "講演", "セミナー"],
        "recommended_model": "base",
        "reason": "一人の話者が中心のため、軽量モデルでも対応可能"
    }
}

# ファイルサイズによるモデル選択
SIZE_BASED_MODEL_SELECTION = [
    {"max_size_mb": 10, "model": "base"},
    {"max_size_mb": 50, "model": "small"},
    {"max_size_mb": 100, "model": "medium"},
    {"max_size_mb": float('inf'), "model": "medium"}  # 100MB以上
]

# エラーハンドリング設定
ERROR_HANDLING = {
    "max_retries": 3,
    "retry_delay_seconds": 5,
    "fallback_models": ["medium", "small", "base", "tiny"],  # 失敗時の代替モデル順序
    "memory_threshold_gb": 4.0,  # メモリ不足判定の閾値
    "timeout_seconds": 3600  # 1時間のタイムアウト
}

# バッチ処理最適化
BATCH_PROCESSING = {
    "enable_parallel": True,
    "max_parallel_jobs": 2,  # 同時処理数（メモリ考慮）
    "priority_order": ["audio", "text", "document", "email"],  # 処理優先順位
    "chunk_duration_seconds": 600  # 長い音声の分割単位（10分）
}

# 音声品質設定
AUDIO_QUALITY_PRESETS = {
    "high_quality": {
        "sample_rate": 16000,
        "channels": 1,
        "format": "wav"
    },
    "low_quality": {
        "sample_rate": 8000,
        "channels": 1,
        "format": "mp3"
    }
}

# 言語設定
LANGUAGE_SETTINGS = {
    "default": "ja",
    "auto_detect_keywords": {
        "ja": ["です", "ます", "ございます", "よろしく"],
        "en": ["the", "and", "is", "are", "hello"],
        "zh": ["的", "是", "在", "有", "我"],
        "ko": ["입니다", "습니다", "있습니다"]
    }
}

# キャッシュ設定
CACHE_SETTINGS = {
    "enable_cache": True,
    "cache_dir": "cache/whisper",
    "cache_expiry_days": 7,
    "max_cache_size_gb": 10
}

# 進捗表示設定
PROGRESS_SETTINGS = {
    "show_progress_bar": True,
    "update_interval_seconds": 5,
    "detailed_logging": True
}

class AudioProcessorConfig:
    """音声処理の設定管理クラス"""
    
    def __init__(self, config_overrides: Optional[Dict] = None):
        """
        初期化
        
        Args:
            config_overrides: 設定の上書き用辞書
        """
        self.config_overrides = config_overrides or {}
        
        # キャッシュディレクトリ作成
        cache_dir = Path(self.get_cache_dir())
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_recommended_model(self, file_path: Path, file_size_mb: float) -> str:
        """
        ファイルに応じた推奨モデルを取得
        
        Args:
            file_path: ファイルパス
            file_size_mb: ファイルサイズ（MB）
            
        Returns:
            推奨モデル名
        """
        filename_lower = file_path.name.lower()
        
        # キーワードベースの推奨
        for category, rules in MODEL_SELECTION_RULES.items():
            if any(keyword in filename_lower for keyword in rules["keywords"]):
                return rules["recommended_model"]
        
        # サイズベースの推奨
        for size_rule in SIZE_BASED_MODEL_SELECTION:
            if file_size_mb <= size_rule["max_size_mb"]:
                return size_rule["model"]
        
        return "medium"  # デフォルト
    
    def get_fallback_model(self, current_model: str) -> Optional[str]:
        """
        エラー時の代替モデルを取得
        
        Args:
            current_model: 現在のモデル
            
        Returns:
            代替モデル名（なければNone）
        """
        fallback_models = ERROR_HANDLING["fallback_models"]
        try:
            current_index = fallback_models.index(current_model)
            if current_index < len(fallback_models) - 1:
                return fallback_models[current_index + 1]
        except ValueError:
            return fallback_models[0]
        
        return None
    
    def should_use_chunking(self, file_size_mb: float) -> bool:
        """
        ファイルを分割処理すべきか判定
        
        Args:
            file_size_mb: ファイルサイズ（MB）
            
        Returns:
            分割処理が必要か
        """
        # 100MB以上のファイルは分割処理推奨
        return file_size_mb > 100
    
    def get_cache_dir(self) -> str:
        """キャッシュディレクトリを取得"""
        return self.config_overrides.get("cache_dir", CACHE_SETTINGS["cache_dir"])
    
    def is_cache_enabled(self) -> bool:
        """キャッシュが有効か確認"""
        return self.config_overrides.get("enable_cache", CACHE_SETTINGS["enable_cache"])
    
    def get_max_parallel_jobs(self) -> int:
        """最大並列処理数を取得"""
        # 利用可能なメモリに応じて調整
        available_memory_gb = self._get_available_memory()
        
        if available_memory_gb < 4:
            return 1
        elif available_memory_gb < 8:
            return 2
        else:
            return self.config_overrides.get(
                "max_parallel_jobs", 
                BATCH_PROCESSING["max_parallel_jobs"]
            )
    
    def _get_available_memory(self) -> float:
        """利用可能なメモリ（GB）を取得"""
        try:
            import psutil
            return psutil.virtual_memory().available / (1024 ** 3)
        except ImportError:
            # psutilがない場合はデフォルト値
            return 8.0
    
    def validate_audio_file(self, file_path: Path) -> tuple[bool, str]:
        """
        音声ファイルの妥当性をチェック
        
        Args:
            file_path: ファイルパス
            
        Returns:
            (妥当性, エラーメッセージ)
        """
        # ファイル存在チェック
        if not file_path.exists():
            return False, "ファイルが存在しません"
        
        # ファイルサイズチェック
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb == 0:
            return False, "ファイルサイズが0です"
        
        if file_size_mb > 1000:  # 1GB以上
            return False, "ファイルサイズが大きすぎます（1GB以上）"
        
        # 拡張子チェック
        valid_extensions = {'.mp3', '.wav', '.m4a', '.mp4', '.aac', '.flac', '.wma', '.ogg'}
        if file_path.suffix.lower() not in valid_extensions:
            return False, f"サポートされていない形式です: {file_path.suffix}"
        
        return True, ""
    
    def get_error_recovery_strategy(self, error_type: str) -> Dict:
        """
        エラータイプに応じた回復戦略を取得
        
        Args:
            error_type: エラーの種類
            
        Returns:
            回復戦略の辞書
        """
        strategies = {
            "memory_error": {
                "action": "use_smaller_model",
                "message": "メモリ不足のため、より小さいモデルを使用します"
            },
            "timeout_error": {
                "action": "chunk_processing",
                "message": "処理時間超過のため、ファイルを分割処理します"
            },
            "model_error": {
                "action": "fallback_model",
                "message": "モデルエラーのため、代替モデルを使用します"
            },
            "unknown_error": {
                "action": "retry",
                "message": "不明なエラーのため、再試行します"
            }
        }
        
        return strategies.get(error_type, strategies["unknown_error"])


# グローバル設定インスタンス
global_config = AudioProcessorConfig()


def get_optimal_settings(file_path: Path) -> Dict:
    """
    ファイルに最適な設定を取得
    
    Args:
        file_path: 音声ファイルパス
        
    Returns:
        最適化された設定辞書
    """
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    
    # 推奨モデル取得
    model = global_config.get_recommended_model(file_path, file_size_mb)
    
    # チャンク処理判定
    use_chunking = global_config.should_use_chunking(file_size_mb)
    
    # 並列処理数
    max_parallel = global_config.get_max_parallel_jobs()
    
    return {
        "model": model,
        "use_chunking": use_chunking,
        "chunk_duration": BATCH_PROCESSING["chunk_duration_seconds"],
        "max_parallel": max_parallel,
        "language": LANGUAGE_SETTINGS["default"],
        "enable_cache": global_config.is_cache_enabled()
    }