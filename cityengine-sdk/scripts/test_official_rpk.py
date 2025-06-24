#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试官方 RPK 文件
"""

import os
import pyprt

def test_official_rpk():
    """测试官方 RPK 文件"""
    print("🧪 测试官方 RPK 文件")
    print("=" * 30)
    
    try:
        # 创建输出目录
        output_dir = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images"
        os.makedirs(output_dir, exist_ok=True)
        
        # 使用官方的 RPK 文件
        rpk_path = "E:/HKUST/202505_Agent_Urban_Design/pyprt-examples/data/extrusion_rule.rpk"
        
        if not os.path.exists(rpk_path):
            print(f"❌ RPK文件不存在: {rpk_path}")
            return False
        
        # 创建一个简单的正方形几何体
        coords = [0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10, 0]
        initial_shape = pyprt.InitialShape(coords)
        print(f"✅ 创建初始形状: {len(coords)//3} 个点")
        
        # 设置属性 - 官方示例使用空属性
        shape_attributes = [{}]
        
        # 设置编码器
        encoder_id = "com.esri.prt.codecs.OBJEncoder"
        encoder_options = {
            'outputPath': output_dir,
            'baseName': 'test_official'
        }
        
        print("🔄 生成模型...")
        model_generator = pyprt.ModelGenerator([initial_shape])
        models = model_generator.generate_model(shape_attributes, rpk_path, encoder_id, encoder_options)
        
        print(f"✅ 生成了 {len(models)} 个模型")
        
        # 检查输出文件
        import glob
        obj_files = glob.glob(os.path.join(output_dir, "test_official*.obj"))
        if obj_files:
            print(f"✅ 成功生成OBJ文件:")
            for obj_file in obj_files:
                file_size = os.path.getsize(obj_file)
                print(f"   - {os.path.basename(obj_file)} ({file_size} 字节)")
                
                # 显示文件内容的前几行
                with open(obj_file, 'r') as f:
                    lines = f.readlines()
                    print(f"   文件内容预览:")
                    for i, line in enumerate(lines[:10]):
                        print(f"     {i+1}: {line.strip()}")
        else:
            print("❌ 没有找到生成的OBJ文件")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_official_rpk() 