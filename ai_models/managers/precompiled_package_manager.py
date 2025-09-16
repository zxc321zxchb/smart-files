#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
预编译包管理器 - 处理预编译AI依赖包的下载、验证和安装
用于解决PyInstaller环境中的pip安装限制问题
"""

import os
import sys
import json
import zipfile
import hashlib
import requests
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# 尝试导入S3下载管理器
try:
    from .s3_download_manager import get_s3_download_manager
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    logger.warning("S3下载管理器不可用，将使用HTTP下载")

class PrecompiledPackageManager:
    """预编译包管理器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化预编译包管理器
        
        Args:
            base_dir: 基础目录，如果为None则使用当前目录
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = Path(base_dir)
        self.packages_dir = self.base_dir / 'data' / 'precompiled_packages'
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载预编译包配置
        self.package_config = self._load_package_config()
        
        # 初始化S3下载管理器
        self.s3_manager = None
        if S3_AVAILABLE:
            try:
                self.s3_manager = get_s3_download_manager()
                logger.info("S3下载管理器初始化成功")
            except Exception as e:
                logger.warning(f"S3下载管理器初始化失败: {e}")
                self.s3_manager = None
    
    def _get_proxy_config(self) -> Optional[Dict[str, str]]:
        """
        获取代理配置
        
        Returns:
            Dict[str, str]: 代理配置字典，如果不需要代理则返回None
        """
        try:
            # 检查环境变量中的代理设置
            http_proxy = os.environ.get('http_proxy') or os.environ.get('HTTP_PROXY')
            https_proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY')
            
            if http_proxy or https_proxy:
                proxies = {}
                if http_proxy:
                    proxies['http'] = http_proxy
                if https_proxy:
                    proxies['https'] = https_proxy
                logger.info(f"检测到代理配置: {proxies}")
                return proxies
            else:
                # 默认使用127.0.0.1:7890代理
                proxies = {
                    'http': 'http://127.0.0.1:7890',
                    'https': 'http://127.0.0.1:7890'
                }
                logger.info(f"使用默认代理配置: {proxies}")
                return proxies
                
        except Exception as e:
            logger.warning(f"代理配置获取失败: {e}")
            return None
    
    def _download_from_s3(self, package_name: str, progress_callback=None) -> bool:
        """
        从S3下载包
        
        Args:
            package_name: 包名称
            progress_callback: 进度回调函数
            
        Returns:
            bool: 下载是否成功
        """
        if not self.s3_manager:
            logger.warning("S3下载管理器不可用")
            return False
        
        try:
            package_info = self.get_package_info(package_name)
            if not package_info:
                logger.error(f"包信息不存在: {package_name}")
                return False
            
            # 构建S3对象键
            object_key = f"{package_name}_v{package_info['version']}.zip"
            package_file = self.packages_dir / f"{package_name}_v{package_info['version']}.zip"
            
            logger.info(f"从S3下载包: {object_key}")
            
            # 使用S3下载
            success = self.s3_manager.download_file(
                object_key=object_key,
                local_path=str(package_file),
                progress_callback=progress_callback
            )
            
            if success:
                logger.info(f"包 {package_name} 从S3下载完成")
                return True
            else:
                logger.error(f"包 {package_name} 从S3下载失败")
                return False
                
        except Exception as e:
            logger.error(f"S3下载包 {package_name} 出错: {e}")
            return False
    
    def _load_package_config(self) -> Dict:
        """
        加载预编译包配置
        
        Returns:
            Dict: 包配置
        """
        config_file = self.base_dir / 'ai_models' / 'config' / 'precompiled_package_config.json'
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                return config_data.get('packages', {})
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}，使用默认配置")
        
        # 默认配置（作为后备）
        return {
            'ai_dependencies': {
                'name': 'ai_dependencies',
                'version': '1.0.0',
                'description': 'AI依赖包 - 包含sentence-transformers, torch, faiss等',
                'download_urls': [
                    'https://your-cdn.com/ai_dependencies_v1.0.0.zip',
                    'https://backup-cdn.com/ai_dependencies_v1.0.0.zip'
                ],
                'file_size_mb': 500,
                'checksum': 'sha256:your_checksum_here',
                'required_files': [
                    'site-packages/sentence_transformers',
                    'site-packages/torch',
                    'site-packages/faiss',
                    'site-packages/transformers',
                    'site-packages/numpy',
                    'metadata.json'
                ]
            },
            'ai_models': {
                'name': 'ai_models',
                'version': '1.0.0',
                'description': 'AI模型包 - 包含sentence transformer模型和faiss索引',
                'download_urls': [
                    'https://your-cdn.com/ai_models_v1.0.0.zip',
                    'https://backup-cdn.com/ai_models_v1.0.0.zip'
                ],
                'file_size_mb': 100,
                'checksum': 'sha256:your_models_checksum_here',
                'required_files': [
                    'sentence-transformers/all-MiniLM-L6-v2',
                    'similarity_index/faiss_index.bin',
                    'similarity_index/metadata.json',
                    'metadata.json'
                ]
            }
        }
    
    def is_pyinstaller_environment(self) -> bool:
        """
        检测是否在PyInstaller环境中运行
        
        Returns:
            bool: True如果在PyInstaller环境中
        """
        return hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS')
    
    def get_package_info(self, package_name: str) -> Optional[Dict]:
        """
        获取包信息
        
        Args:
            package_name: 包名称
            
        Returns:
            Dict: 包信息，如果不存在则返回None
        """
        return self.package_config.get(package_name)
    
    def calculate_file_checksum(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        计算文件校验和
        
        Args:
            file_path: 文件路径
            algorithm: 校验算法
            
        Returns:
            str: 校验和
        """
        hash_func = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return f"{algorithm}:{hash_func.hexdigest()}"
    
    def verify_package_integrity(self, package_path: Path, expected_checksum: str) -> bool:
        """
        验证包完整性
        
        Args:
            package_path: 包文件路径
            expected_checksum: 期望的校验和
            
        Returns:
            bool: 验证是否通过
        """
        try:
            if not package_path.exists():
                return False
            
            # 提取算法和期望值
            algorithm, expected_hash = expected_checksum.split(':', 1)
            actual_checksum = self.calculate_file_checksum(package_path, algorithm)
            actual_hash = actual_checksum.split(':', 1)[1]
            
            return actual_hash == expected_hash
            
        except Exception as e:
            logger.error(f"验证包完整性失败: {e}")
            return False
    
    def download_package(self, package_name: str, progress_callback=None) -> bool:
        """
        下载预编译包
        
        Args:
            package_name: 包名称
            progress_callback: 进度回调函数
            
        Returns:
            bool: 下载是否成功
        """
        package_info = self.get_package_info(package_name)
        if not package_info:
            logger.error(f"未知的包名称: {package_name}")
            return False
        
        package_file = self.packages_dir / f"{package_name}_v{package_info['version']}.zip"
        
        # 检查是否已存在（跳过校验）
        if package_file.exists():
            logger.info(f"包 {package_name} 已存在，跳过下载")
            return True
        
        # 优先尝试S3下载
        if self.s3_manager:
            logger.info(f"尝试从S3下载包: {package_name}")
            if self._download_from_s3(package_name, progress_callback):
                logger.info(f"包 {package_name} 从S3下载成功")
                return True
            else:
                logger.warning(f"包 {package_name} 从S3下载失败，尝试HTTP下载")
        
        # 配置代理
        proxies = self._get_proxy_config()
        
        # 尝试多个HTTP下载地址
        for i, url in enumerate(package_info['download_urls']):
            try:
                logger.info(f"尝试下载包 {package_name} (源 {i+1}/{len(package_info['download_urls'])})")
                logger.info(f"下载地址: {url}")
                if proxies:
                    logger.info(f"使用代理: {proxies}")
                
                if progress_callback:
                    progress_callback(f"下载 {package_name}", 0)
                
                response = requests.get(url, stream=True, timeout=60, proxies=proxies)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0
                
                with open(package_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                progress_callback(f"下载 {package_name}", progress)
                
                # 下载完成（跳过校验）
                logger.info(f"包 {package_name} 下载完成")
                return True
                    
            except Exception as e:
                logger.warning(f"下载失败 (源 {i+1}): {e}")
                if package_file.exists():
                    package_file.unlink()
                if i < len(package_info['download_urls']) - 1:
                    logger.info(f"尝试下一个下载源...")
                    continue
                else:
                    raise e
        
        logger.error(f"所有下载源都失败: {package_name}")
        return False
    
    def extract_package(self, package_name: str, progress_callback=None) -> bool:
        """
        解压预编译包
        
        Args:
            package_name: 包名称
            progress_callback: 进度回调函数
            
        Returns:
            bool: 解压是否成功
        """
        package_info = self.get_package_info(package_name)
        if not package_info:
            return False
        
        package_file = self.packages_dir / f"{package_name}_v{package_info['version']}.zip"
        if not package_file.exists():
            logger.error(f"包文件不存在: {package_file}")
            return False
        
        try:
            extract_dir = self.packages_dir / f"{package_name}_extracted"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"解压包 {package_name}...")
            if progress_callback:
                progress_callback(f"解压 {package_name}", 0)
            
            with zipfile.ZipFile(package_file, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                for i, file_name in enumerate(file_list):
                    zip_ref.extract(file_name, extract_dir)
                    
                    if progress_callback:
                        progress = (i / total_files) * 100
                        progress_callback(f"解压 {package_name}", progress)
            
            logger.info(f"包 {package_name} 解压完成")
            return True
            
        except Exception as e:
            logger.error(f"解压包 {package_name} 失败: {e}")
            return False
    
    def install_ai_dependencies(self, progress_callback=None) -> bool:
        """
        安装AI依赖包（从预编译包）
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 安装是否成功
        """
        if not self.is_pyinstaller_environment():
            logger.info("非PyInstaller环境，跳过预编译包安装")
            return True
        
        logger.info("在PyInstaller环境中安装AI依赖包...")
        
        # 下载依赖包
        if not self.download_package('ai_dependencies', progress_callback):
            return False
        
        # 解压依赖包
        if not self.extract_package('ai_dependencies', progress_callback):
            return False
        
        # 安装到Python路径
        try:
            extract_dir = self.packages_dir / 'ai_dependencies_extracted'
            site_packages_dir = extract_dir / 'site-packages'
            
            if not site_packages_dir.exists():
                logger.error("解压的包中缺少site-packages目录")
                return False
            
            # 将site-packages添加到sys.path
            site_packages_path = str(site_packages_dir)
            if site_packages_path not in sys.path:
                sys.path.insert(0, site_packages_path)
                logger.info(f"已将 {site_packages_path} 添加到Python路径")
            
            # 跳过包验证，只确保文件解压成功
            logger.info("AI依赖包解压完成，跳过导入验证")
            logger.info("注意：包导入将在实际使用时进行验证")
            return True
            
        except Exception as e:
            logger.error(f"安装AI依赖包失败: {e}")
            return False
    
    def install_ai_models(self, progress_callback=None) -> bool:
        """
        安装AI模型包
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 安装是否成功
        """
        logger.info("安装AI模型包...")
        
        # 下载模型包
        if not self.download_package('ai_models', progress_callback):
            return False
        
        # 解压模型包
        if not self.extract_package('ai_models', progress_callback):
            return False
        
        # 复制模型文件到目标位置
        try:
            extract_dir = self.packages_dir / 'ai_models_extracted'
            models_dir = self.base_dir / 'data' / 'models'
            models_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制sentence transformer模型
            st_source = extract_dir / 'sentence-transformers'
            st_target = models_dir / 'sentence-transformers'
            if st_source.exists():
                if st_target.exists():
                    shutil.rmtree(st_target)
                shutil.copytree(st_source, st_target)
                logger.info("sentence transformer模型安装完成")
            
            # 复制faiss索引
            faiss_source = extract_dir / 'similarity_index'
            faiss_target = models_dir / 'similarity_index'
            if faiss_source.exists():
                if faiss_target.exists():
                    shutil.rmtree(faiss_target)
                shutil.copytree(faiss_source, faiss_target)
                logger.info("faiss索引安装完成")
            
            logger.info("AI模型包安装成功")
            return True
            
        except Exception as e:
            logger.error(f"安装AI模型包失败: {e}")
            return False
    
    def setup_ai_environment(self, progress_callback=None) -> bool:
        """
        设置完整的AI环境（安装依赖 + 模型）
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 设置是否成功
        """
        logger.info("开始设置AI环境（使用预编译包）...")
        
        # 步骤1: 安装AI依赖
        if progress_callback:
            progress_callback("安装AI依赖包", 20)
        
        if not self.install_ai_dependencies(progress_callback):
            return False
        
        # 步骤2: 安装AI模型
        if progress_callback:
            progress_callback("安装AI模型包", 60)
        
        if not self.install_ai_models(progress_callback):
            return False
        
        # 步骤3: 跳过验证，直接完成
        if progress_callback:
            progress_callback("AI环境设置完成", 100)
        
        logger.info("AI环境设置完成（跳过验证）")
        logger.info("注意：AI功能将在实际使用时进行验证和初始化")
        return True
    
    def cleanup_packages(self) -> bool:
        """
        清理预编译包文件
        
        Returns:
            bool: 清理是否成功
        """
        try:
            if self.packages_dir.exists():
                shutil.rmtree(self.packages_dir)
                self.packages_dir.mkdir(parents=True, exist_ok=True)
                logger.info("预编译包文件清理完成")
                return True
        except Exception as e:
            logger.error(f"清理预编译包文件失败: {e}")
            return False


def get_precompiled_package_manager() -> PrecompiledPackageManager:
    """获取预编译包管理器实例"""
    return PrecompiledPackageManager()


if __name__ == '__main__':
    # 测试预编译包管理器
    manager = PrecompiledPackageManager()
    
    print("=== 预编译包管理器测试 ===")
    print(f"PyInstaller环境: {manager.is_pyinstaller_environment()}")
    print(f"包目录: {manager.packages_dir}")
    
    # 测试包信息获取
    for package_name in ['ai_dependencies', 'ai_models']:
        info = manager.get_package_info(package_name)
        if info:
            print(f"\n包 {package_name}:")
            print(f"  版本: {info['version']}")
            print(f"  描述: {info['description']}")
            print(f"  大小: {info['file_size_mb']}MB")
            print(f"  下载地址: {len(info['download_urls'])}个")
