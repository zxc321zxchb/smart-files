#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
轻量级相似度服务 - 支持动态加载AI模型
"""

import os
import json
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

# 延迟导入numpy以避免PyInstaller兼容性问题
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

logger = logging.getLogger(__name__)

class SimilarityServiceLite:
    """轻量级相似度检测服务 - 支持动态加载AI模型"""
    
    def __init__(self):
        self.model = None
        self.dimension = 384  # all-MiniLM-L6-v2的向量维度
        self.index = None
        self.document_metadata = {}
        self.index_path = os.path.join(settings.BASE_DIR, 'data', 'similarity_index')
        self.ai_available = False
        self.model_loaded = False
        
        # 尝试加载AI模型
        self._try_load_ai_model()
        
        # 加载或创建索引
        self.load_or_create_index()
    
    def _try_load_ai_model(self):
        """尝试加载AI模型"""
        try:
            # 检查模型文件是否存在
            from model_manager import get_model_manager
            manager = get_model_manager()
            model_status = manager.check_model_files()
            
            if model_status.get('sentence_transformer', False):
                # 尝试导入AI依赖
                from sentence_transformers import SentenceTransformer
                import faiss
                
                # 加载模型
                model_path = os.path.join(settings.BASE_DIR, 'data', 'models', 'sentence-transformers', 'all-MiniLM-L6-v2')
                self.model = SentenceTransformer(model_path)
                self.ai_available = True
                self.model_loaded = True
                logger.info("AI模型加载成功")
            else:
                logger.info("AI模型文件不存在，使用基础相似度算法")
                
        except ImportError as e:
            logger.info(f"AI依赖未安装: {e}")
        except Exception as e:
            logger.error(f"加载AI模型失败: {e}")
    
    def load_or_create_index(self):
        """加载或创建索引"""
        os.makedirs(self.index_path, exist_ok=True)
        index_file = os.path.join(self.index_path, 'faiss_index.bin')
        metadata_file = os.path.join(self.index_path, 'metadata.json')
        
        if self.ai_available and os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                # 加载现有索引
                import faiss
                self.index = faiss.read_index(index_file)
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.document_metadata = json.load(f)
                logger.info(f"已加载相似度索引，包含 {self.index.ntotal} 个文档")
            except Exception as e:
                logger.error(f"加载索引失败: {e}")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """创建新索引"""
        if self.ai_available:
            try:
                import faiss
                self.index = faiss.IndexFlatIP(self.dimension)
                logger.info("创建新的AI相似度索引")
            except ImportError:
                self.index = None
                logger.info("AI依赖不可用，使用基础相似度算法")
        else:
            self.index = None
            logger.info("使用基础相似度算法")
    
    def add_document(self, doc_id: str, content: str, metadata: Dict = None) -> bool:
        """添加文档到索引"""
        try:
            if self.ai_available and self.model and self.index is not None:
                # 使用AI模型
                return self._add_document_with_ai(doc_id, content, metadata)
            else:
                # 使用基础算法
                return self._add_document_basic(doc_id, content, metadata)
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def _add_document_with_ai(self, doc_id: str, content: str, metadata: Dict = None) -> bool:
        """使用AI模型添加文档"""
        try:
            # 生成向量
            vector = self.model.encode([content])[0]
            vector = vector.astype('float32')
            
            # 归一化向量（用于余弦相似度）
            import faiss
            faiss.normalize_L2(vector.reshape(1, -1))
            
            # 添加到索引
            self.index.add(vector.reshape(1, -1))
            
            # 保存元数据
            doc_index = str(self.index.ntotal - 1)
            self.document_metadata[doc_index] = {
                'doc_id': doc_id,
                'content_preview': content[:200],
                'metadata': metadata or {}
            }
            
            # 保存到Django缓存
            cache_key = f"doc_vector:{doc_id}"
            cache.set(cache_key, vector.tobytes(), timeout=3600)
            
            # 定期保存索引
            if self.index.ntotal % 50 == 0:
                self.save_index()
                
            logger.info(f"文档 {doc_id} 已添加到AI相似度索引")
            return True
        except Exception as e:
            logger.error(f"AI添加文档失败: {e}")
            return False
    
    def _add_document_basic(self, doc_id: str, content: str, metadata: Dict = None) -> bool:
        """使用基础算法添加文档"""
        try:
            # 使用简单的文本特征作为"向量"
            features = self._extract_text_features(content)
            
            # 保存到元数据
            doc_index = str(len(self.document_metadata))
            self.document_metadata[doc_index] = {
                'doc_id': doc_id,
                'content_preview': content[:200],
                'features': features,
                'metadata': metadata or {}
            }
            
            # 保存到Django缓存
            cache_key = f"doc_features:{doc_id}"
            cache.set(cache_key, features, timeout=3600)
            
            logger.info(f"文档 {doc_id} 已添加到基础相似度索引")
            return True
        except Exception as e:
            logger.error(f"基础添加文档失败: {e}")
            return False
    
    def _extract_text_features(self, content: str) -> Dict:
        """提取文本特征（基础算法）"""
        import re
        from collections import Counter
        
        # 清理文本
        text = re.sub(r'[^\w\s]', ' ', content.lower())
        words = text.split()
        
        # 计算基础特征
        features = {
            'word_count': len(words),
            'char_count': len(content),
            'unique_words': len(set(words)),
            'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'common_words': dict(Counter(words).most_common(10)),
            'has_numbers': bool(re.search(r'\d', content)),
            'has_urls': bool(re.search(r'http[s]?://', content)),
            'has_emails': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content))
        }
        
        return features
    
    def find_similar_documents(self, query_content: str, top_k: int = 5, threshold: float = 0.3) -> List[Dict]:
        """查找相似文档"""
        try:
            # 检查缓存
            content_hash = hashlib.md5(query_content.encode()).hexdigest()
            cache_key = f"similarity:{content_hash}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info("使用缓存的相似度检测结果")
                return cached_result
            
            if self.ai_available and self.model and self.index is not None:
                # 使用AI模型
                return self._find_similar_with_ai(query_content, top_k, threshold)
            else:
                # 使用基础算法
                return self._find_similar_basic(query_content, top_k, threshold)
                
        except Exception as e:
            logger.error(f"搜索相似文档失败: {e}")
            return []
    
    def _find_similar_with_ai(self, query_content: str, top_k: int, threshold: float) -> List[Dict]:
        """使用AI模型查找相似文档"""
        try:
            if self.index.ntotal == 0:
                logger.warning("索引为空，无法进行相似度检测")
                return []
            
            # 生成查询向量
            query_vector = self.model.encode([query_content])[0]
            query_vector = query_vector.astype('float32')
            import faiss
            faiss.normalize_L2(query_vector.reshape(1, -1))
            
            # 搜索相似文档
            similarities, indices = self.index.search(query_vector.reshape(1, -1), top_k)
            
            results = []
            for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
                if similarity >= threshold:
                    doc_metadata = self.document_metadata.get(str(idx), {})
                    results.append({
                        'doc_id': doc_metadata.get('doc_id', ''),
                        'similarity_score': float(similarity),
                        'content_preview': doc_metadata.get('content_preview', ''),
                        'metadata': doc_metadata.get('metadata', {})
                    })
            
            # 缓存结果
            cache.set(cache_key, results, timeout=1800)
            
            logger.info(f"找到 {len(results)} 个相似文档（AI算法）")
            return results
            
        except Exception as e:
            logger.error(f"AI搜索相似文档失败: {e}")
            return []
    
    def _find_similar_basic(self, query_content: str, top_k: int, threshold: float) -> List[Dict]:
        """使用基础算法查找相似文档"""
        try:
            if not self.document_metadata:
                logger.warning("没有文档数据，无法进行相似度检测")
                return []
            
            # 提取查询特征
            query_features = self._extract_text_features(query_content)
            
            # 计算相似度
            similarities = []
            for doc_index, doc_data in self.document_metadata.items():
                doc_features = doc_data.get('features', {})
                similarity = self._calculate_basic_similarity(query_features, doc_features)
                
                if similarity >= threshold:
                    similarities.append({
                        'doc_id': doc_data.get('doc_id', ''),
                        'similarity_score': similarity,
                        'content_preview': doc_data.get('content_preview', ''),
                        'metadata': doc_data.get('metadata', {}),
                        'doc_index': doc_index
                    })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = similarities[:top_k]
            
            # 缓存结果
            cache_key = f"similarity:{hashlib.md5(query_content.encode()).hexdigest()}"
            cache.set(cache_key, results, timeout=1800)
            
            logger.info(f"找到 {len(results)} 个相似文档（基础算法）")
            return results
            
        except Exception as e:
            logger.error(f"基础搜索相似文档失败: {e}")
            return []
    
    def _calculate_basic_similarity(self, features1: Dict, features2: Dict) -> float:
        """计算基础相似度"""
        try:
            # 基于多个特征的加权相似度
            weights = {
                'word_count': 0.2,
                'char_count': 0.1,
                'unique_words': 0.2,
                'avg_word_length': 0.1,
                'common_words': 0.3,
                'has_numbers': 0.05,
                'has_urls': 0.05
            }
            
            total_similarity = 0.0
            total_weight = 0.0
            
            for feature, weight in weights.items():
                if feature in features1 and feature in features2:
                    if feature == 'common_words':
                        # 计算词汇重叠度
                        words1 = set(features1[feature].keys())
                        words2 = set(features2[feature].keys())
                        if words1 or words2:
                            overlap = len(words1.intersection(words2))
                            union = len(words1.union(words2))
                            similarity = overlap / union if union > 0 else 0
                        else:
                            similarity = 0
                    else:
                        # 数值特征相似度
                        val1 = features1[feature]
                        val2 = features2[feature]
                        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                            if val1 == 0 and val2 == 0:
                                similarity = 1.0
                            else:
                                max_val = max(abs(val1), abs(val2))
                                similarity = 1.0 - abs(val1 - val2) / max_val if max_val > 0 else 0
                        else:
                            similarity = 1.0 if val1 == val2 else 0.0
                    
                    total_similarity += similarity * weight
                    total_weight += weight
            
            return total_similarity / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"计算基础相似度失败: {e}")
            return 0.0
    
    def save_index(self):
        """保存索引到磁盘"""
        try:
            if self.ai_available and self.index is not None:
                import faiss
                index_file = os.path.join(self.index_path, 'faiss_index.bin')
                metadata_file = os.path.join(self.index_path, 'metadata.json')
                
                faiss.write_index(self.index, index_file)
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
                
                logger.info("AI索引已保存到磁盘")
            else:
                # 保存基础索引
                metadata_file = os.path.join(self.index_path, 'metadata.json')
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
                
                logger.info("基础索引已保存到磁盘")
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
    
    def rebuild_index(self) -> int:
        """重建索引"""
        from .models import FileSave
        
        logger.info("开始重建相似度索引...")
        
        # 清空现有索引
        if self.ai_available and self.index is not None:
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)
        self.document_metadata = {}
        
        # 从数据库加载所有文档
        documents = FileSave.objects.filter(
            content_type__in=['text/markdown', 'text/plain']
        ).values('id', 'filename', 'content_data', 'file_path', 'created_at')
        
        success_count = 0
        for doc in documents:
            try:
                import base64
                content = base64.b64decode(doc['content_data']).decode('utf-8')
                self.add_document(
                    doc_id=str(doc['id']),
                    content=content,
                    metadata={
                        'filename': doc['filename'],
                        'file_path': doc['file_path'],
                        'created_at': doc['created_at'].isoformat() if doc['created_at'] else ''
                    }
                )
                success_count += 1
            except Exception as e:
                logger.error(f"处理文档 {doc['id']} 失败: {e}")
        
        self.save_index()
        logger.info(f"索引重建完成，成功处理 {success_count} 个文档")
        return success_count
    
    def get_index_stats(self) -> Dict:
        """获取索引统计信息"""
        return {
            'total_documents': len(self.document_metadata),
            'ai_available': self.ai_available,
            'model_loaded': self.model_loaded,
            'index_type': 'AI' if self.ai_available else 'Basic',
            'last_updated': timezone.now().isoformat()
        }
    
    def get_ai_status(self) -> Dict:
        """获取AI状态信息"""
        from model_manager import get_model_manager
        manager = get_model_manager()
        return manager.get_model_status()

# 全局实例
similarity_service = SimilarityServiceLite()