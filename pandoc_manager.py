#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行时Pandoc管理器
在应用启动时检查pandoc，如果没有则自动下载到data/pandoc目录
"""

import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
import ssl
import threading
import time
from pathlib import Path

class PandocManager:
    def __init__(self):
        # 获取应用根目录
        if getattr(sys, 'frozen', False):
            # 如果是打包的可执行文件
            self.app_dir = Path(sys.executable).parent
        else:
            # 如果是开发环境
            self.app_dir = Path(__file__).parent
        
        # pandoc目录
        self.pandoc_dir = self.app_dir / 'data' / 'pandoc'
        self.pandoc_dir.mkdir(parents=True, exist_ok=True)
        
        # 根据操作系统确定pandoc可执行文件名
        if platform.system() == 'Windows':
            self.pandoc_exe = 'pandoc.exe'
        else:
            self.pandoc_exe = 'pandoc'
        
        self.pandoc_path = self.pandoc_dir / self.pandoc_exe
        
        # 异步下载相关属性
        self._download_thread = None
        self._download_status = "idle"  # idle, downloading, completed, failed
        self._download_progress = 0
        self._download_error = None
    
    def check_pandoc_available(self):
        """检查pandoc是否可用"""
        # 首先检查本地pandoc
        if self.pandoc_path.exists():
            try:
                result = subprocess.run([str(self.pandoc_path), '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"✅ 找到本地pandoc: {self.pandoc_path}")
                    return str(self.pandoc_path)
            except Exception as e:
                print(f"⚠️  本地pandoc测试失败: {e}")
        
        # 检查系统PATH中的pandoc
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ 找到系统pandoc")
                return 'pandoc'
        except Exception:
            pass
        
        return None
    
    def download_pandoc(self):
        """下载pandoc到本地目录"""
        print("📦 开始下载pandoc...")
        
        # 创建SSL上下文
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 获取版本信息
        version = self.get_pandoc_version(ssl_context)
        print(f"pandoc版本: {version}")
        
        # 根据操作系统下载
        system = platform.system().lower()
        
        if system == 'windows':
            return self.download_windows_pandoc(version, ssl_context)
        elif system == 'darwin':
            return self.download_macos_pandoc(version, ssl_context)
        elif system == 'linux':
            return self.download_linux_pandoc(version, ssl_context)
        else:
            print(f"❌ 不支持的操作系统: {system}")
            return False
    
    def get_pandoc_version(self, ssl_context):
        """获取pandoc版本"""
        try:
            import json
            with urllib.request.urlopen('https://api.github.com/repos/jgm/pandoc/releases/latest', context=ssl_context) as response:
                data = json.loads(response.read().decode())
                return data['tag_name'].lstrip('v')
        except Exception as e:
            print(f"⚠️  获取版本失败: {e}")
            return "3.1.9"  # 默认版本
    
    def download_windows_pandoc(self, version, ssl_context):
        """下载Windows版本pandoc"""
        print(f"下载Windows版本pandoc {version}...")
        
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
        
        zip_path = self.pandoc_dir / f"pandoc-{version}-windows.zip"
        
        # 尝试下载
        try:
            print("尝试直接下载...")
            urllib.request.urlretrieve(url, zip_path)
            print("✅ 直接下载成功")
        except Exception as e:
            print(f"直接下载失败: {e}")
            try:
                print("尝试代理下载...")
                urllib.request.urlretrieve(proxy_url, zip_path)
                print("✅ 代理下载成功")
            except Exception as e2:
                print(f"❌ 代理下载失败: {e2}")
                return False
        
        # 解压文件
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.pandoc_dir)
            
            # 查找pandoc.exe
            for root, dirs, files in os.walk(self.pandoc_dir):
                if 'pandoc.exe' in files:
                    pandoc_exe_path = os.path.join(root, 'pandoc.exe')
                    # 移动到目标位置
                    if pandoc_exe_path != str(self.pandoc_path):
                        if self.pandoc_path.exists():
                            self.pandoc_path.unlink()
                        os.rename(pandoc_exe_path, self.pandoc_path)
                    break
            
            # 清理zip文件
            zip_path.unlink()
            
            # 测试pandoc
            result = subprocess.run([str(self.pandoc_path), '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ pandoc下载并安装成功: {self.pandoc_path}")
                return True
            else:
                print("❌ pandoc测试失败")
                return False
                
        except Exception as e:
            print(f"❌ 解压失败: {e}")
            return False
    
    def download_windows_pandoc_with_progress(self, version, ssl_context):
        """下载Windows版本pandoc（带进度条）"""
        print(f"   📦 下载Windows版本pandoc {version}...")
        self._download_progress = 20
        
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-windows-x86_64.zip"
        
        zip_path = self.pandoc_dir / f"pandoc-{version}-windows.zip"
        
        # 尝试下载
        try:
            print("   🌐 尝试直接下载...")
            self._download_progress = 25
            urllib.request.urlretrieve(url, zip_path)
            print("   ✅ 直接下载成功")
            self._download_progress = 50
        except Exception as e:
            print(f"   ⚠️  直接下载失败: {e}")
            try:
                print("   🌐 尝试代理下载...")
                self._download_progress = 30
                urllib.request.urlretrieve(proxy_url, zip_path)
                print("   ✅ 代理下载成功")
                self._download_progress = 50
            except Exception as e2:
                print(f"   ❌ 代理下载失败: {e2}")
                return False
        
        # 解压文件
        try:
            print("   📂 正在解压文件...")
            self._download_progress = 60
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.pandoc_dir)
            
            print("   🔍 正在查找pandoc.exe...")
            self._download_progress = 70
            # 查找pandoc.exe
            for root, dirs, files in os.walk(self.pandoc_dir):
                if 'pandoc.exe' in files:
                    pandoc_exe_path = os.path.join(root, 'pandoc.exe')
                    # 移动到目标位置
                    if pandoc_exe_path != str(self.pandoc_path):
                        if self.pandoc_path.exists():
                            self.pandoc_path.unlink()
                        os.rename(pandoc_exe_path, self.pandoc_path)
                    break
            
            print("   🗑️  清理临时文件...")
            self._download_progress = 80
            # 清理zip文件
            zip_path.unlink()
            
            print("   🧪 测试pandoc功能...")
            self._download_progress = 90
            # 测试pandoc
            result = subprocess.run([str(self.pandoc_path), '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   ✅ pandoc安装成功: {self.pandoc_path}")
                return True
            else:
                print("   ❌ pandoc测试失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 解压失败: {e}")
            return False
    
    def download_macos_pandoc(self, version, ssl_context):
        """下载macOS版本pandoc"""
        print(f"下载macOS版本pandoc {version}...")
        
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-macOS.pkg"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-macOS.pkg"
        
        pkg_path = self.pandoc_dir / f"pandoc-{version}-macOS.pkg"
        
        try:
            print("尝试直接下载...")
            urllib.request.urlretrieve(url, pkg_path)
            print("✅ 下载成功")
        except Exception as e:
            print(f"直接下载失败: {e}")
            try:
                print("尝试代理下载...")
                urllib.request.urlretrieve(proxy_url, pkg_path)
                print("✅ 代理下载成功")
            except Exception as e2:
                print(f"❌ 代理下载失败: {e2}")
                return False
        
        print("⚠️  macOS版本需要手动安装pkg文件")
        print(f"请运行: sudo installer -pkg {pkg_path} -target /")
        return False
    
    def download_macos_pandoc_with_progress(self, version, ssl_context):
        """下载macOS版本pandoc（带进度条）"""
        print(f"   📦 下载macOS版本pandoc {version}...")
        self._download_progress = 20
        
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-macOS.pkg"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-macOS.pkg"
        
        pkg_path = self.pandoc_dir / f"pandoc-{version}-macOS.pkg"
        
        try:
            print("   🌐 尝试直接下载...")
            self._download_progress = 25
            urllib.request.urlretrieve(url, pkg_path)
            print("   ✅ 直接下载成功")
            self._download_progress = 50
        except Exception as e:
            print(f"   ⚠️  直接下载失败: {e}")
            try:
                print("   🌐 尝试代理下载...")
                self._download_progress = 30
                urllib.request.urlretrieve(proxy_url, pkg_path)
                print("   ✅ 代理下载成功")
                self._download_progress = 50
            except Exception as e2:
                print(f"   ❌ 代理下载失败: {e2}")
                return False
        
        print("   ⚠️  macOS版本需要手动安装pkg文件")
        print(f"   💡 请运行: sudo installer -pkg {pkg_path} -target /")
        print("   📋 安装完成后pandoc功能将自动可用")
        return False
    
    def download_linux_pandoc(self, version, ssl_context):
        """下载Linux版本pandoc"""
        print(f"下载Linux版本pandoc {version}...")
        
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-linux-amd64.tar.gz"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-linux-amd64.tar.gz"
        
        tar_path = self.pandoc_dir / f"pandoc-{version}-linux.tar.gz"
        
        try:
            print("尝试直接下载...")
            urllib.request.urlretrieve(url, tar_path)
            print("✅ 直接下载成功")
        except Exception as e:
            print(f"直接下载失败: {e}")
            try:
                print("尝试代理下载...")
                urllib.request.urlretrieve(proxy_url, tar_path)
                print("✅ 代理下载成功")
            except Exception as e2:
                print(f"❌ 代理下载失败: {e2}")
                return False
        
        # 解压文件
        try:
            with tarfile.open(tar_path, 'r:gz') as tar_ref:
                tar_ref.extractall(self.pandoc_dir)
            
            # 查找pandoc可执行文件
            for root, dirs, files in os.walk(self.pandoc_dir):
                if 'pandoc' in files and os.access(os.path.join(root, 'pandoc'), os.X_OK):
                    pandoc_bin_path = os.path.join(root, 'pandoc')
                    # 移动到目标位置
                    if pandoc_bin_path != str(self.pandoc_path):
                        if self.pandoc_path.exists():
                            self.pandoc_path.unlink()
                        os.rename(pandoc_bin_path, self.pandoc_path)
                    # 设置执行权限
                    os.chmod(self.pandoc_path, 0o755)
                    break
            
            # 清理tar文件
            tar_path.unlink()
            
            # 测试pandoc
            result = subprocess.run([str(self.pandoc_path), '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ pandoc下载并安装成功: {self.pandoc_path}")
                return True
            else:
                print("❌ pandoc测试失败")
                return False
                
        except Exception as e:
            print(f"❌ 解压失败: {e}")
            return False
    
    def download_linux_pandoc_with_progress(self, version, ssl_context):
        """下载Linux版本pandoc（带进度条）"""
        print(f"   📦 下载Linux版本pandoc {version}...")
        self._download_progress = 20
        
        url = f"https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-linux-amd64.tar.gz"
        proxy_url = f"https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/{version}/pandoc-{version}-linux-amd64.tar.gz"
        
        tar_path = self.pandoc_dir / f"pandoc-{version}-linux.tar.gz"
        
        try:
            print("   🌐 尝试直接下载...")
            self._download_progress = 25
            urllib.request.urlretrieve(url, tar_path)
            print("   ✅ 直接下载成功")
            self._download_progress = 50
        except Exception as e:
            print(f"   ⚠️  直接下载失败: {e}")
            try:
                print("   🌐 尝试代理下载...")
                self._download_progress = 30
                urllib.request.urlretrieve(proxy_url, tar_path)
                print("   ✅ 代理下载成功")
                self._download_progress = 50
            except Exception as e2:
                print(f"   ❌ 代理下载失败: {e2}")
                return False
        
        # 解压文件
        try:
            print("   📂 正在解压文件...")
            self._download_progress = 60
            with tarfile.open(tar_path, 'r:gz') as tar_ref:
                tar_ref.extractall(self.pandoc_dir)
            
            print("   🔍 正在查找pandoc可执行文件...")
            self._download_progress = 70
            # 查找pandoc可执行文件
            for root, dirs, files in os.walk(self.pandoc_dir):
                if 'pandoc' in files and os.access(os.path.join(root, 'pandoc'), os.X_OK):
                    pandoc_bin_path = os.path.join(root, 'pandoc')
                    # 移动到目标位置
                    if pandoc_bin_path != str(self.pandoc_path):
                        if self.pandoc_path.exists():
                            self.pandoc_path.unlink()
                        os.rename(pandoc_bin_path, self.pandoc_path)
                    # 设置执行权限
                    os.chmod(self.pandoc_path, 0o755)
                    break
            
            print("   🗑️  清理临时文件...")
            self._download_progress = 80
            # 清理tar文件
            tar_path.unlink()
            
            print("   🧪 测试pandoc功能...")
            self._download_progress = 90
            # 测试pandoc
            result = subprocess.run([str(self.pandoc_path), '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   ✅ pandoc安装成功: {self.pandoc_path}")
                return True
            else:
                print("   ❌ pandoc测试失败")
                return False
                
        except Exception as e:
            print(f"   ❌ 解压失败: {e}")
            return False
    
    def ensure_pandoc(self):
        """确保pandoc可用，如果不可用则异步下载"""
        print("🔍 检查pandoc...")
        
        # 检查是否已有pandoc
        pandoc_path = self.check_pandoc_available()
        if pandoc_path:
            return pandoc_path
        
        # 如果没有pandoc，启动异步下载
        print("pandoc不可用，启动后台下载...")
        self.start_async_download()
        return None  # 立即返回，不阻塞启动
    
    def start_async_download(self):
        """启动异步下载pandoc"""
        if self._download_status in ["downloading", "completed"]:
            return
        
        self._download_status = "downloading"
        self._download_progress = 0
        self._download_error = None
        
        def download_worker():
            """后台下载工作线程"""
            try:
                print("🔄 开始后台下载pandoc...")
                print("   📡 正在获取pandoc版本信息...")
                self._download_progress = 5
                
                # 获取版本信息
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                version = self.get_pandoc_version(ssl_context)
                print(f"   📋 pandoc版本: {version}")
                self._download_progress = 10
                
                # 根据操作系统下载
                system = platform.system().lower()
                print(f"   🖥️  检测到操作系统: {system}")
                self._download_progress = 15
                
                if system == 'windows':
                    print("   📦 开始下载Windows版本pandoc...")
                    success = self.download_windows_pandoc_with_progress(version, ssl_context)
                elif system == 'darwin':
                    print("   📦 开始下载macOS版本pandoc...")
                    success = self.download_macos_pandoc_with_progress(version, ssl_context)
                elif system == 'linux':
                    print("   📦 开始下载Linux版本pandoc...")
                    success = self.download_linux_pandoc_with_progress(version, ssl_context)
                else:
                    print(f"   ❌ 不支持的操作系统: {system}")
                    success = False
                
                if success:
                    self._download_status = "completed"
                    self._download_progress = 100
                    print("   ✅ pandoc下载并安装完成！")
                    print("   🎉 文件转换功能现已可用")
                else:
                    self._download_status = "failed"
                    self._download_error = "下载失败"
                    print("   ❌ pandoc下载失败")
                    
            except Exception as e:
                self._download_status = "failed"
                self._download_error = str(e)
                print(f"   ❌ pandoc下载出错: {e}")
        
        # 启动下载线程
        self._download_thread = threading.Thread(target=download_worker, daemon=True)
        self._download_thread.start()
    
    def get_download_status(self):
        """获取下载状态"""
        return {
            "status": self._download_status,
            "progress": self._download_progress,
            "error": self._download_error,
            "pandoc_available": self.check_pandoc_available() is not None
        }
    
    def wait_for_download(self, timeout=300):
        """等待下载完成（可选）"""
        if self._download_thread and self._download_thread.is_alive():
            self._download_thread.join(timeout=timeout)
        return self._download_status == "completed"

def get_pandoc_path():
    """获取pandoc路径的全局函数"""
    manager = PandocManager()
    return manager.ensure_pandoc()

if __name__ == '__main__':
    manager = PandocManager()
    pandoc_path = manager.ensure_pandoc()
    if pandoc_path:
        print(f"✅ pandoc路径: {pandoc_path}")
    else:
        print("❌ pandoc不可用")
