# Windows编码问题修复说明

## 🐛 问题描述

在Windows系统上运行PyInstaller构建时出现编码错误：

```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680' in position 0: character maps to <undefined>
```

## 🔍 问题原因

1. **Windows控制台编码限制**: Windows默认使用CP1252编码，无法显示emoji字符
2. **Python输出编码**: 默认输出编码与系统编码不匹配
3. **Unicode字符**: 构建脚本中使用了emoji字符（🚀、📦等）

## ✅ 解决方案

### 1. 创建Windows兼容构建脚本

创建了 `build-windows.py` 专门处理Windows编码问题：

```python
# 设置Windows编码
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        pass

def print_safe(text):
    """安全打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)
```

### 2. 更新CI构建脚本

更新了 `build-ci.py` 使其跨平台兼容：

```python
# Windows编码设置
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def print_safe(text):
    """安全打印函数，处理编码问题"""
    try:
        print(text)
    except UnicodeEncodeError:
        ascii_text = text.encode('ascii', 'replace').decode('ascii')
        print(ascii_text)
```

### 3. 更新GitHub Actions工作流

修改了 `.github/workflows/build.yml` 使用CI构建脚本：

```yaml
- name: 构建Windows版本
  run: python build-ci.py
```

## 🔧 技术细节

### 编码处理策略

1. **环境变量设置**: `PYTHONIOENCODING=utf-8`
2. **输出流重定向**: 使用UTF-8编码重定向stdout/stderr
3. **安全打印函数**: 捕获编码错误并转换为ASCII
4. **平台检测**: 根据平台选择不同的处理方式

### 兼容性处理

- **Windows**: 使用 `build-windows.py` 或 `build-ci.py`
- **macOS/Linux**: 使用 `build.py` 或 `build-ci.py`
- **CI环境**: 统一使用 `build-ci.py`

## 📁 修改的文件

1. **build.py** - 添加Windows编码支持
2. **build-windows.py** - 新建Windows专用构建脚本
3. **build-ci.py** - 更新CI构建脚本
4. **.github/workflows/build.yml** - 更新工作流配置

## 🧪 测试验证

### 本地测试
```bash
# Windows系统
python build-windows.py

# 其他系统
python build.py
```

### CI测试
```bash
# 推送代码触发GitHub Actions
git add .
git commit -m "Fix Windows encoding issues"
git push origin main
```

## 🎯 预期结果

修复后，Windows构建应该能够：
- ✅ 正常显示构建进度信息
- ✅ 成功生成可执行文件
- ✅ 通过GitHub Actions测试
- ✅ 创建正确的启动脚本

## 🔄 后续优化

1. **统一构建脚本**: 考虑将功能合并到单一脚本
2. **更好的错误处理**: 增强错误提示和调试信息
3. **性能优化**: 减少不必要的编码转换
4. **文档完善**: 添加更多平台特定的说明

## 📞 故障排除

如果仍然遇到编码问题：

1. **检查Python版本**: 确保使用Python 3.8+
2. **验证环境变量**: 确认 `PYTHONIOENCODING` 设置正确
3. **查看构建日志**: 检查GitHub Actions的详细输出
4. **本地测试**: 在Windows系统上本地测试构建脚本

---

**修复完成！** 🎉

现在Windows构建应该能够正常工作，不再出现编码错误。
