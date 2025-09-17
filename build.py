#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyInstaller自动化构建脚本
用于Django项目的单文件打包
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# 设置Windows控制台编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

class PyInstallerBuilder:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.dist_dir = self.base_dir / 'dist'
        self.build_dir = self.base_dir / 'build'
        self.spec_file = self.base_dir / 'file_save_system.spec'
        
    def clean_build(self):
        """清理之前的构建文件"""
        print("🧹 清理之前的构建文件...")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            print(f"   删除目录: {self.dist_dir}")
            
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            print(f"   删除目录: {self.build_dir}")
            
        # 删除spec文件生成的临时文件
        for file in self.base_dir.glob('*.spec'):
            if file.name != 'file_save_system.spec':
                file.unlink()
                print(f"   删除文件: {file}")
                
    def check_dependencies(self):
        """检查依赖是否安装"""
        print("🔍 检查依赖...")
        
        try:
            import PyInstaller
            print(f"   ✅ PyInstaller版本: {PyInstaller.__version__}")
        except ImportError:
            print("   ❌ PyInstaller未安装，正在安装...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller==6.3.0'], check=True)
            print("   ✅ PyInstaller安装完成")
            
        # 检查Django项目依赖
        try:
            import django
            print(f"   ✅ Django版本: {django.get_version()}")
        except ImportError:
            print("   ❌ Django未安装，请先安装项目依赖")
            return False
            
        return True
    
    def download_pandoc(self):
        """下载pandoc"""
        print("📦 准备pandoc...")
        
        try:
            # 根据操作系统选择下载方式
            if sys.platform == 'win32':
                # Windows使用批处理脚本
                result = subprocess.run(['download_pandoc_windows.bat'], 
                                      cwd=self.base_dir, check=True, capture_output=True, text=True)
            else:
                # 其他系统使用Python脚本
                result = subprocess.run([sys.executable, 'download_pandoc_simple.py'], 
                                      cwd=self.base_dir, check=True, capture_output=True, text=True)
            
            print("   ✅ pandoc准备完成")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  pandoc下载失败: {e}")
            print("   将尝试使用系统已安装的pandoc")
            return True  # 不阻止构建，允许使用系统pandoc
        except Exception as e:
            print(f"   ⚠️  pandoc准备出错: {e}")
            return True  # 不阻止构建
        
    def prepare_data_files(self):
        """准备数据文件"""
        print("📁 准备数据文件...")
        
        # 确保data目录存在
        data_dir = self.base_dir / 'data'
        if not data_dir.exists():
            data_dir.mkdir()
            print(f"   创建目录: {data_dir}")
            
        # 确保logs目录存在
        logs_dir = self.base_dir / 'logs'
        if not logs_dir.exists():
            logs_dir.mkdir()
            print(f"   创建目录: {logs_dir}")
            
        # 检查数据库文件
        db_file = data_dir / 'file_save.db'
        if not db_file.exists():
            print("   ⚠️  数据库文件不存在，将在首次运行时创建")
            
    def run_pyinstaller(self):
        """运行PyInstaller"""
        print("🔨 开始PyInstaller打包...")
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(self.spec_file)
        ]
        
        print(f"   执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.base_dir, check=True, capture_output=True, text=True)
            print("   ✅ PyInstaller打包成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ PyInstaller打包失败:")
            print(f"   错误输出: {e.stderr}")
            return False
            
    def post_build_setup(self):
        """构建后设置"""
        print("🔧 构建后设置...")
        
        exe_file = self.dist_dir / 'file_save_system'
        if sys.platform == 'win32':
            exe_file = self.dist_dir / 'file_save_system.exe'
            
        if exe_file.exists():
            print(f"   ✅ 可执行文件已生成: {exe_file}")
            
            # 创建启动脚本
            self.create_startup_script(exe_file)
            
            # 显示文件大小
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"   📊 文件大小: {size_mb:.1f} MB")
            
            return True
        else:
            print(f"   ❌ 可执行文件未找到: {exe_file}")
            return False
            
    def create_startup_script(self, exe_file):
        """创建启动脚本"""
        print("📝 创建启动脚本...")
        
        # Windows批处理文件
        if sys.platform == 'win32':
            bat_file = self.dist_dir / 'start_server.bat'
            with open(bat_file, 'w', encoding='utf-8') as f:
                f.write(f'''@echo off
echo 启动文件保存系统...
echo 访问地址: http://localhost:8000
echo 按Ctrl+C停止服务
echo.
{exe_file.name} runserver 0.0.0.0:8000
pause
''')
            print(f"   ✅ 创建启动脚本: {bat_file}")
            
        # Unix shell脚本
        else:
            sh_file = self.dist_dir / 'start_server.sh'
            with open(sh_file, 'w', encoding='utf-8') as f:
                f.write(f'''#!/bin/bash
echo "启动文件保存系统..."
echo "访问地址: http://localhost:8000"
echo "按Ctrl+C停止服务"
echo ""
./{exe_file.name} runserver 0.0.0.0:8000
''')
            # 设置执行权限
            os.chmod(sh_file, 0o755)
            print(f"   ✅ 创建启动脚本: {sh_file}")
            
    def build(self):
        """执行完整构建流程"""
        print("🚀 开始PyInstaller构建流程...")
        print(f"   项目目录: {self.base_dir}")
        print(f"   输出目录: {self.dist_dir}")
        print()
        
        # 步骤1: 清理构建文件
        self.clean_build()
        print()
        
        # 步骤2: 检查依赖
        if not self.check_dependencies():
            return False
        print()
        
        # 步骤3: 准备数据文件
        self.prepare_data_files()
        print()
        
        # 步骤4: 运行PyInstaller
        if not self.run_pyinstaller():
            return False
        print()
        
        # 步骤5: 构建后设置
        if not self.post_build_setup():
            return False
        print()
        
        print("🎉 构建完成!")
        print(f"   可执行文件位置: {self.dist_dir}")
        print("   使用方法:")
        if sys.platform == 'win32':
            print("   - 双击 start_server.bat 启动服务")
            print("   - 或直接运行 file_save_system.exe")
        else:
            print("   - 运行 ./start_server.sh 启动服务")
            print("   - 或直接运行 ./file_save_system")
        print("   - 访问 http://localhost:8000 使用系统")
        
        return True

def main():
    """主函数"""
    builder = PyInstallerBuilder()
    success = builder.build()
    
    if success:
        print("\n✅ 构建成功完成!")
        sys.exit(0)
    else:
        print("\n❌ 构建失败!")
        sys.exit(1)

if __name__ == '__main__':
    main()
