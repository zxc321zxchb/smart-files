# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

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
]

# 过滤存在的数据文件
import os
datas = [(src, dst) for src, dst in datas if os.path.exists(src)]

# 隐藏导入列表
hiddenimports = [
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
]

# 排除的模块
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'PIL',
    'cv2',
    'tensorflow',
    'torch',
    'jupyter',
    'notebook',
    'IPython'
]

a = Analysis(
    ['manage.py'],
    pathex=[str(BASE_DIR)],
    binaries=[],
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
    name='SmartFilesApp',
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
