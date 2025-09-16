#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI下载管理器 - 管理AI模型的下载、安装和状态监控
"""

import os
import sys
import time
import threading
import logging
from typing import Dict, Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AIDownloadManager:
    """AI下载管理器"""
    
    def __init__(self):
        self.download_status = {
            'is_downloading': False,
            'progress': 0,
            'current_step': '',
            'error': None,
            'completed': False
        }
        self.callbacks = []
        self.download_thread = None
    
    def _setup_proxy_environment(self):
        """设置代理环境变量"""
        try:
            # 设置代理环境变量
            os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
            os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
            os.environ['http_proxy'] = 'http://127.0.0.1:7890'
            os.environ['https_proxy'] = 'http://127.0.0.1:7890'
            
            logger.info("代理环境变量设置完成: 127.0.0.1:7890")
        except Exception as e:
            logger.warning(f"代理环境变量设置失败: {e}")
    
    def add_progress_callback(self, callback: Callable[[Dict], None]):
        """添加进度回调函数"""
        self.callbacks.append(callback)
    
    def _notify_progress(self, status_update: Dict):
        """通知进度更新"""
        self.download_status.update(status_update)
        
        # 直接打印进度信息到控制台
        progress = status_update.get('progress', 0)
        current_step = status_update.get('current_step', '')
        error = status_update.get('error')
        
        if error:
            print(f"\n❌ 错误: {error}")
        elif current_step:
            # 创建进度条
            bar_length = 30
            filled_length = int(bar_length * progress / 100)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            print(f"\r🔄 [{bar}] {progress:5.1f}% {current_step}", end='', flush=True)
            
            if status_update.get('completed', False):
                print()  # 换行
        
        # 调用回调函数
        for callback in self.callbacks:
            try:
                callback(self.download_status.copy())
            except Exception as e:
                logger.error(f"进度回调出错: {e}")
    
    def download_ai_environment(self) -> bool:
        """下载完整的AI环境"""
        try:
            self._notify_progress({
                'is_downloading': True,
                'progress': 0,
                'current_step': '开始下载AI环境',
                'error': None,
                'completed': False
            })
            
            # 步骤1: 安装AI依赖
            self._notify_progress({
                'progress': 10,
                'current_step': '安装AI依赖包...'
            })
            
            if not self._install_ai_dependencies():
                return False
            
            # 步骤2: 下载sentence transformer模型
            self._notify_progress({
                'progress': 30,
                'current_step': '下载sentence transformer模型...'
            })
            
            if not self._download_sentence_transformer_model():
                return False
            
            # 步骤3: 创建faiss索引
            self._notify_progress({
                'progress': 80,
                'current_step': '创建faiss索引...'
            })
            
            if not self._create_faiss_index():
                return False
            
            # 完成
            self._notify_progress({
                'progress': 100,
                'current_step': 'AI环境设置完成',
                'completed': True
            })
            
            return True
            
        except Exception as e:
            logger.error(f"下载AI环境失败: {e}")
            self._notify_progress({
                'error': str(e),
                'is_downloading': False
            })
            return False
        finally:
            self._notify_progress({
                'is_downloading': False
            })
    
    def _install_ai_dependencies(self) -> bool:
        """安装AI依赖包"""
        try:
            # 检测是否在PyInstaller环境中
            is_pyinstaller = hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS')
            
            if is_pyinstaller:
                # 在PyInstaller环境中使用预编译包
                logger.info("检测到PyInstaller环境，使用预编译包安装")
                from precompiled_package_manager import get_precompiled_package_manager
                
                package_manager = get_precompiled_package_manager()
                
                def progress_callback(message, progress):
                    self._notify_progress({
                        'progress': 10 + (progress / 100) * 20,
                        'current_step': message
                    })
                
                return package_manager.install_ai_dependencies(progress_callback)
            else:
                # 在开发环境中使用pip安装
                logger.info("开发环境，使用pip安装")
                import subprocess
                
                packages = [
                    'sentence-transformers==2.7.0',
                    'faiss-cpu==1.12.0',
                    'torch>=2.1.0',
                    'transformers==4.44.0'
                ]
                
                # 设置代理环境变量
                self._setup_proxy_environment()
                
                for i, package in enumerate(packages):
                    self._notify_progress({
                        'progress': 10 + (i / len(packages)) * 20,
                        'current_step': f'安装 {package}...'
                    })
                    
                    logger.info(f"安装包: {package}")
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', package, '--quiet'
                    ], capture_output=True, text=True, timeout=300, env=os.environ.copy())
                    
                    if result.returncode != 0:
                        logger.error(f"安装失败 {package}: {result.stderr}")
                        return False
                
                logger.info("AI依赖安装完成")
                return True
            
        except Exception as e:
            logger.error(f"安装AI依赖失败: {e}")
            return False
    
    def _download_sentence_transformer_model(self) -> bool:
        """下载sentence transformer模型，支持重试和备用下载源"""
        try:
            # 检测是否在PyInstaller环境中
            is_pyinstaller = hasattr(sys, 'frozen') and hasattr(sys, '_MEIPASS')
            
            if is_pyinstaller:
                # 在PyInstaller环境中使用预编译包
                logger.info("检测到PyInstaller环境，使用预编译包安装模型")
                from precompiled_package_manager import get_precompiled_package_manager
                
                package_manager = get_precompiled_package_manager()
                
                def progress_callback(message, progress):
                    self._notify_progress({
                        'progress': 30 + (progress / 100) * 50,
                        'current_step': message
                    })
                
                return package_manager.install_ai_models(progress_callback)
            else:
                # 在开发环境中使用传统下载方式
                logger.info("开发环境，使用传统方式下载模型")
                from model_manager import get_model_manager
                manager = get_model_manager()
                
                def progress_callback(file_name, progress):
                    self._notify_progress({
                        'progress': 30 + (progress / 100) * 50,
                        'current_step': f'下载 {file_name}...'
                    })
                
                # 尝试下载，如果失败则重试
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        self._notify_progress({
                            'current_step': f'下载模型文件 (尝试 {attempt + 1}/{max_retries})...'
                        })
                        
                        success = manager.download_sentence_transformer_model(progress_callback)
                        if success:
                            return True
                        else:
                            logger.warning(f"下载尝试 {attempt + 1} 失败")
                            
                    except Exception as e:
                        logger.warning(f"下载尝试 {attempt + 1} 出错: {e}")
                        if attempt < max_retries - 1:
                            self._notify_progress({
                                'current_step': f'下载失败，正在重试... (尝试 {attempt + 2}/{max_retries})'
                            })
                            time.sleep(2)  # 等待2秒后重试
                        else:
                            raise e
                
                return False
            
        except Exception as e:
            logger.error(f"下载sentence transformer模型失败: {e}")
            self._notify_progress({
                'error': f'模型下载失败: {str(e)}'
            })
            return False
    
    def _create_faiss_index(self) -> bool:
        """创建faiss索引"""
        try:
            from model_manager import get_model_manager
            manager = get_model_manager()
            
            def progress_callback(message, progress):
                self._notify_progress({
                    'progress': 80 + (progress / 100) * 20,
                    'current_step': message
                })
            
            success = manager.create_faiss_index(progress_callback)
            return success
            
        except Exception as e:
            logger.error(f"创建faiss索引失败: {e}")
            return False
    
    def get_download_status(self) -> Dict:
        """获取下载状态"""
        return self.download_status.copy()
    
    def is_downloading(self) -> bool:
        """检查是否正在下载"""
        return self.download_status.get('is_downloading', False)
    
    def is_completed(self) -> bool:
        """检查是否下载完成"""
        return self.download_status.get('completed', False)
    
    def get_error(self) -> Optional[str]:
        """获取错误信息"""
        return self.download_status.get('error')
    
    def start_background_download(self) -> threading.Thread:
        """启动后台下载"""
        if self.download_thread and self.download_thread.is_alive():
            return self.download_thread
        
        def download_worker():
            self.download_ai_environment()
        
        self.download_thread = threading.Thread(target=download_worker, daemon=True)
        self.download_thread.start()
        return self.download_thread
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """等待下载完成"""
        if not self.download_thread:
            return False
        
        self.download_thread.join(timeout=timeout)
        return self.is_completed()


def get_download_manager() -> AIDownloadManager:
    """获取下载管理器实例"""
    return AIDownloadManager()


if __name__ == '__main__':
    # 测试下载管理器
    manager = AIDownloadManager()
    
    def progress_callback(status):
        print(f"[{status['progress']:5.1f}%] {status['current_step']}")
        if status.get('error'):
            print(f"❌ 错误: {status['error']}")
    
    manager.add_progress_callback(progress_callback)
    
    print("🚀 开始测试AI下载管理器...")
    success = manager.download_ai_environment()
    
    if success:
        print("✅ 下载完成")
    else:
        print("❌ 下载失败")
