from typing import Dict, Any, List, Optional
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta, datetime
from .models import FileSaveHistory
from performance.models import PerformanceStats


class FileSaveHistoryService:
    """文件保存历史服务"""
    
    @staticmethod
    def search_history(
        query: Optional[str] = None,
        file_extension: Optional[str] = None,
        save_mode: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        path_category: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        搜索历史记录
        
        Args:
            query: 搜索关键词
            file_extension: 文件扩展名
            save_mode: 保存模式
            date_from: 开始日期
            date_to: 结束日期
            path_category: 路径分类
            limit: 结果限制
            
        Returns:
            搜索结果
        """
        start_time = timezone.now()
        
        try:
            queryset = FileSaveHistory.objects.all()
            
            # 应用过滤条件
            if query:
                queryset = queryset.filter(
                    Q(original_filename__icontains=query) |
                    Q(final_path__icontains=query) |
                    Q(content_preview__icontains=query)
                )
            
            if file_extension:
                queryset = queryset.filter(file_extension=file_extension)
            
            if save_mode:
                queryset = queryset.filter(save_mode=save_mode)
            
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from.date())
            
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to.date())
            
            if path_category:
                queryset = queryset.filter(path_category=path_category)
            
            # 获取结果
            results = queryset.order_by('-created_at')[:limit]
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='history_query',
                response_time_ms=response_time,
                success=True
            )
            
            return {
                'success': True,
                'count': results.count(),
                'results': list(results.values()),
                'message': f'找到 {results.count()} 条历史记录'
            }
            
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='history_query',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '历史记录搜索失败'
            }
    
    @staticmethod
    def get_statistics(days: int = 30) -> Dict[str, Any]:
        """
        获取历史记录统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            统计信息
        """
        start_time = timezone.now()
        
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            queryset = FileSaveHistory.objects.filter(
                created_at__range=[start_date, end_date]
            )
            
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
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'avg_file_size_mb': round(avg_size / (1024 * 1024), 2),
                'file_types': list(file_types),
                'save_modes': list(save_modes),
                'path_categories': list(path_categories),
                'recent_files': recent_files
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
                'message': '统计信息获取失败'
            }
    
    @staticmethod
    def get_trends(days: int = 30) -> Dict[str, Any]:
        """
        获取保存趋势数据
        
        Args:
            days: 趋势天数
            
        Returns:
            趋势数据
        """
        start_time = timezone.now()
        
        try:
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days)
            
            queryset = FileSaveHistory.objects.filter(
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
                'message': '趋势数据获取失败'
            }
    
    @staticmethod
    def get_popular_paths(limit: int = 10) -> Dict[str, Any]:
        """
        获取热门保存路径
        
        Args:
            limit: 结果限制
            
        Returns:
            热门路径数据
        """
        start_time = timezone.now()
        
        try:
            popular_paths = FileSaveHistory.objects.values('final_path').annotate(
                count=Count('id'),
                total_size=Sum('file_size')
            ).order_by('-count')[:limit]
            
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
                'popular_paths': list(popular_paths),
                'message': f'获取到 {len(popular_paths)} 个热门路径'
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
                'message': '热门路径获取失败'
            }
    
    @staticmethod
    def export_history(
        format_type: str = 'json',
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        导出历史记录
        
        Args:
            format_type: 导出格式 (json, csv)
            filters: 过滤条件
            
        Returns:
            导出结果
        """
        start_time = timezone.now()
        
        try:
            queryset = FileSaveHistory.objects.all()
            
            # 应用过滤条件
            if filters:
                if filters.get('date_from'):
                    queryset = queryset.filter(created_at__date__gte=filters['date_from'])
                if filters.get('date_to'):
                    queryset = queryset.filter(created_at__date__lte=filters['date_to'])
                if filters.get('file_extension'):
                    queryset = queryset.filter(file_extension=filters['file_extension'])
                if filters.get('save_mode'):
                    queryset = queryset.filter(save_mode=filters['save_mode'])
            
            if format_type == 'json':
                # JSON导出
                data = list(queryset.values())
                export_result = {
                    'format': 'json',
                    'count': len(data),
                    'data': data
                }
            elif format_type == 'csv':
                # CSV导出（这里应该实现实际的CSV生成逻辑）
                export_result = {
                    'format': 'csv',
                    'count': queryset.count(),
                    'download_url': '/api/history/export/download/'
                }
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='data_export',
                response_time_ms=response_time,
                success=True
            )
            
            return {
                'success': True,
                'export_result': export_result,
                'message': f'成功导出 {export_result["count"]} 条历史记录'
            }
            
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='data_export',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '历史记录导出失败'
            }
