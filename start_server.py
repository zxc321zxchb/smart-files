#!/usr/bin/env python3
"""
Django DRF 服务器启动脚本
"""
import os
import sys
import django
from django.core.management import execute_from_command_line


def setup_django():
    """设置Django环境"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_save_system.settings')
    django.setup()


def start_development_server():
    """启动开发服务器"""
    print("启动Django DRF开发服务器...")
    print("服务器地址: http://localhost:8000")
    print("API文档: http://localhost:8000/swagger/")
    print("管理后台: http://localhost:8000/admin/")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    # 设置Django环境
    setup_django()
    
    try:
        execute_from_command_line(['manage.py', 'runserver', '8000'])
    except KeyboardInterrupt:
        print("\n服务器已停止")


def start_production_server():
    """启动生产服务器"""
    print("启动Django DRF生产服务器...")
    
    # 设置生产环境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_save_system.settings_prod')
    setup_django()
    
    try:
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
    except KeyboardInterrupt:
        print("\n服务器已停止")


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == 'prod':
        start_production_server()
    else:
        start_development_server()


if __name__ == "__main__":
    main()
