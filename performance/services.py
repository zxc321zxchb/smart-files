from typing import Dict, Any, List, Optional
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta, datetime
from .models import PerformanceStats


class PerformanceService:
    """性能监控服务"""
    
    @staticmethod
    def record_performance(
        operation_type: str,
        response_time_ms: float,
        success: bool,
        error_message: Optional[str] = None,
        file_size: Optional[int] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        记录性能数据
        
        Args:
            operation_type: 操作类型
            response_time_ms: 响应时间(毫秒)
            success: 是否成功
            error_message: 错误信息
            file_size: 文件大小
            user_agent: 用户代理
            ip_address: IP地址
            
        Returns:
            记录结果
        """
        try:
            performance_stat = PerformanceStats.objects.create(
                operation_type=operation_type,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                file_size=file_size,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            return {
                'success': True,
                'performance_id': performance_stat.id,
                'message': '性能数据记录成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '性能数据记录失败'
            }
    
    @staticmethod
    def get_performance_summary(days: int = 7) -> Dict[str, Any]:
        """
        获取性能统计摘要
        
        Args:
            days: 统计天数
            
        Returns:
            性能摘要
        """
        start_time = timezone.now()
        
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            queryset = PerformanceStats.objects.filter(
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
            recent_trend = PerformanceService._get_recent_trend(queryset, days)
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=True
            )
            
            return {
                'success': True,
                'period': f'{start_date.date()} 到 {end_date.date()}',
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
            }
            
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '性能摘要获取失败'
            }
    
    @staticmethod
    def get_performance_trends(
        days: int = 7,
        operation_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取性能趋势数据
        
        Args:
            days: 趋势天数
            operation_type: 操作类型过滤
            
        Returns:
            趋势数据
        """
        start_time = timezone.now()
        
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            queryset = PerformanceStats.objects.filter(
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
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=True
            )
            
            return {
                'success': True,
                'period': f'{start_date} 到 {end_date}',
                'operation_type': operation_type or 'all',
                'trends': trends
            }
            
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '性能趋势获取失败'
            }
    
    @staticmethod
    def get_slow_operations(
        threshold: float = 1000,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        获取慢操作列表
        
        Args:
            threshold: 响应时间阈值(毫秒)
            limit: 结果限制
            
        Returns:
            慢操作列表
        """
        start_time = timezone.now()
        
        try:
            slow_ops = PerformanceStats.objects.filter(
                response_time_ms__gt=threshold
            ).order_by('-response_time_ms')[:limit]
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=True
            )
            
            return {
                'success': True,
                'threshold': threshold,
                'count': slow_ops.count(),
                'operations': list(slow_ops.values()),
                'message': f'找到 {slow_ops.count()} 个慢操作'
            }
            
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '慢操作获取失败'
            }
    
    @staticmethod
    def get_error_operations(limit: int = 20) -> Dict[str, Any]:
        """
        获取错误操作列表
        
        Args:
            limit: 结果限制
            
        Returns:
            错误操作列表
        """
        start_time = timezone.now()
        
        try:
            error_ops = PerformanceStats.objects.filter(
                success=False
            ).order_by('-created_at')[:limit]
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=True
            )
            
            return {
                'success': True,
                'count': error_ops.count(),
                'operations': list(error_ops.values()),
                'message': f'找到 {error_ops.count()} 个错误操作'
            }
            
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='statistics',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '错误操作获取失败'
            }
    
    @staticmethod
    def _get_recent_trend(queryset, days: int) -> List[Dict[str, Any]]:
        """
        获取最近趋势数据
        
        Args:
            queryset: 查询集
            days: 天数
            
        Returns:
            趋势数据列表
        """
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
