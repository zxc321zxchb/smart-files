#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitHub Actions CI构建脚本
简化版本，专门用于CI环境
"""

import os
import sys
import subprocess
from pathlib import Path

# Windows编码设置
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def print_safe(text):
    """安全打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)

def main():
    """CI构建主函数"""
    print_safe("开始CI构建...")
    
    # 检查环境
    print_safe(f"Python版本: {sys.version}")
    print_safe(f"工作目录: {os.getcwd()}")
    print_safe(f"平台: {sys.platform}")
    
    # 安装依赖
    print_safe("安装依赖...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    
    # 根据平台选择构建脚本
    if sys.platform == 'win32':
        build_script = 'build-windows.py'
    else:
        build_script = 'build.py'
    
    print_safe(f"使用构建脚本: {build_script}")
    subprocess.run([sys.executable, build_script], check=True)
    
    # 检查构建结果
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print_safe("构建失败：dist目录不存在")
        sys.exit(1)
    
    # 列出生成的文件
    print_safe("构建产物:")
    for file in dist_dir.iterdir():
        size_mb = file.stat().st_size / (1024 * 1024)
        print_safe(f"   {file.name}: {size_mb:.1f} MB")
    
    print_safe("CI构建完成!")

if __name__ == '__main__':
    main()
