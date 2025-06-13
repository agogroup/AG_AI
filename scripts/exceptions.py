class ProfilingSystemError(Exception):
    """プロファイリングシステムの基底例外クラス"""
    pass


class DataLoadError(ProfilingSystemError):
    """データ読み込みエラー"""
    pass


class DataValidationError(ProfilingSystemError):
    """データ検証エラー"""
    pass


class ProfileGenerationError(ProfilingSystemError):
    """プロファイル生成エラー"""
    pass


class WorkflowAnalysisError(ProfilingSystemError):
    """ワークフロー分析エラー"""
    pass


class OutputGenerationError(ProfilingSystemError):
    """出力生成エラー"""
    pass


class AnalysisError(ProfilingSystemError):
    """分析エラー"""
    pass