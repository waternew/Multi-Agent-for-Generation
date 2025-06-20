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
    
    # 重新计算包围盒
    bbox_min = [float('inf')] * 3
    bbox_max = [float('-inf')] * 3
    for obj in imported_objects:
        for vertex in obj.bound_box:
            for i in range(3):
                bbox_min[i] = min(bbox_min[i], vertex[i] + obj.location[i])
                bbox_max[i] = max(bbox_max[i], vertex[i] + obj.location[i])
    model_size = [bbox_max[i] - bbox_min[i] for i in range(3)]
    center = [(bbox_min[i] + bbox_max[i]) / 2 for i in range(3)]

    # 平移所有对象，使整体中心到原点
    for obj in imported_objects:
        obj.location.x -= center[0]
        obj.location.y -= center[1]
        obj.location.z -= center[2]

    # 相机
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = 'ORTHO'
    ortho_scale = max(model_size[0], model_size[2]) * 1.1
    camera.data.ortho_scale = ortho_scale
    camera.location = (0, 0, max(model_size[0], model_size[2]) * 2)
    camera.rotation_euler = (0, 0, 0)
    bpy.context.scene.camera = camera

    # 光源
    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.object
    sun.location = (0, 0, max(model_size[0], model_size[2]) * 3)
    sun.rotation_euler = (0, 0, 0)
    sun.data.energy = 2.0

    # 为每个对象设置材质，让它们更容易看到
    print("设置材质...")
    for i, obj in enumerate(imported_objects):
        print(f"----- 设置对象 {i} 的材质 -----")
        mat_name = f"Building_Material_{i}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        diffuse = nodes.new(type='ShaderNodeBsdfDiffuse')
        diffuse.location = (0, 0)
        import random
        random.seed(i)
        r = random.uniform(0.3, 0.8)
        g = random.uniform(0.3, 0.8)
        b = random.uniform(0.3, 0.8)
        diffuse.inputs[0].default_value = (r, g, b, 1.0)
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        mat.node_tree.links.new(diffuse.outputs[0], output.inputs[0])
        mat.blend_method = 'OPAQUE'
        mat.shadow_method = 'OPAQUE'
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        obj.select_set(False)

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = output_image
    print("开始渲染...")
    bpy.ops.render.render(write_still=True)
    print(f"✅ 图像已保存到: {output_image}")
    
if __name__ == "__main__":
    # obj_path = sys.argv[-2]
    # output_image = sys.argv[-1]

    obj_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_obj_0.obj"
    output_image = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_obj.png"
    
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