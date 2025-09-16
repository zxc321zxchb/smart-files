#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型文件管理器 - 处理AI模型的下载、检查和加载
"""

import os
import sys
import json
import shutil
import requests
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ModelManager:
    """模型文件管理器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化模型管理器
        
        Args:
            base_dir: 基础目录，如果为None则使用当前目录
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = Path(base_dir)
        self.models_dir = self.base_dir / 'data' / 'models'
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 模型配置
        self.model_config = {
            'sentence_transformer': {
                'name': 'all-MiniLM-L6-v2',
                'url': 'https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main',
                'mirror_url': 'https://fastgh.discoverlife.top/https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main',
                'files': [
                    'config.json',
                    'pytorch_model.bin',
                    'sentence_bert_config.json',
                    'special_tokens_map.json',
                    'tokenizer.json',
                    'tokenizer_config.json',
                    'vocab.txt'
                ],
                'size_mb': 90  # 预估大小
            },
            'faiss_index': {
                'name': 'faiss_index',
                'files': ['faiss_index.bin', 'metadata.json'],
                'size_mb': 10  # 预估大小
            }
        }
    
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
    
    def check_ai_dependencies(self) -> bool:
        """
        检查AI依赖是否已安装（宽松检查）
        
        Returns:
            bool: True如果AI依赖可用，False否则
        """
        try:
            # 只检查基础包，不强制要求所有包都可用
            import torch
            logger.info("✅ torch 可用")
            return True
        except ImportError as e:
            logger.warning(f"⚠️ torch 不可用: {e}")
            # 即使torch不可用，也尝试继续（可能使用CPU版本）
            try:
                import faiss
                logger.info("✅ faiss 可用")
                return True
            except ImportError as e2:
                logger.warning(f"⚠️ faiss 不可用: {e2}")
                # 最后尝试sentence_transformers
                try:
                    import sentence_transformers
                    logger.info("✅ sentence_transformers 可用")
                    return True
                except ImportError as e3:
                    logger.warning(f"⚠️ sentence_transformers 不可用: {e3}")
                    logger.info("💡 将使用基础相似度算法作为后备")
                    return False
    
    def check_model_files(self) -> Dict[str, bool]:
        """
        检查模型文件是否存在
        
        Returns:
            Dict[str, bool]: 各模型文件的检查结果
        """
        results = {}
        
        # 检查sentence transformer模型
        st_model_dir = self.models_dir / 'sentence-transformers' / 'all-MiniLM-L6-v2'
        st_files_exist = all(
            (st_model_dir / file).exists() 
            for file in self.model_config['sentence_transformer']['files']
        )
        results['sentence_transformer'] = st_files_exist
        
        # 检查faiss索引
        faiss_files_exist = all(
            (self.models_dir / 'similarity_index' / file).exists()
            for file in self.model_config['faiss_index']['files']
        )
        results['faiss_index'] = faiss_files_exist
        
        return results
    
    def get_model_status(self) -> Dict[str, any]:
        """
        获取模型状态信息
        
        Returns:
            Dict: 包含模型状态、依赖状态等信息
        """
        ai_deps_available = self.check_ai_dependencies()
        model_files_status = self.check_model_files()
        
        return {
            'ai_dependencies_available': ai_deps_available,
            'model_files_status': model_files_status,
            'all_ready': ai_deps_available and all(model_files_status.values()),
            'models_dir': str(self.models_dir)
        }
    
    def download_model_file(self, model_name: str, file_name: str, 
                          progress_callback=None) -> bool:
        """
        下载单个模型文件，支持备用下载地址和代理
        
        Args:
            model_name: 模型名称
            file_name: 文件名
            progress_callback: 进度回调函数
            
        Returns:
            bool: 下载是否成功
        """
        try:
            if model_name == 'sentence_transformer':
                base_url = self.model_config['sentence_transformer']['url']
                mirror_url = self.model_config['sentence_transformer']['mirror_url']
                target_dir = self.models_dir / 'sentence-transformers' / 'all-MiniLM-L6-v2'
            else:
                logger.error(f"不支持的模型类型: {model_name}")
                return False
            
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / file_name
            
            # 尝试多个下载地址
            urls_to_try = [
                f"{base_url}/{file_name}",
                f"{mirror_url}/{file_name}"
            ]
            
            # 配置代理
            proxies = self._get_proxy_config()
            
            for i, url in enumerate(urls_to_try):
                try:
                    logger.info(f"尝试下载文件: {file_name} (源 {i+1}/{len(urls_to_try)})")
                    logger.info(f"下载地址: {url}")
                    if proxies:
                        logger.info(f"使用代理: {proxies}")
                    
                    response = requests.get(url, stream=True, timeout=30, proxies=proxies)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    with open(target_file, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                if progress_callback and total_size > 0:
                                    progress = (downloaded_size / total_size) * 100
                                    progress_callback(file_name, progress)
                    
                    logger.info(f"文件下载完成: {file_name}")
                    return True
                    
                except Exception as e:
                    logger.warning(f"下载失败 (源 {i+1}): {e}")
                    if i < len(urls_to_try) - 1:
                        logger.info(f"尝试下一个下载源...")
                        continue
                    else:
                        raise e
            
            return False
            
        except Exception as e:
            logger.error(f"所有下载源都失败 {file_name}: {e}")
            return False
    
    def download_sentence_transformer_model(self, progress_callback=None) -> bool:
        """
        下载sentence transformer模型
        
        Args:
            progress_callback: 进度回调函数，接收(file_name, progress)参数
            
        Returns:
            bool: 下载是否成功
        """
        logger.info("开始下载sentence transformer模型...")
        
        success_count = 0
        total_files = len(self.model_config['sentence_transformer']['files'])
        
        for i, file_name in enumerate(self.model_config['sentence_transformer']['files']):
            if progress_callback:
                progress_callback(f"下载 {file_name}", (i / total_files) * 100)
            
            if self.download_model_file('sentence_transformer', file_name, progress_callback):
                success_count += 1
        
        success = success_count == total_files
        if success:
            logger.info("sentence transformer模型下载完成")
        else:
            logger.error(f"模型下载不完整: {success_count}/{total_files}")
        
        return success
    
    def create_faiss_index(self, progress_callback=None) -> bool:
        """
        创建faiss索引文件（需要AI依赖）
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 创建是否成功
        """
        if not self.check_ai_dependencies():
            logger.warning("AI依赖部分不可用，将跳过faiss索引创建")
            logger.info("💡 系统将使用基础相似度算法")
            return True  # 不返回False，允许系统继续运行
        
        try:
            from file_save.similarity_service import SimilarityService
            
            logger.info("创建faiss索引...")
            if progress_callback:
                progress_callback("创建索引", 0)
            
            # 创建相似度服务实例
            similarity_service = SimilarityService()
            
            # 重新构建索引
            similarity_service.rebuild_index()
            
            if progress_callback:
                progress_callback("创建索引", 100)
            
            logger.info("faiss索引创建完成")
            return True
            
        except Exception as e:
            logger.error(f"创建faiss索引失败: {e}")
            return False
    
    def install_ai_dependencies(self, progress_callback=None) -> bool:
        """
        安装AI依赖包
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 安装是否成功
        """
        try:
            import subprocess
            import sys
            
            logger.info("开始安装AI依赖...")
            
            packages = [
                'sentence-transformers==2.7.0',
                'faiss-cpu==1.12.0',
                'torch>=2.1.0',
                'transformers==4.44.0'
            ]
            
            for i, package in enumerate(packages):
                if progress_callback:
                    progress_callback(f"安装 {package}", (i / len(packages)) * 100)
                
                logger.info(f"安装包: {package}")
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"安装失败 {package}: {result.stderr}")
                    return False
            
            logger.info("AI依赖安装完成")
            return True
            
        except Exception as e:
            logger.error(f"安装AI依赖失败: {e}")
            return False
    
    def setup_ai_environment(self, progress_callback=None) -> bool:
        """
        设置完整的AI环境（安装依赖 + 下载模型）
        
        Args:
            progress_callback: 进度回调函数
            
        Returns:
            bool: 设置是否成功
        """
        logger.info("开始设置AI环境...")
        
        # 步骤1: 安装AI依赖
        if progress_callback:
            progress_callback("安装AI依赖", 10)
        
        if not self.install_ai_dependencies(progress_callback):
            return False
        
        # 步骤2: 下载sentence transformer模型
        if progress_callback:
            progress_callback("下载模型文件", 50)
        
        if not self.download_sentence_transformer_model(progress_callback):
            return False
        
        # 步骤3: 创建faiss索引
        if progress_callback:
            progress_callback("创建索引", 90)
        
        if not self.create_faiss_index(progress_callback):
            return False
        
        if progress_callback:
            progress_callback("AI环境设置完成", 100)
        
        logger.info("AI环境设置完成")
        return True
    
    def cleanup_models(self) -> bool:
        """
        清理模型文件
        
        Returns:
            bool: 清理是否成功
        """
        try:
            if self.models_dir.exists():
                shutil.rmtree(self.models_dir)
                self.models_dir.mkdir(parents=True, exist_ok=True)
                logger.info("模型文件清理完成")
                return True
        except Exception as e:
            logger.error(f"清理模型文件失败: {e}")
            return False


def get_model_manager() -> ModelManager:
    """获取模型管理器实例"""
    return ModelManager()


if __name__ == '__main__':
    # 测试模型管理器
    manager = ModelManager()
    
    print("=== 模型状态检查 ===")
    status = manager.get_model_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    print("\n=== 检查模型文件 ===")
    model_files = manager.check_model_files()
    print(json.dumps(model_files, indent=2, ensure_ascii=False))
