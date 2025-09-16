import faiss
import numpy as np
import json
import hashlib
import os
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class DocumentSimilarityService:
    """文档相似度检测服务"""
    
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384  # all-MiniLM-L6-v2的向量维度
        self.index = None
        self.document_metadata = {}
        self.index_path = os.path.join(settings.BASE_DIR, 'data', 'similarity_index')
        self.load_or_create_index()
    
    def load_or_create_index(self):
        """加载或创建FAISS索引"""
        os.makedirs(self.index_path, exist_ok=True)
        index_file = os.path.join(self.index_path, 'faiss_index.bin')
        metadata_file = os.path.join(self.index_path, 'metadata.json')
        
        if os.path.exists(index_file) and os.path.exists(metadata_file):
            try:
                # 加载现有索引
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
        self.index = faiss.IndexFlatIP(self.dimension)  # 内积索引，适合余弦相似度
        self.document_metadata = {}
        logger.info("创建新的相似度索引")
    
    def add_document(self, doc_id: str, content: str, metadata: Dict = None) -> bool:
        """添加文档到索引"""
        try:
            # 生成向量
            vector = self.model.encode([content])[0]
            vector = vector.astype('float32')
            
            # 归一化向量（用于余弦相似度）
            faiss.normalize_L2(vector.reshape(1, -1))
            
            # 添加到索引
            self.index.add(vector.reshape(1, -1))
            
            # 保存元数据
            doc_index = str(self.index.ntotal - 1)
            self.document_metadata[doc_index] = {
                'doc_id': doc_id,
                'content_preview': content[:200],  # 只保存前200字符用于预览
                'metadata': metadata or {}
            }
            
            # 保存到Django缓存
            cache_key = f"doc_vector:{doc_id}"
            cache.set(cache_key, vector.tobytes(), timeout=3600)
            
            # 定期保存索引
            if self.index.ntotal % 50 == 0:
                self.save_index()
                
            logger.info(f"文档 {doc_id} 已添加到相似度索引")
            return True
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
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
            
            if self.index.ntotal == 0:
                logger.warning("索引为空，无法进行相似度检测")
                return []
            
            # 生成查询向量
            query_vector = self.model.encode([query_content])[0]
            query_vector = query_vector.astype('float32')
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
            cache.set(cache_key, results, timeout=1800)  # 缓存30分钟
            
            logger.info(f"找到 {len(results)} 个相似文档")
            return results
            
        except Exception as e:
            logger.error(f"搜索相似文档失败: {e}")
            return []
    
    def save_index(self):
        """保存索引到磁盘"""
        try:
            index_file = os.path.join(self.index_path, 'faiss_index.bin')
            metadata_file = os.path.join(self.index_path, 'metadata.json')
            
            faiss.write_index(self.index, index_file)
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info("索引已保存到磁盘")
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
    
    def rebuild_index_from_database(self) -> int:
        """从数据库重建索引"""
        from .models import FileSave
        
        logger.info("开始重建相似度索引...")
        
        # 清空现有索引
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
            'total_documents': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'index_type': 'IndexFlatIP',
            'last_updated': timezone.now().isoformat()
        }

# 全局实例
similarity_service = DocumentSimilarityService()
