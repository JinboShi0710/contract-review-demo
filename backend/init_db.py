# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""
import sys
import os

# 添加 backend 目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db


def main():
    print("正在初始化数据库...")
    init_db()
    print("数据库初始化完成。")


if __name__ == "__main__":
    main()
