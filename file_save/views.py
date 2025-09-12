from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import FileSave, FilePath
from .serializers import (
    FileSaveSerializer, 
    FileSaveCreateSerializer, 
    FileSaveListSerializer,
    FilePathSerializer,
    FilePathCreateSerializer,
    FilePathListSerializer
)


class FileSaveViewSet(viewsets.ModelViewSet):
    """文件保存视图集"""
    queryset = FileSave.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['file_extension', 'content_type']
    search_fields = ['filename', 'file_path']
    ordering_fields = ['created_at', 'file_size', 'filename']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'list':
            return FileSaveListSerializer
        elif self.action == 'create':
            return FileSaveCreateSerializer
        return FileSaveSerializer
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 按文件类型过滤
        file_type = self.request.query_params.get('file_type')
        if file_type:
            if file_type == 'image':
                queryset = queryset.filter(
                    file_extension__in=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
                )
            elif file_type == 'document':
                queryset = queryset.filter(
                    file_extension__in=['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
                )
        
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
        """获取文件保存统计信息"""
        from django.db.models import Count, Sum, Avg
        
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
        
        # 按内容类型统计
        content_types = queryset.values('content_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 最近文件
        from django.utils import timezone
        from datetime import timedelta
        recent_files = queryset.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        return Response({
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'avg_size_mb': round(avg_size / (1024 * 1024), 2),
            'file_types': list(file_types),
            'content_types': list(content_types),
            'recent_files': recent_files
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """高级搜索"""
        query = request.query_params.get('q', '')
        if not query:
            return Response({'results': []})
        
        # 多字段搜索
        queryset = self.get_queryset().filter(
            Q(filename__icontains=query) |
            Q(file_path__icontains=query) |
            Q(content_type__icontains=query)
        )
        
        serializer = FileSaveListSerializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': queryset.count()
        })
    
    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """文件格式转换"""
        import os
        import base64
        import subprocess
        import tempfile
        
        file_save = self.get_object()
        target_format = request.data.get('target_format')
        
        if not target_format:
            return Response(
                {'error': '目标格式不能为空'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 解码文件内容
            file_content = base64.b64decode(file_save.content_data)
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.md', delete=False) as temp_md:
                temp_md.write(file_content)
                temp_md_path = temp_md.name
            
            # 生成输出文件路径
            base_name = os.path.splitext(file_save.filename)[0]
            output_filename = f"{base_name}.{target_format}"
            output_path = os.path.join(os.path.dirname(file_save.file_path), output_filename)
            
            # 根据目标格式进行转换
            if target_format == 'docx':
                # 使用pandoc进行转换
                try:
                    result = subprocess.run([
                        'pandoc', temp_md_path, '-o', output_path, 
                        '--from', 'markdown+fenced_code_blocks+fenced_code_attributes+inline_code_attributes', 
                        '--to', 'docx',
                        '--highlight-style', 'pygments',  # 使用pygments高亮样式
                        '--standalone',  # 生成完整文档
                        '--wrap', 'preserve'  # 保持代码换行
                    ], capture_output=True, text=True, timeout=60)  # 增加到60秒
                    
                    if result.returncode == 0:
                        # 转换成功，读取转换后的文件
                        with open(output_path, 'rb') as f:
                            converted_content = f.read()
                        
                        # 创建新的文件记录
                        converted_file = FileSave.objects.create(
                            filename=output_filename,
                            file_path=output_path,
                            file_size=len(converted_content),
                            file_extension=target_format,
                            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                            content_data=base64.b64encode(converted_content).decode('utf-8')
                        )
                        
                        # 清理临时文件
                        os.unlink(temp_md_path)
                        
                        return Response({
                            'message': f'文件 {file_save.filename} 已转换为 {target_format} 格式',
                            'original_file': FileSaveSerializer(file_save).data,
                            'converted_file': FileSaveSerializer(converted_file).data
                        })
                    else:
                        raise Exception(f'Pandoc转换失败: {result.stderr}')
                        
                except subprocess.TimeoutExpired:
                    raise Exception('转换超时')
                except FileNotFoundError:
                    raise Exception('Pandoc未安装，无法进行转换')
                    
            else:
                return Response(
                    {'error': f'不支持的转换格式: {target_format}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            # 清理临时文件
            if 'temp_md_path' in locals() and os.path.exists(temp_md_path):
                os.unlink(temp_md_path)
            
            return Response(
                {'error': f'转换失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_upload(self, request):
        """批量上传文件"""
        files = request.FILES.getlist('files')
        if not files:
            return Response(
                {'error': '没有上传文件'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        for file in files:
            # 处理每个文件
            file_data = {
                'filename': file.name,
                'file_path': f'/uploads/{file.name}',
                'file_size': file.size,
                'content_type': file.content_type,
                'content_data': 'base64_encoded_content'  # 实际应该编码文件内容
            }
            
            serializer = FileSaveCreateSerializer(data=file_data)
            if serializer.is_valid():
                file_save = serializer.save()
                results.append(FileSaveSerializer(file_save).data)
            else:
                results.append({
                    'filename': file.name,
                    'error': serializer.errors
                })
        
        return Response({
            'message': f'批量上传完成，共处理 {len(files)} 个文件',
            'results': results
        })


class FilePathViewSet(viewsets.ModelViewSet):
    """文件路径管理视图集"""
    queryset = FilePath.objects.filter(is_active=True)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['path_pattern', 'description']
    ordering_fields = ['usage_count', 'last_used_at', 'created_at', 'path_pattern']
    ordering = ['-usage_count', '-last_used_at', '-created_at']
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'list':
            return FilePathListSerializer
        elif self.action == 'create':
            return FilePathCreateSerializer
        return FilePathSerializer
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        
        # 按分类过滤
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # 按使用频率过滤
        frequent_only = self.request.query_params.get('frequent_only')
        if frequent_only and frequent_only.lower() == 'true':
            queryset = queryset.filter(usage_count__gte=5)
        
        # 按最近使用过滤
        recent_days = self.request.query_params.get('recent_days')
        if recent_days:
            try:
                days = int(recent_days)
                since_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(last_used_at__gte=since_date)
            except ValueError:
                pass
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有分类"""
        categories = [
            {'value': choice[0], 'label': choice[1]} 
            for choice in FilePath.CATEGORY_CHOICES
        ]
        return Response(categories)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取路径统计信息"""
        queryset = self.get_queryset()
        
        # 基础统计
        total_paths = queryset.count()
        active_paths = queryset.filter(is_active=True).count()
        frequent_paths = queryset.filter(usage_count__gte=5).count()
        
        # 按分类统计
        category_stats = queryset.values('category').annotate(
            count=Count('id'),
            total_usage=Count('usage_count')
        ).order_by('-count')
        
        # 最近使用的路径
        recent_paths = queryset.filter(
            last_used_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # 最常用的路径
        top_paths = queryset.order_by('-usage_count')[:5]
        top_paths_data = FilePathListSerializer(top_paths, many=True).data
        
        return Response({
            'total_paths': total_paths,
            'active_paths': active_paths,
            'frequent_paths': frequent_paths,
            'recent_paths': recent_paths,
            'category_stats': list(category_stats),
            'top_paths': top_paths_data
        })
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """获取推荐路径"""
        # 获取最常用的路径
        frequent_paths = self.get_queryset().filter(usage_count__gte=3).order_by('-usage_count')[:10]
        
        # 获取最近使用的路径
        recent_paths = self.get_queryset().filter(
            last_used_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-last_used_at')[:5]
        
        # 获取推荐分类的路径
        recommended_paths = self.get_queryset().filter(category='recommended')[:5]
        
        # 合并并去重
        all_paths = list(frequent_paths) + list(recent_paths) + list(recommended_paths)
        unique_paths = []
        seen_ids = set()
        
        for path in all_paths:
            if path.id not in seen_ids:
                unique_paths.append(path)
                seen_ids.add(path.id)
        
        # 限制返回数量
        unique_paths = unique_paths[:15]
        
        serializer = FilePathListSerializer(unique_paths, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def increment_usage(self, request, pk=None):
        """增加路径使用次数"""
        file_path = self.get_object()
        file_path.increment_usage()
        
        serializer = FilePathSerializer(file_path)
        return Response({
            'message': '使用次数已更新',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建路径"""
        paths_data = request.data.get('paths', [])
        if not paths_data:
            return Response(
                {'error': '没有提供路径数据'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        results = []
        for path_data in paths_data:
            serializer = FilePathCreateSerializer(data=path_data)
            if serializer.is_valid():
                file_path = serializer.save()
                results.append(FilePathSerializer(file_path).data)
            else:
                results.append({
                    'path_pattern': path_data.get('path_pattern', ''),
                    'error': serializer.errors
                })
        
        return Response({
            'message': f'批量创建完成，共处理 {len(paths_data)} 个路径',
            'results': results
        })
    
    @action(detail=False, methods=['delete'])
    def batch_delete(self, request):
        """批量删除路径"""
        path_ids = request.data.get('path_ids', [])
        if not path_ids:
            return Response(
                {'error': '没有提供要删除的路径ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = FilePath.objects.filter(id__in=path_ids).delete()[0]
        
        return Response({
            'message': f'成功删除 {deleted_count} 个路径',
            'deleted_count': deleted_count
        })