@echo off
echo 正在启动Blender并运行渲染脚本...

REM 请根据你的Blender安装路径修改下面的路径
REM 常见的Blender安装路径：
REM "C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"
REM "C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"
REM "C:\Program Files\Blender Foundation\Blender 3.5\blender.exe"

set BLENDER_PATH="C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"

REM 检查Blender是否存在
if not exist %BLENDER_PATH% (
    echo 错误: 找不到Blender，请检查路径: %BLENDER_PATH%
    echo 请修改此批处理文件中的BLENDER_PATH变量为你的Blender安装路径
    pause
    exit /b 1
)

REM 运行Blender并执行Python脚本
%BLENDER_PATH% --background --python "%~dp0render_obj_blender.py"

echo 渲染完成！
pause 