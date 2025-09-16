#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
S3/R2下载管理器 - 通过S3协议下载预编译包
支持Cloudflare R2和AWS S3
"""

import os
import sys
import boto3
import logging
from pathlib import Path
from typing import Dict, Optional, Callable
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

logger = logging.getLogger(__name__)

class S3DownloadManager:
    """S3/R2下载管理器"""
    
    def __init__(self, 
                 access_key: str = None,
                 secret_key: str = None,
                 endpoint_url: str = None,
                 region: str = 'auto',
                 bucket_name: str = None):
        """
        初始化S3下载管理器
        
        Args:
            access_key: S3访问密钥ID
            secret_key: S3秘密访问密钥
            endpoint_url: S3端点URL（R2使用）
            region: 区域名称
            bucket_name: 存储桶名称
        """
        self.access_key = access_key or os.environ.get('S3_ACCESS_KEY')
        self.secret_key = secret_key or os.environ.get('S3_SECRET_KEY')
        self.endpoint_url = endpoint_url or os.environ.get('S3_ENDPOINT_URL')
        self.region = region
        self.bucket_name = bucket_name or os.environ.get('S3_BUCKET_NAME')
        
        # 验证必需参数
        if not all([self.access_key, self.secret_key, self.endpoint_url, self.bucket_name]):
            raise ValueError("缺少必需的S3配置参数")
        
        # 创建S3客户端
        self.s3_client = self._create_s3_client()
        
        # 测试连接
        self._test_connection()
    
    def _create_s3_client(self):
        """创建S3客户端"""
        try:
            config = Config(
                region_name=self.region,
                retries={'max_attempts': 3, 'mode': 'adaptive'},
                max_pool_connections=50
            )
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint_url,
                config=config
            )
            
            logger.info(f"S3客户端创建成功，端点: {self.endpoint_url}")
            return s3_client
            
        except Exception as e:
            logger.error(f"创建S3客户端失败: {e}")
            raise
    
    def _test_connection(self):
        """测试S3连接"""
        try:
            # 直接尝试访问存储桶
            response = self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3连接测试成功，存储桶: {self.bucket_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"存储桶不存在: {self.bucket_name}")
            elif error_code == 'AccessDenied':
                logger.warning(f"无法访问存储桶 {self.bucket_name}，但连接正常")
                return True  # 连接正常，只是权限不足
            else:
                logger.error(f"S3连接测试失败: {e}")
            raise
        except Exception as e:
            logger.error(f"S3连接测试出错: {e}")
            raise
    
    def list_objects(self, prefix: str = '') -> list:
        """
        列出存储桶中的对象
        
        Args:
            prefix: 对象前缀
            
        Returns:
            list: 对象列表
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            objects = response.get('Contents', [])
            logger.info(f"找到 {len(objects)} 个对象，前缀: {prefix}")
            return objects
            
        except Exception as e:
            logger.error(f"列出对象失败: {e}")
            return []
    
    def download_file(self, 
                     object_key: str, 
                     local_path: str,
                     progress_callback: Optional[Callable[[str, float], None]] = None) -> bool:
        """
        下载文件
        
        Args:
            object_key: S3对象键
            local_path: 本地保存路径
            progress_callback: 进度回调函数
            
        Returns:
            bool: 下载是否成功
        """
        try:
            local_file = Path(local_path)
            local_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"开始下载文件: {object_key} -> {local_path}")
            
            # 获取对象大小
            try:
                response = self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
                total_size = response['ContentLength']
            except:
                total_size = 0
            
            # 下载文件
            downloaded_size = 0
            
            def progress_callback_wrapper(bytes_transferred):
                nonlocal downloaded_size
                downloaded_size += bytes_transferred
                if progress_callback and total_size > 0:
                    progress = (downloaded_size / total_size) * 100
                    progress_callback(object_key, progress)
            
            self.s3_client.download_file(
                self.bucket_name,
                object_key,
                str(local_file),
                Callback=progress_callback_wrapper
            )
            
            logger.info(f"文件下载完成: {object_key}")
            return True
            
        except ClientError as e:
            logger.error(f"下载文件失败 {object_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"下载文件出错 {object_key}: {e}")
            return False
    
    def get_object_metadata(self, object_key: str) -> Optional[Dict]:
        """
        获取对象元数据
        
        Args:
            object_key: S3对象键
            
        Returns:
            Dict: 对象元数据
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType', 'application/octet-stream')
            }
        except Exception as e:
            logger.error(f"获取对象元数据失败 {object_key}: {e}")
            return None
    
    def check_object_exists(self, object_key: str) -> bool:
        """
        检查对象是否存在
        
        Args:
            object_key: S3对象键
            
        Returns:
            bool: 对象是否存在
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"检查对象存在性失败 {object_key}: {e}")
                return False
        except Exception as e:
            logger.error(f"检查对象存在性出错 {object_key}: {e}")
            return False


def create_r2_download_manager(bucket_name: str = None) -> S3DownloadManager:
    """
    创建Cloudflare R2下载管理器
    
    Args:
        bucket_name: R2存储桶名称
        
    Returns:
        S3DownloadManager: R2下载管理器实例
    """
    # R2配置
    access_key = "f6134b6af4adc6ffab7d4c9299aed86b"
    secret_key = "d9df31a440a03dc9873d0afb880898ff9fbf862c54aba0ea8074897378406f6f"
    endpoint_url = "https://23d76b352b41d77575c8640d98115aa3.r2.cloudflarestorage.com"
    
    return S3DownloadManager(
        access_key=access_key,
        secret_key=secret_key,
        endpoint_url=endpoint_url,
        region='auto',
        bucket_name=bucket_name or 'life'
    )


def get_s3_download_manager() -> S3DownloadManager:
    """获取S3下载管理器实例"""
    try:
        return create_r2_download_manager()
    except Exception as e:
        logger.error(f"创建S3下载管理器失败: {e}")
        raise


if __name__ == '__main__':
    # 测试S3下载管理器
    try:
        manager = get_s3_download_manager()
        
        print("=== S3连接测试 ===")
        print(f"存储桶: {manager.bucket_name}")
        print(f"端点: {manager.endpoint_url}")
        
        print("\n=== 列出对象 ===")
        objects = manager.list_objects()
        for obj in objects[:5]:  # 只显示前5个
            print(f"  {obj['Key']} ({obj['Size']} bytes)")
        
        print("\n✅ S3下载管理器测试成功")
        
    except Exception as e:
        print(f"❌ S3下载管理器测试失败: {e}")
        sys.exit(1)
