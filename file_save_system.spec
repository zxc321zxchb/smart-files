# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 增加递归限制以解决PyInstaller递归错误
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

# 项目根目录
BASE_DIR = Path(SPECPATH).resolve().parent

# 数据文件列表
datas = [
    (str(BASE_DIR / 'file_save_system'), 'file_save_system'),
    (str(BASE_DIR / 'file_save'), 'file_save'),
    (str(BASE_DIR / 'file_history'), 'file_history'),
    (str(BASE_DIR / 'performance'), 'performance'),
    (str(BASE_DIR / 'static'), 'static'),
    (str(BASE_DIR / 'data'), 'data'),
    (str(BASE_DIR / 'requirements.txt'), '.'),
    (str(BASE_DIR / 'manage.py'), '.'),
    (str(BASE_DIR / 'model_manager.py'), '.'),
    (str(BASE_DIR / 'ai_models'), 'ai_models'),
]

# 添加pandoc二进制文件
import platform
import subprocess

def find_pandoc_binary():
    """查找pandoc二进制文件"""
    pandoc_paths = []
    
    # 首先检查项目目录下的pandoc
    project_pandoc_dir = BASE_DIR / 'pandoc'
    if platform.system() == 'Windows':
        project_pandoc = project_pandoc_dir / 'pandoc.exe'
    else:
        project_pandoc = project_pandoc_dir / 'pandoc'
    
    if project_pandoc.exists():
        pandoc_paths.append(str(project_pandoc))
    
    # Windows路径
    if platform.system() == 'Windows':
        # 常见的pandoc安装路径
        possible_paths = [
            r'C:\Program Files\Pandoc\pandoc.exe',
            r'C:\Program Files (x86)\Pandoc\pandoc.exe',
            r'C:\Users\{}\AppData\Local\Pandoc\pandoc.exe'.format(os.getenv('USERNAME', '')),
            r'C:\Users\{}\AppData\Local\Microsoft\WinGet\Packages\JohnMacFarlane.Pandoc_Microsoft.Winget.Source\pandoc.exe'.format(os.getenv('USERNAME', '')),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pandoc_paths.append(path)
                
        # 尝试从PATH中查找
        try:
            result = subprocess.run(['where', 'pandoc'], capture_output=True, text=True)
            if result.returncode == 0:
                pandoc_paths.extend(result.stdout.strip().split('\n'))
        except:
            pass
            
    # macOS/Linux路径
    else:
        # 常见的pandoc安装路径
        possible_paths = [
            '/usr/local/bin/pandoc',
            '/usr/bin/pandoc',
            '/opt/homebrew/bin/pandoc',
            str(Path.home() / '.local/bin/pandoc'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                pandoc_paths.append(path)
                
        # 尝试从PATH中查找
        try:
            result = subprocess.run(['which', 'pandoc'], capture_output=True, text=True)
            if result.returncode == 0:
                pandoc_paths.append(result.stdout.strip())
        except:
            pass
    
    return pandoc_paths

# 查找并添加pandoc二进制文件
pandoc_binaries = find_pandoc_binary()
if pandoc_binaries:
    # 使用第一个找到的pandoc
    pandoc_path = pandoc_binaries[0]
    print(f"找到pandoc: {pandoc_path}")
    
    # 添加到binaries列表
    binaries = [(pandoc_path, '.')]
else:
    print("警告: 未找到pandoc，文件转换功能将不可用")
    binaries = []

# 过滤存在的数据文件
import os
datas = [(src, dst) for src, dst in datas if os.path.exists(src)]

# 隐藏导入列表
hiddenimports = [
    # Django核心模块
    'django',
    'django.core',
    'django.core.management',
    'django.core.management.commands',
    'django.core.management.commands.runserver',
    'django.core.management.commands.migrate',
    'django.core.management.commands.collectstatic',
    'django.core.management.commands.check',
    'django.core.management.commands.compilemessages',
    'django.core.management.commands.createcachetable',
    'django.core.management.commands.dbshell',
    'django.core.management.commands.diffsettings',
    'django.core.management.commands.dumpdata',
    'django.core.management.commands.flush',
    'django.core.management.commands.inspectdb',
    'django.core.management.commands.loaddata',
    'django.core.management.commands.makemessages',
    'django.core.management.commands.makemigrations',
    'django.core.management.commands.optimizemigration',
    'django.core.management.commands.sendtestemail',
    'django.core.management.commands.shell',
    'django.core.management.commands.showmigrations',
    'django.core.management.commands.sqlflush',
    'django.core.management.commands.sqlmigrate',
    'django.core.management.commands.sqlsequencereset',
    'django.core.management.commands.squashmigrations',
    'django.core.management.commands.startapp',
    'django.core.management.commands.startproject',
    'django.core.management.commands.test',
    'django.core.management.commands.testserver',
    
    # Django数据库后端
    'django.db',
    'django.db.backends',
    'django.db.backends.sqlite3',
    'django.db.backends.sqlite3.base',
    'django.db.backends.sqlite3.client',
    'django.db.backends.sqlite3.creation',
    'django.db.backends.sqlite3.features',
    'django.db.backends.sqlite3.introspection',
    'django.db.backends.sqlite3.operations',
    'django.db.backends.sqlite3.schema',
    
    # Django应用模块
    'django.contrib',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Django REST Framework
    'rest_framework',
    'rest_framework.renderers',
    'rest_framework.parsers',
    'rest_framework.pagination',
    'rest_framework.filters',
    'rest_framework.views',
    'rest_framework.viewsets',
    'rest_framework.serializers',
    'rest_framework.response',
    'rest_framework.request',
    'rest_framework.permissions',
    'rest_framework.authentication',
    'rest_framework.throttling',
    'rest_framework.pagination',
    'rest_framework.filters',
    'rest_framework.decorators',
    'rest_framework.routers',
    'rest_framework.status',
    'rest_framework.exceptions',
    'rest_framework.settings',
    'rest_framework.utils',
    'rest_framework.compat',
    'rest_framework.apps',
    
    # 第三方包
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
    'uritemplate',
    
    # 项目应用
    'file_save_system',
    'file_save_system.settings',
    'file_save_system.urls',
    'file_save_system.wsgi',
    'file_save',
    'file_history',
    'performance',
    'model_manager',
    
    # 基础数据处理依赖（移除重型AI依赖）
    'numpy',
    'scikit-learn',
    'jieba',
    
    # 确保Django模板引擎正常工作
    'django.template',
    'django.template.loader',
    'django.template.context_processors',
    'django.template.backends',
    'django.template.backends.django',
    
    # 确保Django中间件正常工作
    'django.middleware',
    'django.middleware.security',
    'django.middleware.common',
    'django.middleware.csrf',
    'django.middleware.clickjacking',
    'corsheaders.middleware',
    
    # 确保Django缓存正常工作
    'django.core.cache',
    'django.core.cache.backends',
    'django.core.cache.backends.locmem',
]

# 排除的模块
excludes = [
    'tkinter',
    'matplotlib',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'tensorflow',
    'jupyter',
    'notebook',
    'IPython',
    # 排除重型AI依赖（已移除AI功能）
    # 'sentence_transformers',
    # 'torch', 
    # 'transformers',
    # 'faiss',
    # 'huggingface_hub',
    # 'tokenizers',
    # 'accelerate',
    # 'safetensors'
]

a = Analysis(
    ['start_server_fixed.py'],
    pathex=[str(BASE_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='file_save_system',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
