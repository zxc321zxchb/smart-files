#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI模型管理模块
包含模型下载、安装、管理的所有相关功能
"""

from .managers.model_manager import get_model_manager, ModelManager
from .managers.ai_download_manager import get_download_manager, AIDownloadManager
from .managers.s3_download_manager import get_s3_download_manager, S3DownloadManager, create_r2_download_manager
from .managers.precompiled_package_manager import get_precompiled_package_manager, PrecompiledPackageManager

__all__ = [
    'get_model_manager',
    'ModelManager',
    'get_download_manager', 
    'AIDownloadManager',
    'get_s3_download_manager',
    'S3DownloadManager',
    'create_r2_download_manager',
    'get_precompiled_package_manager',
    'PrecompiledPackageManager'
]
