#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI模型管理器模块
包含各种模型管理器的实现
"""

from .model_manager import get_model_manager, ModelManager
from .ai_download_manager import get_download_manager, AIDownloadManager
from .s3_download_manager import get_s3_download_manager, S3DownloadManager, create_r2_download_manager
from .precompiled_package_manager import get_precompiled_package_manager, PrecompiledPackageManager

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
