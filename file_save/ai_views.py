#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI功能相关的视图
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
import logging
from .similarity_service_simple import similarity_service

logger = logging.getLogger(__name__)

class AIStatusViewSet(ViewSet):
    """AI状态管理视图集"""
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """获取AI功能状态"""
        try:
            ai_status = similarity_service.get_ai_status()
            return Response({
                'success': True,
                'data': ai_status
            })
        except Exception as e:
            logger.error(f"获取AI状态失败: {e}")
            return Response({
                'success': False,
                'message': f'获取AI状态失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def index_stats(self, request):
        """获取相似度索引统计信息"""
        try:
            stats = similarity_service.get_index_stats()
            return Response({
                'success': True,
                'data': stats
            })
        except Exception as e:
            logger.error(f"获取索引统计失败: {e}")
            return Response({
                'success': False,
                'message': f'获取索引统计失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def rebuild_index(self, request):
        """重建相似度索引"""
        try:
            count = similarity_service.rebuild_index()
            return Response({
                'success': True,
                'message': f'索引重建完成，处理了 {count} 个文档'
            })
        except Exception as e:
            logger.error(f"重建索引失败: {e}")
            return Response({
                'success': False,
                'message': f'重建索引失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
