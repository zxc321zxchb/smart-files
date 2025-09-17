@echo off
echo === Windows Pandoc下载器 ===
echo.

REM 创建pandoc目录
if not exist "pandoc" mkdir pandoc

REM 检查是否已存在pandoc.exe
if exist "pandoc\pandoc.exe" (
    echo pandoc.exe已存在，跳过下载
    pandoc\pandoc.exe --version
    goto :end
)

echo 正在下载pandoc...
echo.

REM 下载pandoc
curl -L -o pandoc.zip "https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-windows-x86_64.zip"

if %errorlevel% neq 0 (
    echo 下载失败，尝试使用代理...
    curl -L -o pandoc.zip "https://fastgh.discoverlife.top/https://github.com/jgm/pandoc/releases/download/3.1.9/pandoc-3.1.9-windows-x86_64.zip"
)

if %errorlevel% neq 0 (
    echo 下载失败，请手动下载pandoc
    echo 访问: https://pandoc.org/installing.html
    goto :end
)

echo 下载完成，正在解压...

REM 解压文件
powershell -command "Expand-Archive -Path pandoc.zip -DestinationPath temp_pandoc -Force"

REM 复制pandoc.exe到pandoc目录
copy "temp_pandoc\pandoc-3.1.9\pandoc.exe" "pandoc\pandoc.exe"

REM 清理临时文件
rmdir /s /q temp_pandoc
del pandoc.zip

echo.
echo 测试pandoc...
pandoc\pandoc.exe --version

if %errorlevel% equ 0 (
    echo.
    echo ✅ pandoc安装成功！
) else (
    echo.
    echo ❌ pandoc安装失败
)

:end
pause
