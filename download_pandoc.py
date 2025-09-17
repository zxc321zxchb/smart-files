#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动下载pandoc二进制文件的脚本
用于在打包前确保pandoc可用
"""

import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path

class PandocDownloader:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.pandoc_dir = self.base_dir / 'pandoc'
        self.pandoc_dir.mkdir(exist_ok=True)
        
    def get_pandoc_version(self):
        """获取最新的pandoc版本"""
        try:
            import json
            # 尝试直接访问GitHub API
            with urllib.request.urlopen('https://api.github.com/repos/jgm/pandoc/releases/latest') as response:
                data = json.loads(response.read().decode())
                return data['tag_name'].lstrip('v')
        except Exception as e:
            print(f"直接获取pandoc版本失败: {e}")
            try:
                # 使用代理获取
                proxy_url = 'https://fastgh.discoverlife.top/https://api.github.com/repos/jgm/pandoc/releases/latest'
                with urllib.request.urlopen(proxy_url) as response:
                    data = json.loads(response.read().decode())
                    return data['tag_name'].lstrip('v')
            except Exception as e2:
                print(f"代理获取pandoc版本失败: {e2}")
                return "3.1.9"  # 默认版本
    
    def download_windows_pandoc(self, version):
        """下载Windows版本的pandoc"""
        print(f"下载Windows版本的pandoc {version}...")
        
        # 构建下载URL
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
        
        # 下载文件
        zip_path = self.pandoc_dir / f"pandoc-{version}-windows.zip"
        
        # 首先尝试直接下载
        try:
            print("尝试直接下载...")
            urllib.request.urlretrieve(url, zip_path)
            print(f"直接下载完成: {zip_path}")
        except Exception as e:
            print(f"直接下载失败: {e}")
            try:
                print("尝试使用代理下载...")
                urllib.request.urlretrieve(proxy_url, zip_path)
                print(f"代理下载完成: {zip_path}")
            except Exception as e2:
                print(f"代理下载也失败: {e2}")
                return None
        
        try:
            # 解压文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.pandoc_dir)
            
            # 查找pandoc.exe
            pandoc_exe = None
            for root, dirs, files in os.walk(self.pandoc_dir):
                if 'pandoc.exe' in files:
                    pandoc_exe = os.path.join(root, 'pandoc.exe')
                    break
            
            if pandoc_exe:
                # 移动到pandoc目录
                target_path = self.pandoc_dir / 'pandoc.exe'
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(pandoc_exe, target_path)
                print(f"pandoc.exe已保存到: {target_path}")
                return str(target_path)
            else:
                print("未找到pandoc.exe")
                return None
                
        except Exception as e:
            print(f"解压Windows pandoc失败: {e}")
            return None
    
    def download_macos_pandoc(self, version):
        """下载macOS版本的pandoc"""
        print(f"下载macOS版本的pandoc {version}...")
        
        # 构建下载URL
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-macOS.pkg"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-macOS.pkg"
        
        # 下载文件
        pkg_path = self.pandoc_dir / f"pandoc-{version}-macOS.pkg"
        
        # 首先尝试直接下载
        try:
            print("尝试直接下载...")
            urllib.request.urlretrieve(url, pkg_path)
            print(f"直接下载完成: {pkg_path}")
        except Exception as e:
            print(f"直接下载失败: {e}")
            try:
                print("尝试使用代理下载...")
                urllib.request.urlretrieve(proxy_url, pkg_path)
                print(f"代理下载完成: {pkg_path}")
            except Exception as e2:
                print(f"代理下载也失败: {e2}")
                return None
        
        print("请手动安装pandoc.pkg文件")
        return str(pkg_path)
    
    def download_linux_pandoc(self, version):
        """下载Linux版本的pandoc"""
        print(f"下载Linux版本的pandoc {version}...")
        
        # 构建下载URL
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-linux-amd64.tar.gz"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-linux-amd64.tar.gz"
        
        # 下载文件
        tar_path = self.pandoc_dir / f"pandoc-{version}-linux.tar.gz"
        
        # 首先尝试直接下载
        try:
            print("尝试直接下载...")
            urllib.request.urlretrieve(url, tar_path)
            print(f"直接下载完成: {tar_path}")
        except Exception as e:
            print(f"直接下载失败: {e}")
            try:
                print("尝试使用代理下载...")
                urllib.request.urlretrieve(proxy_url, tar_path)
                print(f"代理下载完成: {tar_path}")
            except Exception as e2:
                print(f"代理下载也失败: {e2}")
                return None
        
        try:
            # 解压文件
            with tarfile.open(tar_path, 'r:gz') as tar_ref:
                tar_ref.extractall(self.pandoc_dir)
            
            # 查找pandoc可执行文件
            pandoc_bin = None
            for root, dirs, files in os.walk(self.pandoc_dir):
                if 'pandoc' in files and os.access(os.path.join(root, 'pandoc'), os.X_OK):
                    pandoc_bin = os.path.join(root, 'pandoc')
                    break
            
            if pandoc_bin:
                # 移动到pandoc目录
                target_path = self.pandoc_dir / 'pandoc'
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(pandoc_bin, target_path)
                # 设置执行权限
                os.chmod(target_path, 0o755)
                print(f"pandoc已保存到: {target_path}")
                return str(target_path)
            else:
                print("未找到pandoc可执行文件")
                return None
                
        except Exception as e:
            print(f"解压Linux pandoc失败: {e}")
            return None
    
    def check_system_pandoc(self):
        """检查系统是否已安装pandoc"""
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print("系统已安装pandoc")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return False
    
    def download_pandoc(self):
        """下载pandoc"""
        print("开始下载pandoc...")
        
        # 首先检查系统是否已安装pandoc
        if self.check_system_pandoc():
            print("系统已安装pandoc，无需下载")
            return True
        
        # 获取版本
        version = self.get_pandoc_version()
        print(f"pandoc版本: {version}")
        
        # 根据操作系统下载对应版本
        system = platform.system().lower()
        
        if system == 'windows':
            pandoc_path = self.download_windows_pandoc(version)
        elif system == 'darwin':  # macOS
            pandoc_path = self.download_macos_pandoc(version)
        elif system == 'linux':
            pandoc_path = self.download_linux_pandoc(version)
        else:
            print(f"不支持的操作系统: {system}")
            return False
        
        if pandoc_path and os.path.exists(pandoc_path):
            print(f"pandoc下载成功: {pandoc_path}")
            return True
        else:
            print("pandoc下载失败")
            return False
    
    def get_pandoc_path(self):
        """获取pandoc路径"""
        system = platform.system().lower()
        
        if system == 'windows':
            pandoc_path = self.pandoc_dir / 'pandoc.exe'
        else:
            pandoc_path = self.pandoc_dir / 'pandoc'
        
        if pandoc_path.exists():
            return str(pandoc_path)
        
        # 如果本地没有，检查系统PATH
        if self.check_system_pandoc():
            return 'pandoc'
        
        return None

def main():
    """主函数"""
    downloader = PandocDownloader()
    
    print("=== Pandoc下载器 ===")
    print(f"操作系统: {platform.system()}")
    print(f"架构: {platform.machine()}")
    print()
    
    success = downloader.download_pandoc()
    
    if success:
        pandoc_path = downloader.get_pandoc_path()
        if pandoc_path:
            print(f"\n✅ pandoc准备完成: {pandoc_path}")
            
            # 测试pandoc是否可用
            try:
                result = subprocess.run([pandoc_path, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print("✅ pandoc测试成功")
                    print(f"版本信息: {result.stdout.split()[1]}")
                else:
                    print("❌ pandoc测试失败")
            except Exception as e:
                print(f"❌ pandoc测试失败: {e}")
        else:
            print("❌ 未找到pandoc")
            return False
    else:
        print("❌ pandoc下载失败")
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
