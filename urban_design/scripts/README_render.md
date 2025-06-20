# OBJ文件布局渲染脚本使用说明

## 文件说明

- `render_obj_blender.py`: 主要的渲染脚本，可以在Blender中运行
- `run_render.bat`: 批处理文件，用于自动启动Blender并运行脚本
- `render_obj.py`: 原始脚本（不能在普通Python环境中运行）

## 使用方法

### 方法1: 使用批处理文件（推荐）

1. **修改Blender路径**：
   - 打开 `run_render.bat` 文件
   - 修改 `BLENDER_PATH` 变量为你的Blender安装路径
   - 常见的路径：
     - `"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"`
     - `"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"`
     - `"C:\Program Files\Blender Foundation\Blender 3.5\blender.exe"`

2. **确保OBJ文件存在**：
   - `E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/generated_model_0.obj`
   - `E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/generated_model_1.obj`
   - `E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/generated_model_2.obj`

3. **运行批处理文件**：
   - 双击 `run_render.bat`
   - 脚本会自动启动Blender并执行渲染

### 方法2: 手动在Blender中运行

1. **启动Blender**

2. **打开脚本编辑器**：
   - 切换到 "Scripting" 工作区
   - 或者点击顶部菜单 "Editor Type" → "Text Editor"

3. **加载脚本**：
   - 点击 "Open" 按钮
   - 选择 `render_obj_blender.py` 文件

4. **运行脚本**：
   - 点击 "Run Script" 按钮（或按 Alt+P）

### 方法3: 命令行运行

```bash
# 替换为你的Blender路径
"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe" --background --python render_obj_blender.py
```

## 脚本功能

1. **导入多个OBJ文件**：同时导入三个建筑模型
2. **统一缩放**：将所有对象缩放为0.1倍
3. **智能相机设置**：
   - 自动计算最佳相机位置
   - 假设建筑面向Y轴
   - 相机在Y轴正方向拍摄
4. **专业光照**：
   - 主光源：太阳光（暖色调）
   - 填充光：面光源（冷色调）
   - 天空环境：Hosek-Wilkie天空模型
5. **材质系统**：为每个建筑分配不同颜色
6. **高质量渲染**：
   - Cycles渲染引擎
   - 256采样数
   - 1920x1080分辨率
   - JPEG格式，95%质量

## 输出文件

渲染结果将保存为：
`E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_render.jpg`

## 故障排除

### 1. "找不到Blender"错误
- 检查 `run_render.bat` 中的Blender路径是否正确
- 确保Blender已正确安装

### 2. "输入文件不存在"错误
- 检查OBJ文件路径是否正确
- 确保文件确实存在

### 3. 渲染质量不佳
- 可以修改脚本中的 `samples` 参数（默认256）
- 增加采样数会提高质量但增加渲染时间

### 4. 相机角度不理想
- 可以修改脚本中的相机位置计算逻辑
- 调整 `camera_distance` 和相机偏移参数

## 自定义修改

如果需要修改渲染参数，可以编辑 `render_obj_blender.py` 文件中的以下部分：

- **分辨率**：修改 `resolution_x` 和 `resolution_y`
- **采样数**：修改 `cycles.samples`
- **输出格式**：修改 `file_format` 和 `quality`
- **相机参数**：修改 `camera.data.lens` 和相机位置计算
- **光照参数**：修改光源的 `energy` 和 `color` 值 