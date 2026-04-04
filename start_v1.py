#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Blueclaw v1.0 - Week 15 Implementation

Usage:
    python start_v1.py                          # 使用规则引擎
    python start_v1.py --llm                    # 使用 LLM 引擎（模拟模式）
    python start_v1.py --llm --api-key xxx      # 使用真实 LLM
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    from v1.main_window import main
    main()

if __name__ == "__main__":
    main()
