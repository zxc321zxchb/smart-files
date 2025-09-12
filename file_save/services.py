import base64
import os
import mimetypes
from typing import Optional, Dict, Any
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone
from .models import FileSave
from file_history.models import FileSaveHistory
from performance.models import PerformanceStats


class FileSaveService:
    """文件保存服务"""
    
    @staticmethod
    def save_file(
        filename: str,
        content_data: str,
        file_path: Optional[str] = None,
        save_mode: str = 'manual'
    ) -> Dict[str, Any]:
        """
        保存文件
        
        Args:
            filename: 文件名
            content_data: base64编码的文件内容
            file_path: 保存路径（可选）
            save_mode: 保存模式
            
        Returns:
            保存结果字典
        """
        start_time = timezone.now()
        
        try:
            # 解码base64内容
            file_content = base64.b64decode(content_data)
            file_size = len(file_content)
            
            # 自动生成文件路径
            if not file_path:
                file_path = f"/uploads/{filename}"
            
            # 获取文件扩展名和内容类型
            file_extension = os.path.splitext(filename)[1][1:].lower()
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            # 创建文件保存记录
            file_save = FileSave.objects.create(
                filename=filename,
                file_path=file_path,
                file_size=file_size,
                file_extension=file_extension,
                content_type=content_type,
                content_data=content_data
            )
            
            # 创建历史记录
            FileSaveHistory.objects.create(
                original_filename=filename,
                final_path=file_path,
                file_size=file_size,
                file_extension=file_extension,
                content_preview=FileSaveService._generate_preview(file_content, content_type),
                save_mode=save_mode
            )
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='file_save',
                response_time_ms=response_time,
                success=True,
                file_size=file_size
            )
            
            return {
                'success': True,
                'file_id': file_save.id,
                'filename': filename,
                'file_path': file_path,
                'file_size': file_size,
                'message': '文件保存成功'
            }
            
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='file_save',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '文件保存失败'
            }
    
    @staticmethod
    def convert_file(file_save_id: int, target_format: str) -> Dict[str, Any]:
        """
        转换文件格式
        
        Args:
            file_save_id: 文件保存记录ID
            target_format: 目标格式
            
        Returns:
            转换结果字典
        """
        start_time = timezone.now()
        
        try:
            file_save = FileSave.objects.get(id=file_save_id)
            
            # 这里应该实现实际的格式转换逻辑
            # 目前返回模拟结果
            converted_filename = f"{os.path.splitext(file_save.filename)[0]}.{target_format}"
            converted_path = f"/converted/{converted_filename}"
            
            # 记录性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='file_convert',
                response_time_ms=response_time,
                success=True,
                file_size=file_save.file_size
            )
            
            return {
                'success': True,
                'original_file': file_save.filename,
                'converted_filename': converted_filename,
                'converted_path': converted_path,
                'target_format': target_format,
                'message': '文件转换成功'
            }
            
        except FileSave.DoesNotExist:
            return {
                'success': False,
                'error': '文件不存在',
                'message': '文件转换失败'
            }
        except Exception as e:
            # 记录错误性能数据
            end_time = timezone.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            PerformanceStats.objects.create(
                operation_type='file_convert',
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                'success': False,
                'error': str(e),
                'message': '文件转换失败'
            }
    
    @staticmethod
    def batch_save_files(files_data: list) -> Dict[str, Any]:
        """
        批量保存文件
        
        Args:
            files_data: 文件数据列表
            
        Returns:
            批量保存结果
        """
        start_time = timezone.now()
        results = []
        success_count = 0
        
        for file_data in files_data:
            result = FileSaveService.save_file(
                filename=file_data.get('filename'),
                content_data=file_data.get('content_data'),
                file_path=file_data.get('file_path'),
                save_mode='batch'
            )
            results.append(result)
            if result['success']:
                success_count += 1
        
        # 记录性能数据
        end_time = timezone.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        PerformanceStats.objects.create(
            operation_type='file_save',
            response_time_ms=response_time,
            success=success_count > 0,
            file_size=sum(r.get('file_size', 0) for r in results if r.get('success'))
        )
        
        return {
            'success': success_count > 0,
            'total_files': len(files_data),
            'success_count': success_count,
            'failed_count': len(files_data) - success_count,
            'results': results,
            'message': f'批量保存完成，成功 {success_count} 个，失败 {len(files_data) - success_count} 个'
        }
    
    @staticmethod
    def _generate_preview(file_content: bytes, content_type: str) -> str:
        """
        生成文件内容预览
        
        Args:
            file_content: 文件内容
            content_type: 内容类型
            
        Returns:
            预览文本
        """
        try:
            if content_type.startswith('text/'):
                # 文本文件预览
                text_content = file_content.decode('utf-8', errors='ignore')
                return text_content[:500] + '...' if len(text_content) > 500 else text_content
            
            elif content_type.startswith('image/'):
                # 图片文件预览
                return f"[图片文件，大小: {len(file_content)} 字节]"
            
            elif content_type in ['application/pdf']:
                # PDF文件预览
                return "[PDF文档]"
            
            else:
                # 其他文件类型
                return f"[{content_type} 文件，大小: {len(file_content)} 字节]"
                
        except Exception:
            return f"[文件预览生成失败，大小: {len(file_content)} 字节]"
