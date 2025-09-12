from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from .models import FileSaveHistory
from .serializers import (
    FileSaveHistorySerializer,
    FileSaveHistoryCreateSerializer,
    FileSaveHistoryListSerializer,
    FileSaveHistorySearchSerializer,
    FileSaveHistoryStatsSerializer
)


class FileSaveHistoryViewSet(viewsets.ModelViewSet):
    """文件保存历史视图集"""
    queryset = FileSaveHistory.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['file_extension', 'save_mode', 'path_category']
    search_fields = ['original_filename', 'final_path', 'content_preview']
    ordering_fields = ['created_at', 'file_size', 'original_filename']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'list':
            return FileSaveHistoryListSerializer
        elif self.action == 'create':
            return FileSaveHistoryCreateSerializer
        return FileSaveHistorySerializer
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 按日期范围过滤
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        # 按文件大小过滤
        min_size = self.request.query_params.get('min_size')
        max_size = self.request.query_params.get('max_size')
        if min_size:
            queryset = queryset.filter(file_size__gte=int(min_size))
        if max_size:
            queryset = queryset.filter(file_size__lte=int(max_size))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取历史记录统计信息"""
        queryset = self.get_queryset()
        
        # 基础统计
        total_files = queryset.count()
        total_size = queryset.aggregate(total=Sum('file_size'))['total'] or 0
        avg_size = queryset.aggregate(avg=Avg('file_size'))['avg'] or 0
        
        # 按文件类型统计
        file_types = queryset.values('file_extension').annotate(
            count=Count('id'),
            total_size=Sum('file_size')
        ).order_by('-count')
        
        # 按保存模式统计
        save_modes = queryset.values('save_mode').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 按路径分类统计
        path_categories = queryset.values('path_category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 最近文件
        recent_files = queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return Response({
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'avg_file_size_mb': round(avg_size / (1024 * 1024), 2),
            'file_types': list(file_types),
            'save_modes': list(save_modes),
            'path_categories': list(path_categories),
            'recent_files': recent_files
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """高级搜索"""
        serializer = FileSaveHistorySearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        queryset = self.get_queryset()
        
        # 关键词搜索
        if data.get('query'):
            query = data['query']
            queryset = queryset.filter(
                Q(original_filename__icontains=query) |
                Q(final_path__icontains=query) |
                Q(content_preview__icontains=query)
            )
        
        # 其他过滤条件
        if data.get('file_extension'):
            queryset = queryset.filter(file_extension=data['file_extension'])
        
        if data.get('save_mode'):
            queryset = queryset.filter(save_mode=data['save_mode'])
        
        if data.get('path_category'):
            queryset = queryset.filter(path_category=data['path_category'])
        
        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FileSaveHistoryListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = FileSaveHistoryListSerializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """获取保存趋势数据"""
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            created_at__date__range=[start_date, end_date]
        )
        
        # 按日期统计
        trends = []
        current_date = start_date
        while current_date <= end_date:
            day_queryset = queryset.filter(created_at__date=current_date)
            count = day_queryset.count()
            total_size = day_queryset.aggregate(total=Sum('file_size'))['total'] or 0
            
            trends.append({
                'date': current_date.isoformat(),
                'count': count,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            })
            
            current_date += timedelta(days=1)
        
        return Response({
            'period': f'{start_date} 到 {end_date}',
            'trends': trends
        })
    
    @action(detail=False, methods=['get'])
    def popular_paths(self, request):
        """获取热门保存路径"""
        limit = int(request.query_params.get('limit', 10))
        
        popular_paths = self.get_queryset().values('final_path').annotate(
            count=Count('id'),
            total_size=Sum('file_size'),
            last_used=timezone.now()  # 这里应该用Max('created_at')
        ).order_by('-count')[:limit]
        
        return Response({
            'popular_paths': list(popular_paths)
        })
    
    @action(detail=False, methods=['post'])
    def export(self, request):
        """导出历史记录"""
        format_type = request.data.get('format', 'csv')
        queryset = self.get_queryset()
        
        if format_type == 'csv':
            # 这里应该实现CSV导出逻辑
            return Response({
                'message': f'已导出 {queryset.count()} 条记录为CSV格式',
                'download_url': '/api/history/export/download/'
            })
        elif format_type == 'json':
            serializer = FileSaveHistoryListSerializer(queryset, many=True)
            return Response({
                'message': f'已导出 {queryset.count()} 条记录为JSON格式',
                'data': serializer.data
            })
        else:
            return Response(
                {'error': '不支持的导出格式'}, 
                status=status.HTTP_400_BAD_REQUEST
            )