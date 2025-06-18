#!/usr/bin/env python3
"""
AGO Group インテリジェント業務分析システム
メインエントリーポイント - binディレクトリの実際のスクリプトを呼び出す
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bin.analyze import main

if __name__ == "__main__":
    main()