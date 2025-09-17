#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
清理版相似度服务
专注于基础算法，移除所有AI依赖，为后期升级预留接口
"""

import os
import sys
import json
import hashlib
import logging
import re
import math
from typing import List, Dict, Optional, Tuple, Any
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class SimilarityServiceSimple:
    """清理版相似度检测服务 - 专注基础算法"""
    
    def __init__(self):
        self.document_metadata = {}
        self.index_path = os.path.join(settings.BASE_DIR, 'data', 'similarity_index')
        
        # 为后期AI升级预留的接口
        self.ai_interface = None
        self.ai_available = False
        
        # 加载现有索引
        self.load_or_create_index()
    
    def _extract_text_features(self, content: str) -> Dict[str, Any]:
        """提取文本特征（增强版）"""
        try:
            # 基础文本清理
            cleaned_content = self._clean_text(content)
            
            # 分词（简单版本）
            words = self._simple_tokenize(cleaned_content)
            
            # 提取各种特征
            features = {
                # 基础统计特征
                'word_count': len(words),
                'char_count': len(content),
                'unique_words': len(set(words)),
                'avg_word_length': sum(len(w) for w in words) / len(words) if words else 0,
                
                # 词汇特征
                'common_words': dict(Counter(words).most_common(20)),
                'word_frequency': self._calculate_word_frequency(words),
                'vocabulary_richness': len(set(words)) / len(words) if words else 0,
                
                # 结构特征
                'sentence_count': len(re.split(r'[。！？]', content)),
                'paragraph_count': len([p for p in content.split('\n') if p.strip()]),
                'has_numbers': bool(re.search(r'\d', content)),
                'has_urls': bool(re.search(r'http[s]?://', content)),
                'has_emails': bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)),
                'has_phone': bool(re.search(r'1[3-9]\d{9}', content)),
                
                # 语言特征
                'chinese_ratio': self._get_chinese_ratio(content),
                'english_ratio': self._get_english_ratio(content),
                'digit_ratio': self._get_digit_ratio(content),
                
                # 语义特征（简化版）
                'semantic_keywords': self._extract_semantic_keywords(words),
                'topic_words': self._extract_topic_words(words),
                
                # 时间特征
                'has_time': bool(re.search(r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', content)),
                'has_date': bool(re.search(r'(今天|昨天|明天|今年|去年|明年)', content)),
                
                # 情感特征（简化版）
                'sentiment_score': self._calculate_sentiment_score(words),
            }
            
            return features
            
        except Exception as e:
            logger.error(f"提取文本特征失败: {e}")
            return {}
    
    def _clean_text(self, content: str) -> str:
        """清理文本"""
        # 移除HTML标签
        content = re.sub(r'<[^>]+>', '', content)
        # 移除多余空白
        content = re.sub(r'\s+', ' ', content)
        # 移除特殊字符但保留中文、英文、数字
        content = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', content)
        return content.strip()
    
    def _simple_tokenize(self, content: str) -> List[str]:
        """简单分词"""
        # 按空格和标点符号分词
        words = re.findall(r'\b\w+\b', content)
        # 过滤单字符词
        words = [w for w in words if len(w) > 1]
        return words
    
    def _calculate_word_frequency(self, words: List[str]) -> Dict[str, float]:
        """计算词频"""
        if not words:
            return {}
        word_count = Counter(words)
        total_words = len(words)
        return {word: count / total_words for word, count in word_count.items()}
    
    def _extract_semantic_keywords(self, words: List[str]) -> List[Tuple[str, float]]:
        """提取语义关键词（基于词频和长度）"""
        if not words:
            return []
        
        # 计算词的重要性分数
        word_scores = {}
        for word in words:
            if len(word) >= 2:  # 至少2个字符
                # 基于词频和长度的综合评分
                freq = words.count(word)
                length_score = len(word) / 10  # 长度分数
                freq_score = freq / len(words) * 100  # 频率分数
                word_scores[word] = length_score + freq_score
        
        # 返回得分最高的前10个词
        return sorted(word_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def _extract_topic_words(self, words: List[str]) -> List[Tuple[str, float]]:
        """提取主题词（基于TF简化版）"""
        if not words:
            return []
        
        # 简化的TF计算
        word_count = Counter(words)
        total_words = len(words)
        
        # 计算TF分数
        tf_scores = {}
        for word, count in word_count.items():
            if len(word) >= 2:
                tf_scores[word] = count / total_words
        
        # 返回TF分数最高的词
        return sorted(tf_scores.items(), key=lambda x: x[1], reverse=True)[:15]
    
    def _get_chinese_ratio(self, content: str) -> float:
        """获取中文字符比例"""
        if not content:
            return 0.0
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', content))
        return chinese_chars / len(content)
    
    def _get_english_ratio(self, content: str) -> float:
        """获取英文字符比例"""
        if not content:
            return 0.0
        english_chars = len(re.findall(r'[a-zA-Z]', content))
        return english_chars / len(content)
    
    def _get_digit_ratio(self, content: str) -> float:
        """获取数字字符比例"""
        if not content:
            return 0.0
        digit_chars = len(re.findall(r'\d', content))
        return digit_chars / len(content)
    
    def _calculate_sentiment_score(self, words: List[str]) -> float:
        """计算情感分数（简化版）"""
        if not words:
            return 0.0
        
        # 简单的情感词典
        positive_words = {'好', '棒', '优秀', '完美', '喜欢', '爱', '开心', '高兴', '满意', '成功'}
        negative_words = {'坏', '差', '糟糕', '讨厌', '恨', '难过', '失望', '失败', '问题', '错误'}
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count + negative_count == 0:
            return 0.0
        
        return (positive_count - negative_count) / (positive_count + negative_count)
    
    def _calculate_enhanced_similarity(self, features1: Dict, features2: Dict) -> float:
        """计算增强的相似度"""
        try:
            # 定义特征权重
            weights = {
                'word_count': 0.08,
                'char_count': 0.05,
                'unique_words': 0.08,
                'avg_word_length': 0.05,
                'common_words': 0.30,
                'word_frequency': 0.20,
                'vocabulary_richness': 0.08,
                'sentence_count': 0.03,
                'paragraph_count': 0.03,
                'has_numbers': 0.02,
                'has_urls': 0.02,
                'has_emails': 0.02,
                'has_phone': 0.02,
                'chinese_ratio': 0.05,
                'english_ratio': 0.05,
                'digit_ratio': 0.03,
                'sentiment_score': 0.08,
                'has_time': 0.02,
                'has_date': 0.02,
                'semantic_keywords': 0.15,
                'topic_words': 0.10,
            }
            
            total_similarity = 0.0
            total_weight = 0.0
            
            for feature, weight in weights.items():
                if feature in features1 and feature in features2:
                    similarity = self._calculate_feature_similarity(
                        features1[feature], features2[feature], feature
                    )
                    total_similarity += similarity * weight
                    total_weight += weight
            
            return total_similarity / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            logger.error(f"计算增强相似度失败: {e}")
            return 0.0
    
    def _calculate_feature_similarity(self, val1: Any, val2: Any, feature: str) -> float:
        """计算单个特征的相似度"""
        try:
            if feature in ['common_words', 'word_frequency']:
                # 字典类型特征
                return self._calculate_dict_similarity(val1, val2)
            elif feature in ['semantic_keywords', 'topic_words']:
                # 列表类型特征（转换为字典）
                dict1 = dict(val1) if isinstance(val1, list) else val1
                dict2 = dict(val2) if isinstance(val2, list) else val2
                return self._calculate_dict_similarity(dict1, dict2)
            elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                # 数值特征相似度
                return self._calculate_numeric_similarity(val1, val2)
            else:
                # 布尔特征相似度
                return 1.0 if val1 == val2 else 0.0
                
        except Exception as e:
            logger.warning(f"计算特征相似度失败 {feature}: {e}")
            return 0.0
    
    def _calculate_dict_similarity(self, dict1: Dict, dict2: Dict) -> float:
        """计算字典相似度（Jaccard相似度）"""
        if not dict1 and not dict2:
            return 1.0
        if not dict1 or not dict2:
            return 0.0
        
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())
        
        intersection = keys1.intersection(keys2)
        union = keys1.union(keys2)
        
        if not union:
            return 0.0
        
        # 基础Jaccard相似度
        jaccard = len(intersection) / len(union)
        
        # 考虑值的相似度
        value_similarity = 0.0
        for key in intersection:
            val1 = dict1[key]
            val2 = dict2[key]
            if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                if val1 == 0 and val2 == 0:
                    value_similarity += 1.0
                else:
                    max_val = max(abs(val1), abs(val2))
                    value_similarity += 1.0 - abs(val1 - val2) / max_val if max_val > 0 else 0
        else:
                value_similarity += 1.0 if val1 == val2 else 0.0
        
        if intersection:
            value_similarity /= len(intersection)
        
        # 综合相似度
        return (jaccard + value_similarity) / 2
    
    def _calculate_numeric_similarity(self, val1: float, val2: float) -> float:
        """计算数值相似度"""
        if val1 == val2:
            return 1.0
        
        # 使用相对误差计算相似度
        max_val = max(abs(val1), abs(val2))
        if max_val == 0:
            return 1.0
        
        error = abs(val1 - val2) / max_val
        return max(0.0, 1.0 - error)
    
    # 为后期AI升级预留的接口
    def set_ai_interface(self, ai_interface):
        """设置AI接口（为后期升级预留）"""
        self.ai_interface = ai_interface
        self.ai_available = ai_interface is not None
        logger.info(f"AI接口已设置，可用性: {self.ai_available}")
    
    def _try_ai_similarity(self, query_content: str, top_k: int = 5, threshold: float = 0.3) -> List[Dict]:
        """尝试使用AI进行相似度检测（为后期升级预留）"""
        if not self.ai_available or not self.ai_interface:
            return []
        
        try:
            return self.ai_interface.find_similar_documents(query_content, top_k, threshold)
        except Exception as e:
            logger.warning(f"AI相似度检测失败: {e}")
            return []
    
    def load_or_create_index(self):
        """加载或创建索引"""
        os.makedirs(self.index_path, exist_ok=True)
        metadata_file = os.path.join(self.index_path, 'metadata.json')
        
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self.document_metadata = json.load(f)
                logger.info(f"已加载相似度索引，包含 {len(self.document_metadata)} 个文档")
            except Exception as e:
                logger.error(f"加载索引失败: {e}")
                self.document_metadata = {}
        else:
            self.document_metadata = {}
            logger.info("创建新的相似度索引")
    
    def add_document(self, doc_id: str, content: str, metadata: Dict = None) -> bool:
        """添加文档到索引"""
        try:
            # 提取增强特征
            features = self._extract_text_features(content)
            if not features:
                logger.warning(f"无法提取文档 {doc_id} 的特征")
                return False
            
            # 保存文档元数据
            self.document_metadata[doc_id] = {
                'content_preview': content[:500],
                'features': features,
                'metadata': metadata or {},
                'created_at': timezone.now().isoformat()
            }
            
            # 保存到Django缓存
            cache_key = f"doc_features:{doc_id}"
            cache.set(cache_key, features, timeout=3600)
            
            # 保存到磁盘
            self.save_index()
            
            logger.info(f"文档 {doc_id} 已添加到清理版相似度索引")
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
            
            # 优先尝试AI检测（如果可用）
            if self.ai_available:
                ai_results = self._try_ai_similarity(query_content, top_k, threshold)
                if ai_results:
                    logger.info("使用AI相似度检测")
                    return ai_results
            
            # 使用增强基础算法
            return self._find_similar_enhanced(query_content, top_k, threshold)
                
        except Exception as e:
            logger.error(f"搜索相似文档失败: {e}")
            return []
    
    def _find_similar_enhanced(self, query_content: str, top_k: int, threshold: float) -> List[Dict]:
        """使用增强算法查找相似文档"""
        try:
            if not self.document_metadata:
                logger.warning("没有文档数据，无法进行相似度检测")
                return []
            
            # 提取查询特征
            query_features = self._extract_text_features(query_content)
            if not query_features:
                logger.warning("无法提取查询特征")
                return []
            
            # 计算相似度
            similarities = []
            for doc_id, doc_data in self.document_metadata.items():
                doc_features = doc_data.get('features', {})
                similarity = self._calculate_enhanced_similarity(query_features, doc_features)
                
                if similarity >= threshold:
                    similarities.append({
                        'doc_id': doc_id,
                        'similarity_score': similarity,
                        'content_preview': doc_data.get('content_preview', ''),
                        'metadata': doc_data.get('metadata', {}),
                        'created_at': doc_data.get('created_at', '')
                    })
            
            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            results = similarities[:top_k]
            
            # 缓存结果
            cache_key = f"similarity:{hashlib.md5(query_content.encode()).hexdigest()}"
            cache.set(cache_key, results, timeout=1800)
            
            logger.info(f"找到 {len(results)} 个相似文档（清理版基础算法）")
            return results
            
        except Exception as e:
            logger.error(f"增强搜索相似文档失败: {e}")
            return []
    
    def save_index(self):
        """保存索引到磁盘"""
        try:
            metadata_file = os.path.join(self.index_path, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
            
            logger.info("清理版相似度索引已保存到磁盘")
        except Exception as e:
            logger.error(f"保存索引失败: {e}")
    
    def get_index_stats(self) -> Dict:
        """获取索引统计信息"""
        return {
            'total_documents': len(self.document_metadata),
            'algorithm_type': 'Clean Basic',
            'ai_available': self.ai_available,
            'features_extracted': len(self.document_metadata) > 0,
            'last_updated': timezone.now().isoformat()
        }
    
    def get_algorithm_info(self) -> Dict:
        """获取算法信息"""
        return {
            'current_algorithm': 'Clean Basic Similarity',
            'features': [
                'Text Statistics',
                'Word Frequency Analysis',
                'Semantic Keywords',
                'Topic Words',
                'Language Detection',
                'Structure Analysis',
                'Sentiment Analysis'
            ],
            'ai_upgrade_ready': True,
            'ai_interface_available': self.ai_available
        }

# 全局实例
similarity_service_simple = SimilarityServiceSimple()
