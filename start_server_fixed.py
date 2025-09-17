#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复PyInstaller打包Django应用启动问题的启动脚本
"""

import os
import sys
import django
import argparse
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application

def setup_django():
    """设置Django环境"""
    # 处理PyInstaller打包后的路径问题
    if getattr(sys, 'frozen', False):
        # PyInstaller打包后的路径处理
        base_path = sys._MEIPASS
        # 将项目根目录添加到Python路径
        if base_path not in sys.path:
            sys.path.insert(0, base_path)
        print(f"🔧 设置打包环境路径: {base_path}")
    else:
        # 开发环境路径处理
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        print(f"🔧 设置开发环境路径: {current_dir}")
    
    # 初始化pandoc管理器（异步）
    try:
        from pandoc_manager import PandocManager
        manager = PandocManager()
        pandoc_path = manager.ensure_pandoc()
        if pandoc_path:
            print(f"✅ pandoc已准备就绪: {pandoc_path}")
        else:
            print("🔄 pandoc正在后台下载，文件转换功能稍后可用")
            print("   📊 下载进度将实时显示在控制台")
            print("   💡 下载完成后将自动启用pandoc功能")
            print("   🌐 您可以通过API /api/files/pandoc_status/ 查看下载状态")
    except Exception as e:
        print(f"⚠️  pandoc管理器初始化失败: {e}")
        print("   💡 文件转换功能将受限")
    
    # 设置Django设置模块
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_save_system.settings')
    
    # 初始化Django
    django.setup()

def create_database_tables():
    """自动创建数据库表"""
    print("🗄️  检查数据库表...")
    
    try:
        from django.core.management import execute_from_command_line
        
        # 使用migrate命令自动创建表（如果不存在）
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb', '--noinput'])
        print("✅ 数据库表检查完成")
        
    except Exception as e:
        print(f"⚠️  数据库表创建警告: {e}")
        # 继续启动，不因为表创建问题而停止

def check_ai_environment():
    """检查AI环境状态"""
    print("🤖 检查AI环境状态...")
    
    # AI功能已禁用，直接返回False
    print("   💡 提示: AI功能不可用，将使用基础相似度算法")
    return False

def ask_user_for_ai_download():
    """询问用户是否下载AI模型"""
    print("\n" + "="*60)
    print("🚀 AI功能设置向导")
    print("="*60)
    print("💡 检测到AI功能未启用，您可以：")
    print("   1. 下载AI模型，享受智能相似度检测 (推荐)")
    print("   2. 继续使用基础相似度算法")
    print()
    print("📋 AI功能优势：")
    print("   • 更准确的文档相似度检测")
    print("   • 支持语义理解和智能匹配")
    print("   • 提升文件管理和搜索体验")
    print()
    print("⚠️  注意：AI模型约90MB，需要网络连接")
    print("="*60)
    
    while True:
        try:
            choice = input("\n是否下载AI模型？(y/n): ").strip().lower()
            if choice in ['y', 'yes', '是', '1']:
                return True
            elif choice in ['n', 'no', '否', '2']:
                return False
            else:
                print("请输入 y 或 n")
        except KeyboardInterrupt:
            print("\n\n❌ 用户取消操作")
            return False

def start_ai_download_background():
    """在后台启动AI模型下载"""
    # AI功能已禁用，直接返回None
    print("   💡 将继续使用基础相似度算法")
    return None

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='智能文件保存系统')
    parser.add_argument('--no-ai', '--aiflag=false', action='store_true', 
                       help='禁用AI功能，使用基础相似度算法')
    parser.add_argument('--port', type=int, default=8000,
                       help='服务器端口 (默认: 8000)')
    parser.add_argument('--host', default='0.0.0.0',
                       help='服务器主机 (默认: 0.0.0.0)')
    return parser.parse_args()

def start_server():
    """启动Django开发服务器"""
    # 解析命令行参数
    args = parse_arguments()
    
    print("🚀 启动文件保存系统...")
    print(f"📡 访问地址: http://{args.host}:{args.port}")
    print("⏹️  按Ctrl+C停止服务")
    print()
    
    try:
        # 设置Django环境
        setup_django()
        
        # 检查AI环境
        ai_ready = check_ai_environment()
        
        # AI功能已禁用，始终使用基础相似度算法
        print("\n📝 AI功能已禁用，将使用基础相似度算法")
        print("   💡 系统将使用轻量级相似度检测算法")
        
        # 自动创建数据库表
        create_database_tables()
        
        # 使用Django的runserver命令，但禁用自动重载
        from django.core.management import execute_from_command_line
        
        # 设置环境变量禁用自动重载
        os.environ['DJANGO_AUTO_RELOAD'] = '0'
        
        print("\n🌐 启动Web服务器...")
        # 执行runserver命令，禁用自动重载
        execute_from_command_line(['manage.py', 'runserver', f'{args.host}:{args.port}', '--noreload'])
        
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    start_server()
