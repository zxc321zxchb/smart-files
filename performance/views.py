from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime
from .models import PerformanceStats
from .serializers import (
    PerformanceStatsSerializer,
    PerformanceStatsCreateSerializer,
    PerformanceStatsListSerializer,
    PerformanceStatsTrendSerializer,
    PerformanceStatsSummarySerializer
)


class PerformanceStatsViewSet(viewsets.ModelViewSet):
    """性能统计视图集"""
    queryset = PerformanceStats.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['operation_type', 'success']
    search_fields = ['error_message']
    ordering_fields = ['created_at', 'response_time_ms']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'list':
            return PerformanceStatsListSerializer
        elif self.action == 'create':
            return PerformanceStatsCreateSerializer
        return PerformanceStatsSerializer
    
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
        
        # 按响应时间过滤
        min_time = self.request.query_params.get('min_time')
        max_time = self.request.query_params.get('max_time')
        if min_time:
            queryset = queryset.filter(response_time_ms__gte=float(min_time))
        if max_time:
            queryset = queryset.filter(response_time_ms__lte=float(max_time))
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取性能统计摘要"""
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            created_at__range=[start_date, end_date]
        )
        
        # 基础统计
        total_operations = queryset.count()
        success_operations = queryset.filter(success=True).count()
        success_rate = (success_operations / total_operations * 100) if total_operations > 0 else 0
        
        # 响应时间统计
        response_stats = queryset.aggregate(
            avg_time=Avg('response_time_ms'),
            max_time=Max('response_time_ms'),
            min_time=Min('response_time_ms')
        )
        
        # 慢操作统计
        slow_operations = queryset.filter(response_time_ms__gt=1000).count()
        
        # 错误操作统计
        error_operations = queryset.filter(success=False).count()
        
        # 按操作类型统计
        operation_types = queryset.values('operation_type').annotate(
            count=Count('id'),
            avg_time=Avg('response_time_ms'),
            success_rate=Avg('success') * 100
        ).order_by('-count')
        
        # 按性能等级统计
        performance_levels = {
            'excellent': queryset.filter(response_time_ms__lt=100).count(),
            'good': queryset.filter(response_time_ms__gte=100, response_time_ms__lt=500).count(),
            'average': queryset.filter(response_time_ms__gte=500, response_time_ms__lt=1000).count(),
            'poor': queryset.filter(response_time_ms__gte=1000).count()
        }
        
        # 最近趋势
        recent_trend = self._get_recent_trend(queryset, days)
        
        return Response({
            'total_operations': total_operations,
            'success_rate': round(success_rate, 2),
            'avg_response_time': round(response_stats['avg_time'] or 0, 2),
            'max_response_time': round(response_stats['max_time'] or 0, 2),
            'min_response_time': round(response_stats['min_time'] or 0, 2),
            'slow_operations': slow_operations,
            'error_operations': error_operations,
            'operation_types': list(operation_types),
            'performance_levels': performance_levels,
            'recent_trend': recent_trend
        })
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """获取性能趋势数据"""
        days = int(request.query_params.get('days', 7))
        operation_type = request.query_params.get('operation_type')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        queryset = self.get_queryset().filter(
            created_at__date__range=[start_date, end_date]
        )
        
        if operation_type:
            queryset = queryset.filter(operation_type=operation_type)
        
        # 按日期统计
        trends = []
        current_date = start_date
        while current_date <= end_date:
            day_queryset = queryset.filter(created_at__date=current_date)
            
            total_ops = day_queryset.count()
            success_ops = day_queryset.filter(success=True).count()
            success_rate = (success_ops / total_ops * 100) if total_ops > 0 else 0
            avg_time = day_queryset.aggregate(avg=Avg('response_time_ms'))['avg'] or 0
            slow_ops = day_queryset.filter(response_time_ms__gt=1000).count()
            
            trends.append({
                'date': current_date.isoformat(),
                'operation_type': operation_type or 'all',
                'total_operations': total_ops,
                'success_rate': round(success_rate, 2),
                'avg_response_time': round(avg_time, 2),
                'slow_operations': slow_ops
            })
            
            current_date += timedelta(days=1)
        
        return Response({
            'period': f'{start_date} 到 {end_date}',
            'operation_type': operation_type or 'all',
            'trends': trends
        })
    
    @action(detail=False, methods=['get'])
    def slow_operations(self, request):
        """获取慢操作列表"""
        limit = int(request.query_params.get('limit', 20))
        threshold = float(request.query_params.get('threshold', 1000))
        
        slow_ops = self.get_queryset().filter(
            response_time_ms__gt=threshold
        ).order_by('-response_time_ms')[:limit]
        
        serializer = PerformanceStatsListSerializer(slow_ops, many=True)
        return Response({
            'threshold': threshold,
            'count': slow_ops.count(),
            'operations': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def error_operations(self, request):
        """获取错误操作列表"""
        limit = int(request.query_params.get('limit', 20))
        
        error_ops = self.get_queryset().filter(
            success=False
        ).order_by('-created_at')[:limit]
        
        serializer = PerformanceStatsListSerializer(error_ops, many=True)
        return Response({
            'count': error_ops.count(),
            'operations': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def record(self, request):
        """记录性能数据"""
        serializer = PerformanceStatsCreateSerializer(data=request.data)
        if serializer.is_valid():
            # 自动设置IP地址
            if not serializer.validated_data.get('ip_address'):
                serializer.validated_data['ip_address'] = self._get_client_ip(request)
            
            # 自动设置用户代理
            if not serializer.validated_data.get('user_agent'):
                serializer.validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
            
            performance_stat = serializer.save()
            return Response(
                PerformanceStatsSerializer(performance_stat).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_recent_trend(self, queryset, days):
        """获取最近趋势数据"""
        trends = []
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            day_queryset = queryset.filter(created_at__date=date)
            
            trends.append({
                'date': date.isoformat(),
                'total_operations': day_queryset.count(),
                'avg_response_time': round(
                    day_queryset.aggregate(avg=Avg('response_time_ms'))['avg'] or 0, 2
                ),
                'success_rate': round(
                    (day_queryset.filter(success=True).count() / day_queryset.count() * 100) 
                    if day_queryset.count() > 0 else 0, 2
                )
            })
        
        return list(reversed(trends))
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip