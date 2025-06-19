import bpy
import os
import sys

def render_obj(obj_path, output_image):
    # 清除默认对象
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # 导入 obj - 使用选项来保持网格分离
    bpy.ops.import_scene.obj(
        filepath=obj_path,
        use_edges=True,
        use_smooth_groups=True,
        use_split_objects=True,  # 按对象分割
        use_split_groups=True,   # 按组分割
        use_groups_as_vgroups=False,
        use_image_search=True,
        split_mode='ON',         # 强制分割
        global_clamp_size=0.0
    )
    
    # 获取导入的对象
    imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    print(f"导入了 {len(imported_objects)} 个网格对象")
    
    if not imported_objects:
        print("警告: 没有找到网格对象")
        return
    
    # 详细分析每个网格对象
    print("\n=== 网格对象详细信息 ===")
    total_vertices = 0
    total_faces = 0
    
    for i, obj in enumerate(imported_objects):
        mesh = obj.data
        print(f"对象 {i+1}: '{obj.name}'")
        print(f"  - 顶点数: {len(mesh.vertices)}")
        print(f"  - 面数: {len(mesh.polygons)}")
        print(f"  - 位置: {obj.location}")
        print(f"  - 尺寸: {obj.dimensions}")
        
        # 计算实际几何体尺寸
        if len(mesh.vertices) > 0:
            vert_coords = [vert.co for vert in mesh.vertices]
            x_coords = [v[0] for v in vert_coords]
            y_coords = [v[1] for v in vert_coords]
            z_coords = [v[2] for v in vert_coords]
            
            x_range = max(x_coords) - min(x_coords)
            y_range = max(y_coords) - min(y_coords)
            z_range = max(z_coords) - min(z_coords)
            
            print(f"  - 几何体尺寸: X={x_range:.2f}, Y={y_range:.2f}, Z={z_range:.2f}")
            print(f"  - 坐标范围: X[{min(x_coords):.2f}, {max(x_coords):.2f}], Y[{min(y_coords):.2f}, {max(y_coords):.2f}], Z[{min(z_coords):.2f}, {max(z_coords):.2f}]")
            
            total_vertices += len(mesh.vertices)
            total_faces += len(mesh.polygons)
    
    print(f"\n总计: {total_vertices} 个顶点, {total_faces} 个面")
    print("=== 详细信息结束 ===\n")
    
    # 选择所有网格对象并居中
    for obj in imported_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = imported_objects[0]
    
    # 居中所有对象
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bpy.ops.object.location_clear()
    
    # 计算模型边界框
    bbox_min = [float('inf')] * 3
    bbox_max = [float('-inf')] * 3
    
    for obj in imported_objects:
        for vertex in obj.bound_box:
            for i in range(3):
                bbox_min[i] = min(bbox_min[i], vertex[i])
                bbox_max[i] = max(bbox_max[i], vertex[i])
    
    model_size = [bbox_max[i] - bbox_min[i] for i in range(3)]
    print(f"模型尺寸: {model_size}")
    print(f"模型边界: 最小={bbox_min}, 最大={bbox_max}")

    # 为每个对象设置材质，让它们更容易看到
    print("设置材质...")
    for i, obj in enumerate(imported_objects):
        print(f"----- 设置对象 {i} 的材质 -----")
        # 创建新材质
        mat_name = f"Building_Material_{i}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        
        # 清除默认节点
        nodes.clear()
        
        # 添加漫反射节点
        diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        diffuse.location = (0, 0)
        
        # 设置不同的颜色，让每个建筑更容易区分
        import random
        random.seed(i)  # 使用索引作为种子，确保颜色一致
        r = random.uniform(0.3, 0.8)
        g = random.uniform(0.3, 0.8)
        b = random.uniform(0.3, 0.8)
        diffuse.inputs[0].default_value = (r, g, b, 1.0)
        
        # 添加输出节点
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        
        # 连接节点
        mat.node_tree.links.new(diffuse.outputs[0], output.inputs[0])
        
        # 设置材质属性
        mat.blend_method = 'OPAQUE'  # 确保不透明
        mat.shadow_method = 'OPAQUE'  # 确保阴影不透明
        
        # 将材质分配给对象
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        
        # 重新计算法线，确保面朝上
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)  # 确保法线朝外
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)

    # 添加相机
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    # 设置为正交相机
    camera.data.type = 'ORTHO'
    
    # 针对平面模型进行特殊处理
    max_size = max(model_size)
    print(f"最大模型尺寸: {max_size}")
    
    # 如果模型是平面的（Y轴很小），使用特殊设置
    if model_size[1] < 1.0:  # Y轴高度很小
        print("检测到平面模型，使用平面模型设置")
        # 尝试更激进的相机设置
        camera.data.ortho_scale = max_size * 1.8  # 进一步减小视野
        camera.location = (0, 0, max_size * 1.5)  # 进一步减小相机距离
        # 稍微倾斜相机角度，让平面更容易看到
        camera.rotation_euler = (0.01, 0, 0)  # 增加倾斜角度
    elif max_size > 1000:  # 地理坐标系统
        print("检测到大坐标模型，使用地理坐标设置")
        camera.data.ortho_scale = max_size * 10.0
        camera.location = (0, 0, max_size * 50)
        camera.rotation_euler = (0, 0, 0)
    else:  # 普通模型
        print("使用普通模型设置")
        camera.data.ortho_scale = max_size * 3.0
        camera.location = (0, 0, max_size * 10)
        camera.rotation_euler = (0, 0, 0)
    
    bpy.context.scene.camera = camera
    
    print(f"相机位置: {camera.location}")
    print(f"相机正交缩放: {camera.data.ortho_scale}")
    print(f"相机旋转: {camera.rotation_euler}")
    
    # 计算相机视野范围
    ortho_scale = camera.data.ortho_scale
    print(f"相机视野范围: X={-ortho_scale/2:.2f} 到 {ortho_scale/2:.2f}, Y={-ortho_scale/2:.2f} 到 {ortho_scale/2:.2f}")
    print(f"模型是否在视野内: X轴 {bbox_min[0] >= -ortho_scale/2 and bbox_max[0] <= ortho_scale/2}")
    print(f"模型是否在视野内: Z轴 {bbox_min[2] >= -ortho_scale/2 and bbox_max[2] <= ortho_scale/2}")

    # 添加光照 - 针对平面模型优化
    # 删除默认光源
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)
    
    # 添加主光源 - 从上方照射
    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.object
    sun.location = (0, 0, 10)
    sun.rotation_euler = (0, 0, 0)  # 垂直向下
    sun.data.energy = 2.0  # 增加光照强度
    
    # 添加环境光 - 从侧面照射
    bpy.ops.object.light_add(type='AREA')
    fill_light = bpy.context.object
    fill_light.location = (max_size, 0, max_size)
    fill_light.rotation_euler = (0.785, 0, 0)  # 45度角
    fill_light.data.energy = 1.0  # 增加光照强度
    fill_light.data.size = max_size * 2

    # 设置渲染引擎为Cycles以获得更好的光照效果
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    
    # 设置分辨率
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.image_settings.file_format = 'PNG'

    # 开始渲染
    bpy.context.scene.render.filepath = output_image
    print("开始渲染...")
    bpy.ops.render.render(write_still=True)

    print(f"✅ 图像已保存到: {output_image}")

if __name__ == "__main__":
    # 直接获取参数，跳过脚本名称
    if len(sys.argv) < 3:
        print("错误: 需要2个参数")
        print("用法: blender --background --python script.py <obj_path> <output_image>")
        exit(1)

    obj_path = sys.argv[-2]
    output_image = sys.argv[-1]
    
    # 检查输入文件是否存在
    if not os.path.exists(obj_path):
        print(f"错误: 输入文件不存在: {obj_path}")
        exit(1)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_image)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"正在处理: {obj_path}")
    print(f"输出到: {output_image}")
    
    render_obj(obj_path, output_image)