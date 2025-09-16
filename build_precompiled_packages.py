#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
预编译包构建脚本
用于构建AI依赖包和模型包，供PyInstaller环境使用
"""

import os
import sys
import json
import zipfile
import hashlib
import shutil
import tempfile
from pathlib import Path
import subprocess
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PrecompiledPackageBuilder:
    """预编译包构建器"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化构建器
        
        Args:
            base_dir: 基础目录
        """
        if base_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.base_dir = Path(base_dir)
        self.build_dir = self.base_dir / 'build' / 'precompiled_packages'
        self.build_dir.mkdir(parents=True, exist_ok=True)
        
        # 包配置
        self.package_configs = {
            'ai_dependencies': {
                'name': 'ai_dependencies',
                'version': '1.0.0',
                'description': 'AI依赖包 - 包含sentence-transformers, torch, faiss等',
                'packages': [
                    'sentence-transformers==2.7.0',
                    'faiss-cpu==1.12.0',
                    'torch>=2.1.0',
                    'transformers==4.44.0',
                    'numpy>=1.26.0'
                ]
            },
            'ai_models': {
                'name': 'ai_models',
                'version': '1.0.0',
                'description': 'AI模型包 - 包含sentence transformer模型和faiss索引',
                'model_name': 'all-MiniLM-L6-v2'
            }
        }
    
    def create_virtual_environment(self, env_name: str) -> Path:
        """
        创建虚拟环境
        
        Args:
            env_name: 环境名称
            
        Returns:
            Path: 虚拟环境路径
        """
        env_path = self.build_dir / f"venv_{env_name}"
        
        if env_path.exists():
            logger.info(f"虚拟环境 {env_name} 已存在，跳过创建")
            return env_path
        
        logger.info(f"创建虚拟环境: {env_name}")
        result = subprocess.run([
            sys.executable, '-m', 'venv', str(env_path)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"创建虚拟环境失败: {result.stderr}")
        
        logger.info(f"虚拟环境创建成功: {env_path}")
        return env_path
    
    def install_packages_to_venv(self, env_path: Path, packages: list) -> bool:
        """
        在虚拟环境中安装包
        
        Args:
            env_path: 虚拟环境路径
            packages: 包列表
            
        Returns:
            bool: 安装是否成功
        """
        if sys.platform == 'win32':
            pip_path = env_path / 'Scripts' / 'pip.exe'
        else:
            pip_path = env_path / 'bin' / 'pip'
        
        logger.info(f"在虚拟环境中安装包: {packages}")
        
        for package in packages:
            logger.info(f"安装包: {package}")
            result = subprocess.run([
                str(pip_path), 'install', package
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"安装包 {package} 失败: {result.stderr}")
                return False
        
        logger.info("所有包安装完成")
        return True
    
    def download_model_in_venv(self, env_path: Path, model_name: str) -> bool:
        """
        在虚拟环境中下载模型
        
        Args:
            env_path: 虚拟环境路径
            model_name: 模型名称
            
        Returns:
            bool: 下载是否成功
        """
        if sys.platform == 'win32':
            python_path = env_path / 'Scripts' / 'python.exe'
        else:
            python_path = env_path / 'bin' / 'python'
        
        # 创建下载脚本
        download_script = self.build_dir / 'download_model.py'
        script_content = f'''
import os
import sys
from sentence_transformers import SentenceTransformer

# 设置缓存目录
cache_dir = "{self.build_dir / 'models_cache'}"
os.makedirs(cache_dir, exist_ok=True)
os.environ['HF_HOME'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir

# 下载模型
print(f"下载模型: {model_name}")
model = SentenceTransformer("{model_name}", cache_folder=cache_dir)

# 测试模型
test_text = "这是一个测试文本"
embedding = model.encode([test_text])
print(f"模型测试成功，向量维度: {{embedding.shape}}")
print("模型下载完成")
'''
        
        with open(download_script, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"在虚拟环境中下载模型: {model_name}")
        result = subprocess.run([
            str(python_path), str(download_script)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"下载模型失败: {result.stderr}")
            return False
        
        logger.info("模型下载完成")
        return True
    
    def build_ai_dependencies_package(self) -> bool:
        """
        构建AI依赖包
        
        Returns:
            bool: 构建是否成功
        """
        logger.info("开始构建AI依赖包...")
        
        try:
            # 创建虚拟环境
            env_path = self.create_virtual_environment('ai_deps')
            
            # 安装包
            config = self.package_configs['ai_dependencies']
            if not self.install_packages_to_venv(env_path, config['packages']):
                return False
            
            # 创建包目录结构
            package_dir = self.build_dir / 'ai_dependencies_package'
            if package_dir.exists():
                shutil.rmtree(package_dir)
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制site-packages
            if sys.platform == 'win32':
                site_packages = env_path / 'Lib' / 'site-packages'
            else:
                site_packages = env_path / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'site-packages'
            
            target_site_packages = package_dir / 'site-packages'
            shutil.copytree(site_packages, target_site_packages)
            
            # 创建元数据
            metadata = {
                'name': config['name'],
                'version': config['version'],
                'description': config['description'],
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
                'platform': sys.platform,
                'packages': config['packages'],
                'created_at': str(Path().cwd()),
                'build_info': {
                    'python_executable': sys.executable,
                    'build_dir': str(self.build_dir)
                }
            }
            
            with open(package_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 创建ZIP包
            zip_path = self.build_dir / f"ai_dependencies_v{config['version']}.zip"
            self.create_zip_package(package_dir, zip_path)
            
            # 计算校验和
            checksum = self.calculate_file_checksum(zip_path)
            logger.info(f"AI依赖包构建完成: {zip_path}")
            logger.info(f"校验和: {checksum}")
            
            return True
            
        except Exception as e:
            logger.error(f"构建AI依赖包失败: {e}")
            return False
    
    def build_ai_models_package(self) -> bool:
        """
        构建AI模型包
        
        Returns:
            bool: 构建是否成功
        """
        logger.info("开始构建AI模型包...")
        
        try:
            # 创建虚拟环境并下载模型
            env_path = self.create_virtual_environment('ai_models')
            
            # 先安装必要的包
            required_packages = ['sentence-transformers', 'torch', 'transformers']
            if not self.install_packages_to_venv(env_path, required_packages):
                return False
            
            # 下载模型
            config = self.package_configs['ai_models']
            if not self.download_model_in_venv(env_path, config['model_name']):
                return False
            
            # 创建包目录结构
            package_dir = self.build_dir / 'ai_models_package'
            if package_dir.exists():
                shutil.rmtree(package_dir)
            package_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制模型文件
            models_cache = self.build_dir / 'models_cache'
            if models_cache.exists():
                # 复制sentence transformer模型
                st_source = models_cache / f"models--sentence-transformers--{config['model_name']}"
                st_target = package_dir / 'sentence-transformers' / config['model_name']
                st_target.mkdir(parents=True, exist_ok=True)
                
                if st_source.exists():
                    # 找到实际的模型文件
                    snapshots_dir = st_source / 'snapshots'
                    if snapshots_dir.exists():
                        for snapshot_dir in snapshots_dir.iterdir():
                            if snapshot_dir.is_dir():
                                shutil.copytree(snapshot_dir, st_target, dirs_exist_ok=True)
                                break
                
                # 创建faiss索引目录（空目录，实际索引会在运行时创建）
                faiss_dir = package_dir / 'similarity_index'
                faiss_dir.mkdir(parents=True, exist_ok=True)
                
                # 创建空的faiss索引文件
                (faiss_dir / 'faiss_index.bin').touch()
                (faiss_dir / 'metadata.json').write_text('{"created": false, "note": "将在运行时创建"}')
            
            # 创建元数据
            metadata = {
                'name': config['name'],
                'version': config['version'],
                'description': config['description'],
                'model_name': config['model_name'],
                'python_version': f"{sys.version_info.major}.{sys.version_info.minor}",
                'platform': sys.platform,
                'created_at': str(Path().cwd()),
                'build_info': {
                    'python_executable': sys.executable,
                    'build_dir': str(self.build_dir)
                }
            }
            
            with open(package_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # 创建ZIP包
            zip_path = self.build_dir / f"ai_models_v{config['version']}.zip"
            self.create_zip_package(package_dir, zip_path)
            
            # 计算校验和
            checksum = self.calculate_file_checksum(zip_path)
            logger.info(f"AI模型包构建完成: {zip_path}")
            logger.info(f"校验和: {checksum}")
            
            return True
            
        except Exception as e:
            logger.error(f"构建AI模型包失败: {e}")
            return False
    
    def create_zip_package(self, source_dir: Path, zip_path: Path) -> None:
        """
        创建ZIP包
        
        Args:
            source_dir: 源目录
            zip_path: ZIP文件路径
        """
        logger.info(f"创建ZIP包: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"ZIP包创建完成: {zip_path}")
    
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
    
    def build_all_packages(self) -> bool:
        """
        构建所有包
        
        Returns:
            bool: 构建是否成功
        """
        logger.info("开始构建所有预编译包...")
        
        success = True
        
        # 构建AI依赖包
        if not self.build_ai_dependencies_package():
            success = False
        
        # 构建AI模型包
        if not self.build_ai_models_package():
            success = False
        
        if success:
            logger.info("所有预编译包构建完成!")
            self.print_build_summary()
        else:
            logger.error("部分预编译包构建失败!")
        
        return success
    
    def print_build_summary(self):
        """打印构建摘要"""
        print("\n" + "="*60)
        print("📦 预编译包构建摘要")
        print("="*60)
        
        for package_name in ['ai_dependencies', 'ai_models']:
            config = self.package_configs[package_name]
            zip_path = self.build_dir / f"{package_name}_v{config['version']}.zip"
            
            if zip_path.exists():
                size_mb = zip_path.stat().st_size / (1024 * 1024)
                checksum = self.calculate_file_checksum(zip_path)
                print(f"\n📦 {package_name} v{config['version']}")
                print(f"   文件: {zip_path.name}")
                print(f"   大小: {size_mb:.1f} MB")
                print(f"   校验和: {checksum}")
            else:
                print(f"\n❌ {package_name} - 构建失败")
        
        print(f"\n📁 构建目录: {self.build_dir}")
        print("\n💡 下一步:")
        print("   1. 将生成的ZIP文件上传到CDN")
        print("   2. 更新 precompiled_package_manager.py 中的下载地址和校验和")
        print("   3. 测试预编译包下载和安装")


def main():
    """主函数"""
    print("🔧 预编译包构建工具")
    print("="*50)
    
    builder = PrecompiledPackageBuilder()
    
    # 检查是否在虚拟环境中
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ 检测到虚拟环境")
    else:
        print("⚠️ 未检测到虚拟环境，建议在虚拟环境中构建")
        response = input("是否继续构建? (y/N): ")
        if response.lower() != 'y':
            print("构建已取消")
            return
    
    # 构建所有包
    success = builder.build_all_packages()
    
    if success:
        print("\n🎉 预编译包构建完成!")
    else:
        print("\n❌ 预编译包构建失败!")
        sys.exit(1)


if __name__ == '__main__':
    main()
