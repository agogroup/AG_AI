#!/usr/bin/env python3
"""
高度な分析システム - エントリーポイント
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bin.analyze_advanced import main

if __name__ == "__main__":
    main()