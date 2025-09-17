from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
import base64
import os
import logging
from .models import FileSave, FilePath, FileSaveHistory
from .serializers import (
    FileSaveSerializer, 
    FileSaveCreateSerializer, 
    FileSaveListSerializer,
    FilePathSerializer,
    FilePathCreateSerializer,
    FilePathListSerializer
)
# 启用简单相似度服务（不依赖numpy，适合PyInstaller打包）
from .similarity_service_simple import similarity_service_simple

logger = logging.getLogger(__name__)


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
    
    def create(self, request, *args, **kwargs):
        """重写create方法，添加相似度索引支持"""
        try:
            # 调用父类的create方法
            response = super().create(request, *args, **kwargs)
            
            # 如果创建成功，将文件添加到相似度索引
            if response.status_code == 201:
                file_data = response.data
                file_id = file_data.get('id')
                
                if file_id:
                    # 获取文件内容
                    try:
                        file_obj = FileSave.objects.get(id=file_id)
                        content_data = file_obj.content_data
                        
                        if content_data:
                            # 解码base64内容
                            import base64
                            content = base64.b64decode(content_data).decode('utf-8')
                            
                            # 添加到相似度索引（如果服务可用）
                            if similarity_service_simple:
                                similarity_service_simple.add_document(
                                    doc_id=str(file_id),
                                    content=content,
                                    metadata={
                                        'filename': file_obj.filename,
                                        'file_path': file_obj.file_path,
                                        'created_at': file_obj.created_at.isoformat()
                                    }
                                )
                            
                            # 更新索引标记
                            file_obj.is_indexed = True
                            file_obj.save()
                            
                            logger.info(f"文件 {file_id} 已添加到相似度索引")
                            
                    except Exception as e:
                        logger.warning(f"添加文件 {file_id} 到相似度索引失败: {e}")
                        # 不影响主要的创建流程
            
            return response
            
        except Exception as e:
            logger.error(f"创建文件失败: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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
    
    def get_pandoc_path(self):
        """获取pandoc可执行文件路径"""
        import sys
        import os
        
        # 如果是PyInstaller打包的环境
        if getattr(sys, 'frozen', False):
            # 获取可执行文件所在目录
            base_path = os.path.dirname(sys.executable)
            
            # 在Windows上查找pandoc.exe
            if sys.platform == 'win32':
                pandoc_path = os.path.join(base_path, 'pandoc.exe')
                if os.path.exists(pandoc_path):
                    return pandoc_path
            else:
                # 在macOS/Linux上查找pandoc
                pandoc_path = os.path.join(base_path, 'pandoc')
                if os.path.exists(pandoc_path):
                    return pandoc_path
        
        # 如果不是打包环境或找不到打包的pandoc，尝试系统PATH中的pandoc
        try:
            result = subprocess.run(['pandoc', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return 'pandoc'
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
            
        return None

    def check_pandoc_available(self):
        """检查pandoc是否可用"""
        pandoc_path = self.get_pandoc_path()
        return pandoc_path is not None

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
        
        # 检查pandoc是否可用
        if not self.check_pandoc_available():
            return Response(
                {'error': 'Pandoc未安装，无法进行转换。请访问 https://pandoc.org/installing.html 下载并安装Pandoc，或使用包管理器安装：choco install pandoc'}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
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
                # 获取pandoc路径
                pandoc_path = self.get_pandoc_path()
                if not pandoc_path:
                    raise Exception('Pandoc未安装，无法进行转换。请访问 https://pandoc.org/installing.html 下载并安装Pandoc，或使用包管理器安装：choco install pandoc')
                
                # 使用pandoc进行转换
                try:
                    result = subprocess.run([
                        pandoc_path, temp_md_path, '-o', output_path, 
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
                    raise Exception('Pandoc未安装，无法进行转换。请访问 https://pandoc.org/installing.html 下载并安装Pandoc，或使用包管理器安装：choco install pandoc')
                    
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
    
    @action(detail=False, methods=['post'])
    def find_similar_files(self, request):
        """查找相似文件"""
        try:
            content = request.data.get('content', '')
            top_k = request.data.get('top_k', 5)
            threshold = request.data.get('threshold', 0.1)  # 降低阈值提高匹配率
            
            if not content:
                return Response({
                    'success': False, 
                    'message': '内容不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 查找相似文件（如果服务可用）
            # similarity_service_simple 已经在模块级别导入
            if similarity_service_simple:
                logger.info(f"开始查找相似文件，内容长度: {len(content)}, 阈值: {threshold}")
                similar_docs = similarity_service_simple.find_similar_documents(
                    query_content=content,
                    top_k=top_k,
                    threshold=threshold
                )
                logger.info(f"找到 {len(similar_docs)} 个相似文档")
            else:
                # 相似度服务不可用，返回空结果
                logger.warning("相似度服务不可用")
                similar_docs = []
            
            # 获取完整文件信息
            results = []
            for doc in similar_docs:
                try:
                    file_obj = FileSave.objects.get(id=doc['doc_id'])
                    results.append({
                        'id': file_obj.id,
                        'filename': file_obj.filename,
                        'file_path': file_obj.file_path,
                        'file_size_mb': file_obj.file_size_mb,
                        'created_at': file_obj.created_at.isoformat(),
                        'similarity_score': doc['similarity_score'],
                        'content_preview': doc['content_preview']
                    })
                except FileSave.DoesNotExist:
                    logger.warning(f"文件 {doc['doc_id']} 不存在，跳过")
                    continue
            
            return Response({
                'success': True,
                'data': results,
                'message': f'找到 {len(results)} 个相似文件'
            })
            
        except Exception as e:
            logger.error(f"查找相似文件失败: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def similarity_debug(self, request):
        """相似度服务调试接口"""
        try:
            # similarity_service_simple 已经在模块级别导入
            if not similarity_service_simple:
                return Response({
                    'success': False,
                    'message': '相似度服务不可用'
                })
            
            # 获取索引统计
            # similarity_service_simple 已经在模块级别导入
            if not similarity_service_simple:
                return Response({
                    'success': False,
                    'message': '相似度服务不可用'
                })
            
            stats = similarity_service_simple.get_index_stats()
            
            # 获取数据库中的文件数量
            from .models import FileSave
            total_files = FileSave.objects.count()
            indexed_files = FileSave.objects.filter(is_indexed=True).count()
            
            return Response({
                'success': True,
                'data': {
                    'index_stats': stats,
                    'database_stats': {
                        'total_files': total_files,
                        'indexed_files': indexed_files,
                        'not_indexed_files': total_files - indexed_files
                    }
                }
            })
        except Exception as e:
            logger.error(f"相似度调试失败: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def rebuild_similarity_index(self, request):
        """重建相似度索引"""
        try:
            # similarity_service_simple 已经在模块级别导入
            if not similarity_service_simple:
                return Response({
                    'success': False,
                    'message': '相似度服务不可用'
                })
            
            # 重建索引
            success_count = similarity_service_simple.rebuild_index_from_database()
            
            return Response({
                'success': True,
                'message': f'索引重建完成，成功处理 {success_count} 个文档',
                'data': {
                    'processed_documents': success_count
                }
            })
        except Exception as e:
            logger.error(f"重建索引失败: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def save_to_similar_file(self, request):
        """保存内容到相似文件"""
        try:
            content = request.data.get('content', '')
            target_file_id = request.data.get('target_file_id')
            url = request.data.get('url', '')
            title = request.data.get('title', '')
            is_selection = request.data.get('is_selection', False)
            
            if not content:
                return Response({
                    'success': False,
                    'message': '内容不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 如果指定了目标文件ID，则追加到该文件
            if target_file_id and is_selection:
                try:
                    target_file = FileSave.objects.get(id=target_file_id)
                    result = self.append_to_file(target_file, content, url, title)
                    return Response(result)
                except FileSave.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '目标文件不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # 否则创建新文件
            result = self.create_new_file(content, url, title, is_selection)
            
            # 将新文件添加到相似度索引（如果服务可用）
            if result['success']:
                # similarity_service_simple 已经在模块级别导入
                if similarity_service_simple:
                    similarity_service_simple.add_document(
                    doc_id=str(result['file_id']),
                    content=content,
                    metadata={
                        'filename': result['filename'],
                        'file_path': result['file_path'],
                        'created_at': timezone.now().isoformat()
                    }
                )
                
                # 更新索引标记
                try:
                    file_obj = FileSave.objects.get(id=result['file_id'])
                    file_obj.is_indexed = True
                    file_obj.save()
                except FileSave.DoesNotExist:
                    pass
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"保存到相似文件失败: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def append_to_file(self, file: FileSave, content: str, url: str, title: str) -> dict:
        """追加内容到文件尾部"""
        try:
            # 解码现有内容
            existing_content = base64.b64decode(file.content_data).decode('utf-8')
            
            # 添加分隔符和元数据
            separator = "\n\n---\n\n"
            metadata = f"**来源**: {title}\n**链接**: {url}\n**时间**: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            new_content = existing_content + separator + metadata + content
            
            # 重新编码为base64
            new_content_b64 = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
            
            # 更新数据库记录
            file.content_data = new_content_b64
            file.file_size = len(new_content.encode('utf-8'))
            file.save()
            
            # 更新本地文件
            if os.path.exists(file.file_path):
                with open(file.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            # 创建历史记录
            FileSaveHistory.objects.create(
                original_filename=f"追加到 {file.filename}",
                final_path=file.file_path,
                file_size=len(content.encode('utf-8')),
                file_extension=file.file_extension,
                content_preview=content[:200] + "..." if len(content) > 200 else content,
                save_mode='append_to_similar'
            )
            
            return {
                'success': True,
                'message': f'内容已追加到文件: {file.filename}',
                'filename': file.filename,
                'file_path': file.file_path,
                'file_id': file.id
            }
            
        except Exception as e:
            logger.error(f"追加文件失败: {e}")
            return {'success': False, 'message': f'追加文件失败: {str(e)}'}
    
    def create_new_file(self, content: str, url: str, title: str, is_selection: bool = False) -> dict:
        """创建新文件"""
        try:
            # 生成文件名
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            prefix = "selection" if is_selection else "document"
            filename = f"{prefix}_{timestamp}.md"
            file_path = f"./uploads/{prefix}s/{filename}"
            
            # 添加元数据
            metadata = f"# {title}\n\n**来源链接**: {url}\n**保存时间**: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n**类型**: {'选区内容' if is_selection else '文档'}\n\n---\n\n"
            full_content = metadata + content
            
            # 编码为base64
            content_b64 = base64.b64encode(full_content.encode('utf-8')).decode('utf-8')
            
            # 创建文件保存记录
            file_save = FileSave.objects.create(
                filename=filename,
                file_path=file_path,
                file_size=len(full_content.encode('utf-8')),
                file_extension='md',
                content_type='text/markdown',
                content_data=content_b64,
                is_indexed=False  # 稍后会在调用方设置为True
            )
            
            # 保存到本地文件
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            return {
                'success': True,
                'message': f'已创建新文件: {filename}',
                'filename': filename,
                'file_path': file_path,
                'file_id': file_save.id
            }
            
        except Exception as e:
            logger.error(f"创建文件失败: {e}")
            return {'success': False, 'message': f'创建文件失败: {str(e)}'}
    
    @action(detail=False, methods=['post'])
    def rebuild_similarity_index(self, request):
        """重建相似度索引"""
        try:
            # similarity_service_simple 已经在模块级别导入
            if not similarity_service_simple:
                return Response({
                    'success': False,
                    'message': '相似度服务不可用'
                })
            
            count = similarity_service_simple.rebuild_index_from_database()
            
            # 更新所有文档的索引标记
            FileSave.objects.filter(
                content_type__in=['text/markdown', 'text/plain']
            ).update(is_indexed=True)
            
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
    
    @action(detail=False, methods=['get'])
    def similarity_index_stats(self, request):
        """获取相似度索引统计信息"""
        try:
            # similarity_service_simple 已经在模块级别导入
            if not similarity_service_simple:
                return Response({
                    'success': False,
                    'message': '相似度服务不可用'
                })
            
            stats = similarity_service_simple.get_index_stats()
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
    
    @action(detail=False, methods=['post'])
    def save_to_similar_file(self, request):
        """保存内容到相似文件"""
        try:
            content = request.data.get('content', '')
            target_file_id = request.data.get('target_file_id')
            url = request.data.get('url', '')
            title = request.data.get('title', '')
            is_selection = request.data.get('is_selection', False)
            
            if not content:
                return Response({
                    'success': False,
                    'message': '内容不能为空'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 如果指定了目标文件ID，则追加到该文件
            if target_file_id and is_selection:
                try:
                    target_file = FileSave.objects.get(id=target_file_id)
                    result = self.append_to_file(target_file, content, url, title)
                    return Response(result)
                except FileSave.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': '目标文件不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
            
            # 否则创建新文件
            result = self.create_new_file(content, url, title, is_selection)
            
            # 将新文件添加到相似度索引（如果服务可用）
            if result['success']:
                # similarity_service_simple 已经在模块级别导入
                if similarity_service_simple:
                    similarity_service_simple.add_document(
                    doc_id=str(result['file_id']),
                    content=content,
                    metadata={
                        'filename': result['filename'],
                        'file_path': result['file_path'],
                        'created_at': timezone.now().isoformat()
                    }
                )
                
                # 更新索引标记
                try:
                    file_obj = FileSave.objects.get(id=result['file_id'])
                    file_obj.is_indexed = True
                    file_obj.save()
                except FileSave.DoesNotExist:
                    pass
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"保存到相似文件失败: {e}")
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def append_to_file(self, file: FileSave, content: str, url: str, title: str) -> dict:
        """追加内容到文件尾部"""
        try:
            # 解码现有内容
            existing_content = base64.b64decode(file.content_data).decode('utf-8')
            
            # 添加分隔符和元数据
            separator = "\n\n---\n\n"
            metadata = f"**来源**: {title}\n**链接**: {url}\n**时间**: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            new_content = existing_content + separator + metadata + content
            
            # 重新编码为base64
            new_content_b64 = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
            
            # 更新数据库记录
            file.content_data = new_content_b64
            file.file_size = len(new_content.encode('utf-8'))
            file.save()
            
            # 更新本地文件
            if os.path.exists(file.file_path):
                with open(file.file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            # 创建历史记录
            FileSaveHistory.objects.create(
                original_filename=f"追加到 {file.filename}",
                final_path=file.file_path,
                file_size=len(content.encode('utf-8')),
                file_extension=file.file_extension,
                content_preview=content[:200] + "..." if len(content) > 200 else content,
                save_mode='append_to_similar'
            )
            
            return {
                'success': True,
                'message': f'内容已追加到文件: {file.filename}',
                'filename': file.filename,
                'file_path': file.file_path,
                'file_id': file.id
            }
            
        except Exception as e:
            logger.error(f"追加文件失败: {e}")
            return {'success': False, 'message': f'追加文件失败: {str(e)}'}
    
    def create_new_file(self, content: str, url: str, title: str, is_selection: bool = False) -> dict:
        """创建新文件"""
        try:
            # 生成文件名
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            prefix = "selection" if is_selection else "document"
            filename = f"{prefix}_{timestamp}.md"
            file_path = f"./uploads/{prefix}s/{filename}"
            
            # 添加元数据
            metadata = f"# {title}\n\n**来源链接**: {url}\n**保存时间**: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}\n**类型**: {'选区内容' if is_selection else '文档'}\n\n---\n\n"
            full_content = metadata + content
            
            # 编码为base64
            content_b64 = base64.b64encode(full_content.encode('utf-8')).decode('utf-8')
            
            # 创建文件保存记录
            file_save = FileSave.objects.create(
                filename=filename,
                file_path=file_path,
                file_size=len(full_content.encode('utf-8')),
                file_extension='md',
                content_type='text/markdown',
                content_data=content_b64,
                is_indexed=False  # 稍后会在调用方设置为True
            )
            
            # 保存到本地文件
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            return {
                'success': True,
                'message': f'已创建新文件: {filename}',
                'filename': filename,
                'file_path': file_path,
                'file_id': file_save.id
            }
            
        except Exception as e:
            logger.error(f"创建文件失败: {e}")
            return {'success': False, 'message': f'创建文件失败: {str(e)}'}
    
    @action(detail=False, methods=['post'])
    def rebuild_similarity_index(self, request):
        """重建相似度索引"""
        try:
            # similarity_service_simple 已经在模块级别导入
            if not similarity_service_simple:
                return Response({
                    'success': False,
                    'message': '相似度服务不可用'
                })
            
            count = similarity_service_simple.rebuild_index_from_database()
            
            # 更新所有文档的索引标记
            FileSave.objects.filter(
                content_type__in=['text/markdown', 'text/plain']
            ).update(is_indexed=True)
            
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
    
    @action(detail=False, methods=['get'])
    def similarity_index_stats(self, request):
        """获取相似度索引统计信息"""
        try:
            # similarity_service_simple 已经在模块级别导入
            if not similarity_service_simple:
                return Response({
                    'success': False,
                    'message': '相似度服务不可用'
                })
            
            stats = similarity_service_simple.get_index_stats()
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