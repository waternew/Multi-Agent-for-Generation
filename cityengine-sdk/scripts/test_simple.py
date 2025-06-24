#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试脚本 - 使用parthenon.rpk
"""

import os
import pyprt

def test_simple_generation():
    """简单测试"""
    
    print("🧪 简单PyPRT测试")
    print("=" * 30)
    
    try:
        # 创建一个简单的矩形几何体
        coords = [0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10, 0]  # 3D坐标
        initial_shape = pyprt.InitialShape(coords)
        print(f"✅ 创建初始形状: {len(coords)//3} 个点")
        
        # 使用parthenon.rpk
        rpk_path = "E:/HKUST/202505_Agent_Urban_Design/cityengine-sdk/data/parthenon.rpk"
        
        if not os.path.exists(rpk_path):
            print(f"❌ RPK文件不存在: {rpk_path}")
            return False
        
        # 设置属性 - parthenon.rpk的默认属性
        shape_attributes = [{}]  # 使用默认属性
        
        # 设置编码器
        encoder_id = "com.esri.prt.codecs.OBJEncoder"
        encoder_options = {}
        
        print("🔄 生成模型...")
        model_generator = pyprt.ModelGenerator([initial_shape])
        models = model_generator.generate_model(shape_attributes, rpk_path, encoder_id, encoder_options)
        
        print(f"✅ 生成了 {len(models)} 个模型")
        
        # 保存结果
        output_dir = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images"
        os.makedirs(output_dir, exist_ok=True)
        
        for i, model in enumerate(models):
            try:
                model_data = model.get_data()
                if model_data:
                    output_path = os.path.join(output_dir, f"test_simple_{i}.obj")
                    with open(output_path, 'wb') as f:
                        f.write(model_data)
                    print(f"✅ 保存: {output_path}")
                else:
                    print(f"⚠️  模型 {i} 没有数据")
            except Exception as e:
                print(f"❌ 保存失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_generation() 