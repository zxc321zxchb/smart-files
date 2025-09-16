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
    
    try:
        # 在打包环境中跳过AI检查，直接返回False
        if getattr(sys, 'frozen', False):
            print("   📦 打包环境，跳过AI功能检查")
            return False
            
        from model_manager import get_model_manager
        manager = get_model_manager()
        status = manager.get_model_status()
        
        print(f"   AI依赖可用: {'✅' if status['ai_dependencies_available'] else '❌'}")
        print(f"   模型文件状态: {status['model_files_status']}")
        print(f"   完整AI功能: {'✅' if status['all_ready'] else '❌'}")
        
        return status['all_ready']
        
    except Exception as e:
        print(f"   ⚠️  检查AI环境失败: {e}")
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
    import threading
    import time
    
    def download_worker():
        """后台下载工作线程"""
        try:
            # 在打包环境中跳过AI下载
            if getattr(sys, 'frozen', False):
                print("\n📦 打包环境，跳过AI模型下载")
                print("   💡 将使用基础相似度算法")
                return
                
            from ai_models.managers.ai_download_manager import AIDownloadManager
            downloader = AIDownloadManager()
            
            print("\n🔄 开始后台下载AI模型...")
            print("   📡 正在下载，请稍候...")
            print("   💡 下载期间您可以正常使用应用")
            print("   📋 下载进度将实时显示：")
            
            success = downloader.download_ai_environment()
            
            if success:
                print("\n✅ AI模型下载完成！")
                print("   🎉 智能相似度检测功能已启用")
                print("   🔄 正在重新加载AI服务...")
                
                # 通知相似度服务重新加载
                try:
                    from file_save.similarity_service_simple import similarity_service
                    if hasattr(similarity_service, 'reload_ai_model'):
                        similarity_service.reload_ai_model()
                        print("   ✅ AI服务重新加载成功")
                except Exception as e:
                    print(f"   ⚠️  AI服务重新加载失败: {e}")
            else:
                print("\n❌ AI模型下载失败")
                print("   💡 将继续使用基础相似度算法")
                
        except Exception as e:
            print(f"\n❌ 后台下载出错: {e}")
            print("   💡 将继续使用基础相似度算法")
    
    # 启动后台下载线程
    download_thread = threading.Thread(target=download_worker, daemon=True)
    download_thread.start()
    
    return download_thread

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
        
        # 根据命令行参数决定AI处理策略
        if args.no_ai:
            print("\n📝 已禁用AI功能，将使用基础相似度算法")
            print("   💡 如需启用AI功能，请重新启动时不使用 --no-ai 参数")
        elif not ai_ready:
            print("\n💡 提示: AI功能不可用，将使用基础相似度算法")
            
            # 自动启动AI模型下载（不再询问用户）
            print("🔄 正在自动启动AI模型下载...")
            download_thread = start_ai_download_background()
            print("   📋 下载进度将实时显示：")
            print("   💡 下载期间您可以正常使用应用")
        else:
            print("\n✅ AI功能已就绪，将使用智能相似度检测")
        
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
