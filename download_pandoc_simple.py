#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版pandoc下载脚本
直接提供下载链接，避免复杂的网络请求
"""

import os
import platform
import subprocess
from pathlib import Path

def download_pandoc_simple():
    """简化版pandoc下载"""
    print("=== 简化版Pandoc下载器 ===")
    print(f"操作系统: {platform.system()}")
    print(f"架构: {platform.machine()}")
    print()
    
    # 创建pandoc目录
    base_dir = Path(__file__).resolve().parent
    pandoc_dir = base_dir / 'pandoc'
    pandoc_dir.mkdir(exist_ok=True)
    
    # 根据操作系统提供下载链接
    system = platform.system().lower()
    
    if system == 'windows':
        print("Windows系统检测到")
        print("请手动下载pandoc并放置到pandoc目录中：")
        print("1. 访问: https://pandoc.org/installing.html")
        print("2. 下载Windows版本的pandoc")
        print("3. 解压后将pandoc.exe放置到以下目录：")
        print(f"   {pandoc_dir / 'pandoc.exe'}")
        print()
        print("或者使用以下命令下载：")
        print("curl -L -o pandoc.zip https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-windows-x86_64.zip")
        print("unzip pandoc.zip")
        print("mv pandoc-3.1.9/pandoc.exe pandoc/")
        
    elif system == 'darwin':  # macOS
        print("macOS系统检测到")
        print("请手动下载pandoc并放置到pandoc目录中：")
        print("1. 访问: https://pandoc.org/installing.html")
        print("2. 下载macOS版本的pandoc")
        print("3. 解压后将pandoc可执行文件放置到以下目录：")
        print(f"   {pandoc_dir / 'pandoc'}")
        print()
        print("或者使用以下命令下载：")
        print("curl -L -o pandoc.tar.gz https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-macOS.pkg")
        
    elif system == 'linux':
        print("Linux系统检测到")
        print("请手动下载pandoc并放置到pandoc目录中：")
        print("1. 访问: https://pandoc.org/installing.html")
        print("2. 下载Linux版本的pandoc")
        print("3. 解压后将pandoc可执行文件放置到以下目录：")
        print(f"   {pandoc_dir / 'pandoc'}")
        print()
        print("或者使用以下命令下载：")
        print("curl -L -o pandoc.tar.gz https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-linux-amd64.tar.gz")
        print("tar -xzf pandoc.tar.gz")
        print("mv pandoc-3.1.9/bin/pandoc pandoc/")
        print("chmod +x pandoc/pandoc")
    
    else:
        print(f"不支持的操作系统: {system}")
        return False
    
    # 检查是否已有pandoc文件
    if system == 'windows':
        pandoc_file = pandoc_dir / 'pandoc.exe'
    else:
        pandoc_file = pandoc_dir / 'pandoc'
    
    if pandoc_file.exists():
        print(f"\n✅ 找到pandoc文件: {pandoc_file}")
        
        # 测试pandoc是否可用
        try:
            result = subprocess.run([str(pandoc_file), '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("✅ pandoc测试成功")
                print(f"版本信息: {result.stdout.split()[1]}")
                return True
            else:
                print("❌ pandoc测试失败")
                return False
        except Exception as e:
            print(f"❌ pandoc测试失败: {e}")
            return False
    else:
        print(f"\n❌ 未找到pandoc文件: {pandoc_file}")
        print("请按照上述说明下载并放置pandoc文件")
        return False

if __name__ == '__main__':
    success = download_pandoc_simple()
    exit(0 if success else 1)
