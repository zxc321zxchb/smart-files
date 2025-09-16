#!/usr/bin/env python
"""
PyInstaller构建配置文件
用于Django项目的单文件打包
"""

import os
import sys
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# PyInstaller配置
PYINSTALLER_CONFIG = {
    'name': 'SmartFilesApp',
    'main_script': 'manage.py',
    'onefile': True,
    'console': True,
    'clean': True,
    'noconfirm': True,
    
    # 包含的包
    'packages': [
        'file_save_system',
        'file_save',
        'file_history', 
        'performance',
        'django',
        'rest_framework',
        'django_filters',
        'corsheaders',
        'drf_yasg',
        'asgiref',
        'sqlparse',
        'yaml',
        'inflection',
        'packaging',
        'pytz',
        'uritemplate'
    ],
    
    # 隐藏导入
    'hidden_imports': [
        'django.core.management',
        'django.core.management.commands',
        'django.core.management.commands.runserver',
        'django.core.management.commands.migrate',
        'django.core.management.commands.collectstatic',
        'django.db.backends.sqlite3',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'rest_framework',
        'rest_framework.renderers',
        'rest_framework.parsers',
        'rest_framework.pagination',
        'rest_framework.filters',
        'django_filters',
        'corsheaders',
        'drf_yasg',
        'drf_yasg.generators',
        'drf_yasg.views',
        'drf_yasg.utils',
        'drf_yasg.apps',
        'asgiref',
        'asgiref.sync',
        'sqlparse',
        'yaml',
        'inflection',
        'packaging',
        'pytz',
        'uritemplate'
    ],
    
    # 数据文件
    'datas': [
        (str(BASE_DIR / 'file_save_system'), 'file_save_system'),
        (str(BASE_DIR / 'file_save'), 'file_save'),
        (str(BASE_DIR / 'file_history'), 'file_history'),
        (str(BASE_DIR / 'performance'), 'performance'),
        (str(BASE_DIR / 'static'), 'static'),
        (str(BASE_DIR / 'data'), 'data'),
        (str(BASE_DIR / 'requirements.txt'), '.'),
    ],
    
    # 排除的模块
    'excludes': [
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch'
    ],
    
    # 运行时钩子
    'runtime_hooks': [],
    
    # 图标文件（如果有的话）
    'icon': None,
    
    # 版本信息
    'version': '1.0.0',
    'description': 'File Save System - Django Web Application',
    'author': 'Your Name',
    'company': 'Your Company'
}

def get_pyinstaller_command():
    """生成PyInstaller命令行"""
    cmd = ['pyinstaller']
    
    if PYINSTALLER_CONFIG['onefile']:
        cmd.append('--onefile')
    
    if PYINSTALLER_CONFIG['console']:
        cmd.append('--console')
    
    if PYINSTALLER_CONFIG['clean']:
        cmd.append('--clean')
    
    if PYINSTALLER_CONFIG['noconfirm']:
        cmd.append('--noconfirm')
    
    # 添加包
    for package in PYINSTALLER_CONFIG['packages']:
        cmd.extend(['--add-data', f'{package}:{package}'])
    
    # 添加隐藏导入
    for hidden_import in PYINSTALLER_CONFIG['hidden_imports']:
        cmd.extend(['--hidden-import', hidden_import])
    
    # 添加数据文件
    for data in PYINSTALLER_CONFIG['datas']:
        if isinstance(data, tuple):
            cmd.extend(['--add-data', f'{data[0]}:{data[1]}'])
        else:
            cmd.extend(['--add-data', data])
    
    # 排除模块
    for exclude in PYINSTALLER_CONFIG['excludes']:
        cmd.extend(['--exclude-module', exclude])
    
    # 添加主脚本
    cmd.append(PYINSTALLER_CONFIG['main_script'])
    
    return cmd

if __name__ == '__main__':
    print("PyInstaller配置已加载")
    print(f"项目目录: {BASE_DIR}")
    print(f"主脚本: {PYINSTALLER_CONFIG['main_script']}")
    print(f"输出名称: {PYINSTALLER_CONFIG['name']}")
