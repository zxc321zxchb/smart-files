#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windows兼容的PyInstaller构建脚本
专门处理Windows编码问题
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Windows编码设置
if sys.platform == 'win32':
    # 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 尝试设置控制台编码
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass

def print_safe(text):
    """安全打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 如果无法打印unicode，使用ASCII替代
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)

class WindowsPyInstallerBuilder:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.dist_dir = self.base_dir / 'dist'
        self.build_dir = self.base_dir / 'build'
        self.spec_file = self.base_dir / 'file_save_system.spec'
        
    def clean_build(self):
        """清理之前的构建文件"""
        print_safe("清理之前的构建文件...")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print_safe(f"   删除目录: {self.dist_dir}")
            
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print_safe(f"   删除目录: {self.build_dir}")
            
    def check_dependencies(self):
        """检查依赖是否安装"""
        print_safe("检查依赖...")
        
        try:
            import PyInstaller
            print_safe(f"   PyInstaller版本: {PyInstaller.__version__}")
        except ImportError:
            print_safe("   PyInstaller未安装，正在安装...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller==6.3.0'], check=True)
            print_safe("   PyInstaller安装完成")
            
        try:
            import django
            print_safe(f"   Django版本: {django.get_version()}")
        except ImportError:
            print_safe("   Django未安装，请先安装项目依赖")
            return False
            
        return True
        
    def prepare_data_files(self):
        """准备数据文件"""
        print_safe("准备数据文件...")
        
        data_dir = self.base_dir / 'data'
        if not data_dir.exists():
            data_dir.mkdir()
            print_safe(f"   创建目录: {data_dir}")
            
        logs_dir = self.base_dir / 'logs'
        if not logs_dir.exists():
            logs_dir.mkdir()
            print_safe(f"   创建目录: {logs_dir}")
            
    def run_pyinstaller(self):
        """运行PyInstaller"""
        print_safe("开始PyInstaller打包...")
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(self.spec_file)
        ]
        
        print_safe(f"   执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.base_dir, check=True, capture_output=True, text=True, encoding='utf-8')
            print_safe("   PyInstaller打包成功")
            return True
        except subprocess.CalledProcessError as e:
            print_safe(f"   PyInstaller打包失败:")
            print_safe(f"   错误输出: {e.stderr}")
            return False
            
    def post_build_setup(self):
        """构建后设置"""
        print_safe("构建后设置...")
        
        exe_file = self.dist_dir / 'file_save_system.exe'
        
        if exe_file.exists():
            print_safe(f"   可执行文件已生成: {exe_file}")
            
            # 创建Windows启动脚本
            bat_file = self.dist_dir / 'start_server.bat'
            with open(bat_file, 'w', encoding='utf-8') as f:
                f.write('''@echo off
echo 启动文件保存系统...
echo 访问地址: http://localhost:8000
echo 按Ctrl+C停止服务
echo.
file_save_system.exe runserver 0.0.0.0:8000
pause
''')
            print_safe(f"   创建启动脚本: {bat_file}")
            
            # 显示文件大小
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print_safe(f"   文件大小: {size_mb:.1f} MB")
            
            return True
        else:
            print_safe(f"   可执行文件未找到: {exe_file}")
            return False
            
    def build(self):
        """执行完整构建流程"""
        print_safe("开始PyInstaller构建流程...")
        print_safe(f"   项目目录: {self.base_dir}")
        print_safe(f"   输出目录: {self.dist_dir}")
        print_safe("")
        
        # 步骤1: 清理构建文件
        self.clean_build()
        print_safe("")
        
        # 步骤2: 检查依赖
        if not self.check_dependencies():
            return False
        print_safe("")
        
        # 步骤3: 准备数据文件
        self.prepare_data_files()
        print_safe("")
        
        # 步骤4: 运行PyInstaller
        if not self.run_pyinstaller():
            return False
        print_safe("")
        
        # 步骤5: 构建后设置
        if not self.post_build_setup():
            return False
        print_safe("")
        
        print_safe("构建完成!")
        print_safe(f"   可执行文件位置: {self.dist_dir}")
        print_safe("   使用方法:")
        print_safe("   - 双击 start_server.bat 启动服务")
        print_safe("   - 或直接运行 file_save_system.exe")
        print_safe("   - 访问 http://localhost:8000 使用系统")
        
        return True

def main():
    """主函数"""
    builder = WindowsPyInstallerBuilder()
    success = builder.build()
    
    if success:
        print_safe("构建成功完成!")
        sys.exit(0)
    else:
        print_safe("构建失败!")
        sys.exit(1)

if __name__ == '__main__':
    main()
