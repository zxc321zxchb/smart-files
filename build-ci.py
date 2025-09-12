#!/usr/bin/env python
"""
GitHub Actions CI构建脚本
简化版本，专门用于CI环境
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """CI构建主函数"""
    print("🚀 开始CI构建...")
    
    # 检查环境
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    
    # 安装依赖
    print("📦 安装依赖...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    
    # 运行构建
    print("🔨 开始构建...")
    subprocess.run([sys.executable, 'build.py'], check=True)
    
    # 检查构建结果
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("❌ 构建失败：dist目录不存在")
        sys.exit(1)
    
    # 列出生成的文件
    print("📁 构建产物:")
    for file in dist_dir.iterdir():
        size_mb = file.stat().st_size / (1024 * 1024)
        print(f"   {file.name}: {size_mb:.1f} MB")
    
    print("✅ CI构建完成!")

if __name__ == '__main__':
    main()
