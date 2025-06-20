import bpy
import os
import sys
import mathutils

def render_multiple_objs(obj_paths, output_image):
    # 清除默认对象
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

    # 导入所有OBJ文件
    all_imported_objects = []
    
    for obj_path in obj_paths:
        print(f"正在导入: {obj_path}")
        
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
        
        # 获取刚导入的对象
        imported_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj not in all_imported_objects]
        all_imported_objects.extend(imported_objects)
        print(f"从 {obj_path} 导入了 {len(imported_objects)} 个网格对象")
    
    if not all_imported_objects:
        print("警告: 没有找到网格对象")
        return
    
    # 缩放所有对象为0.1倍
    print("缩放所有对象为0.1倍...")
    for obj in all_imported_objects:
        obj.scale = (0.1, 0.1, 0.1)
        # 应用缩放变换
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.select_set(False)
    
    # 详细分析每个网格对象
    print("\n=== 网格对象详细信息 ===")
    total_vertices = 0
    total_faces = 0
    
    for i, obj in enumerate(all_imported_objects):
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
    
    # 计算所有对象的整体包围盒
    bbox_min = [float('inf')] * 3
    bbox_max = [float('-inf')] * 3
    
    for obj in all_imported_objects:
        # 计算对象的世界坐标包围盒
        for vertex in obj.bound_box:
            world_vertex = obj.matrix_world @ mathutils.Vector(vertex)
            for i in range(3):
                bbox_min[i] = min(bbox_min[i], world_vertex[i])
                bbox_max[i] = max(bbox_max[i], world_vertex[i])
    
    model_size = [bbox_max[i] - bbox_min[i] for i in range(3)]
    center = [(bbox_min[i] + bbox_max[i]) / 2 for i in range(3)]
    
    print(f"整体包围盒:")
    print(f"  - 中心: {center}")
    print(f"  - 尺寸: {model_size}")
    print(f"  - 范围: X[{bbox_min[0]:.2f}, {bbox_max[0]:.2f}], Y[{bbox_min[1]:.2f}, {bbox_max[1]:.2f}], Z[{bbox_min[2]:.2f}, {bbox_max[2]:.2f}]")
    
    # 设置相机 - 假设建筑面向Y轴，相机在Y轴正方向
    print("设置相机...")
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = 'PERSP'  # 使用透视相机以获得更好的效果
    
    # 相机位置：在Y轴正方向，稍微向上偏移
    camera_distance = max(model_size[0], model_size[2]) * 2.0  # 距离是建筑宽度的2倍
    camera.location = (center[0], bbox_max[1] + camera_distance, center[2] + model_size[2] * 0.5)
    
    # 相机朝向：看向建筑群中心
    direction = center - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    
    # 设置相机视野
    camera.data.lens = 35  # 35mm镜头
    camera.data.clip_start = 0.1
    camera.data.clip_end = 1000.0
    
    bpy.context.scene.camera = camera
    
    print(f"相机位置: {camera.location}")
    print(f"相机朝向: {camera.rotation_euler}")
    
    # 设置光源
    print("设置光源...")
    
    # 主光源 - 太阳光
    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.object
    sun.location = (center[0], center[1] - 10, center[2] + 20)
    sun.rotation_euler = (math.radians(45), 0, math.radians(-45))  # 45度角照射
    sun.data.energy = 3.0
    sun.data.color = (1.0, 0.95, 0.9)  # 暖色调
    
    # 填充光 - 环境光
    bpy.ops.object.light_add(type='AREA')
    fill_light = bpy.context.object
    fill_light.location = (center[0] - 15, center[1] + 5, center[2] + 10)
    fill_light.rotation_euler = (0, math.radians(90), 0)
    fill_light.data.energy = 1.0
    fill_light.data.color = (0.9, 0.95, 1.0)  # 冷色调
    fill_light.data.size = 10.0
    
    # 为每个对象设置材质
    print("设置材质...")
    for i, obj in enumerate(all_imported_objects):
        print(f"设置对象 {i+1} 的材质...")
        mat_name = f"Building_Material_{i}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # 创建漫反射着色器
        diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        diffuse.location = (0, 0)
        
        # 随机颜色，但保持建筑感
        import random
        random.seed(i)
        r = random.uniform(0.4, 0.8)
        g = random.uniform(0.4, 0.8)
        b = random.uniform(0.4, 0.8)
        diffuse.inputs[0].default_value = (r, g, b, 1.0)
        
        # 创建输出节点
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        
        # 连接节点
        mat.node_tree.links.new(diffuse.outputs[0], output.inputs[0])
        mat.blend_method = 'OPAQUE'
        mat.shadow_method = 'OPAQUE'
        
        # 应用材质到对象
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        
        # 确保法线方向正确
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)
    
    # 设置渲染参数
    print("设置渲染参数...")
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 256  # 增加采样数以获得更好的质量
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.image_settings.quality = 95
    bpy.context.scene.render.filepath = output_image
    
    # 设置世界环境
    world = bpy.context.scene.world
    world.use_nodes = True
    world_nodes = world.node_tree.nodes
    world_nodes.clear()
    
    # 创建天空纹理
    sky_texture = world_nodes.new(type='ShaderNodeTexSky')
    sky_texture.location = (0, 0)
    sky_texture.sky_type = 'HOSEK_WILKIE'
    sky_texture.sun_elevation = 0.5
    sky_texture.sun_rotation = 0.0
    sky_texture.altitude = 0.0
    sky_texture.air_density = 1.0
    sky_texture.dust_density = 1.0
    
    # 创建背景节点
    background = world_nodes.new(type='ShaderNodeBackground')
    background.location = (300, 0)
    background.inputs[1].default_value = 0.5  # 强度
    
    # 创建输出节点
    world_output = world_nodes.new(type='ShaderNodeOutputWorld')
    world_output.location = (600, 0)
    
    # 连接节点
    world.node_tree.links.new(sky_texture.outputs[0], background.inputs[0])
    world.node_tree.links.new(background.outputs[0], world_output.inputs[0])
    
    print("开始渲染...")
    bpy.ops.render.render(write_still=True)
    print(f"✅ 布局图已保存到: {output_image}")

if __name__ == "__main__":
    # 定义OBJ文件路径
    obj_paths = [
        "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/generated_model_0.obj",
        "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/generated_model_1.obj",
        "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/generated_model_2.obj"
    ]
    
    output_image = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_render.jpg"
    
    # 检查输入文件是否存在
    for obj_path in obj_paths:
        if not os.path.exists(obj_path):
            print(f"错误: 输入文件不存在: {obj_path}")
            exit(1)
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_image)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("=== 多OBJ文件布局渲染 ===")
    print(f"输入文件:")
    for i, obj_path in enumerate(obj_paths):
        print(f"  {i+1}. {obj_path}")
    print(f"输出文件: {output_image}")
    print("=" * 30)
    
    render_multiple_objs(obj_paths, output_image) 