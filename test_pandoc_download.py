#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试pandoc下载功能
包括直接下载和代理下载
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from download_pandoc import PandocDownloader

def test_version_check():
    """测试版本检查功能"""
    print("=== 测试版本检查 ===")
    downloader = PandocDownloader()
    
    try:
        version = downloader.get_pandoc_version()
        print(f"✅ 获取到pandoc版本: {version}")
        return True
    except Exception as e:
        print(f"❌ 版本检查失败: {e}")
        return False

def test_system_pandoc():
    """测试系统pandoc检测"""
    print("\n=== 测试系统pandoc检测 ===")
    downloader = PandocDownloader()
    
    try:
        has_pandoc = downloader.check_system_pandoc()
        if has_pandoc:
            print("✅ 系统已安装pandoc")
        else:
            print("ℹ️  系统未安装pandoc")
        return True
    except Exception as e:
        print(f"❌ 系统pandoc检测失败: {e}")
        return False

def test_download():
    """测试下载功能"""
    print("\n=== 测试下载功能 ===")
    downloader = PandocDownloader()
    
    try:
        success = downloader.download_pandoc()
        if success:
            print("✅ pandoc下载成功")
            
            # 测试pandoc路径
            pandoc_path = downloader.get_pandoc_path()
            if pandoc_path:
                print(f"✅ pandoc路径: {pandoc_path}")
            else:
                print("⚠️  未找到pandoc路径")
        else:
            print("❌ pandoc下载失败")
        return success
    except Exception as e:
        print(f"❌ 下载测试失败: {e}")
        return False

def test_proxy_download():
    """测试代理下载功能"""
    print("\n=== 测试代理下载功能 ===")
    
    import urllib.request
    import platform
    
    # 测试代理连接
    proxy_url = "https://fastgh.discoverlife.top/https://api.github.com/repos/jgm/pandoc/releases/latest"
    
    try:
        print("测试代理连接...")
        with urllib.request.urlopen(proxy_url, timeout=10) as response:
            data = response.read()
            print(f"✅ 代理连接成功，响应大小: {len(data)} bytes")
            return True
    except Exception as e:
        print(f"❌ 代理连接失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试pandoc下载功能...")
    print(f"操作系统: {platform.system()}")
    print(f"Python版本: {sys.version}")
    print()
    
    tests = [
        ("版本检查", test_version_check),
        ("系统pandoc检测", test_system_pandoc),
        ("代理连接测试", test_proxy_download),
        ("下载功能", test_download),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("📊 测试结果汇总:")
    print("="*50)
    
    success_count = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(results)} 个测试通过")
    
    if success_count == len(results):
        print("🎉 所有测试通过！")
        return True
    else:
        print("⚠️  部分测试失败，请检查网络连接和配置")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
