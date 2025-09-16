from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class FilePath(models.Model):
    """文件路径管理模型"""
    CATEGORY_CHOICES = [
        ('default', '默认'),
        ('user_defined', '用户定义'),
        ('auto_generated', '自动生成'),
        ('recommended', '推荐'),
        ('frequent', '常用'),
    ]
    
    path_pattern = models.CharField(max_length=500, unique=True, verbose_name="路径模式")
    description = models.CharField(max_length=200, blank=True, verbose_name="描述")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='user_defined', verbose_name="分类")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")
    usage_count = models.PositiveIntegerField(default=0, verbose_name="使用次数")
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name="最后使用时间")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'file_paths'
        ordering = ['-usage_count', '-last_used_at', '-created_at']
        verbose_name = "文件路径"
        verbose_name_plural = "文件路径"
    
    def __str__(self):
        return f"{self.path_pattern} ({self.get_category_display()})"
    
    def increment_usage(self):
        """增加使用次数并更新最后使用时间"""
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.save(update_fields=['usage_count', 'last_used_at'])
    
    @property
    def is_frequent(self):
        """判断是否为常用路径"""
        return self.usage_count >= 5


class FileSave(models.Model):
    """文件保存模型"""
    filename = models.CharField(max_length=255, verbose_name="文件名")
    file_path = models.TextField(verbose_name="文件路径")
    file_size = models.BigIntegerField(verbose_name="文件大小(字节)")
    file_extension = models.CharField(max_length=20, blank=True, verbose_name="文件扩展名")
    content_type = models.CharField(max_length=100, verbose_name="内容类型")
    content_data = models.TextField(verbose_name="文件内容(base64编码)")
    file_path_ref = models.ForeignKey(FilePath, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联路径")
    is_indexed = models.BooleanField(default=False, verbose_name="是否已索引")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        db_table = 'file_saves'
        ordering = ['-created_at']
        verbose_name = "文件保存记录"
        verbose_name_plural = "文件保存记录"
    
    def __str__(self):
        return f"{self.filename} ({self.file_size} bytes)"
    
    @property
    def file_size_mb(self):
        """返回文件大小(MB)"""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_image(self):
        """判断是否为图片文件"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        return self.file_extension.lower() in image_extensions
    
    @property
    def is_document(self):
        """判断是否为文档文件"""
        doc_extensions = ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt']
        return self.file_extension.lower() in doc_extensions


class FileSaveHistory(models.Model):
    """文件保存历史记录模型"""
    SAVE_MODE_CHOICES = [
        ('normal', '普通保存'),
        ('append_to_similar', '追加到相似文件'),
        ('smart_save', '智能保存'),
    ]
    
    original_filename = models.CharField(max_length=255, verbose_name="原始文件名")
    final_path = models.TextField(verbose_name="最终保存路径")
    file_size = models.BigIntegerField(verbose_name="文件大小(字节)")
    file_extension = models.CharField(max_length=20, blank=True, verbose_name="文件扩展名")
    content_preview = models.TextField(blank=True, verbose_name="内容预览")
    save_mode = models.CharField(max_length=20, choices=SAVE_MODE_CHOICES, default='normal', verbose_name="保存模式")
    source_url = models.URLField(blank=True, verbose_name="来源URL")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        db_table = 'file_save_histories'
        ordering = ['-created_at']
        verbose_name = "文件保存历史"
        verbose_name_plural = "文件保存历史"
    
    def __str__(self):
        return f"{self.original_filename} ({self.get_save_mode_display()})"
    
    @property
    def file_size_mb(self):
        """返回文件大小(MB)"""
        return round(self.file_size / (1024 * 1024), 2)