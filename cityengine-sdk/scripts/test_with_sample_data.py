#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例数据测试CityEngine SDK
"""

import os
import pyprt

def test_with_sample_data():
    """使用示例数据测试"""
    
    print("🏙️ CityEngine SDK 示例数据测试")
    print("=" * 40)
    
    try:
        print("🔄 开始测试...")
        
        # 创建简单的几何体（矩形）
        coords = [0, 0, 10, 0, 10, 10, 0, 10]
        print(f"📐 创建坐标: {coords}")
        
        initial_shape = pyprt.InitialShape(coords)
        print(f"✅ 创建初始形状成功")
        
        # 使用你的CGA规则
        cga_rule = """
        version "2024.1"

        @StartRule

        Lot -->
            extrude(height)
            comp(f) { 
                top : Roof  
            }

        attr height = 30
            
        Roof -->
            color("#87CEFA")
        """
        
        print("✅ 加载CGA规则")
        print(f"CGA规则内容:\n{cga_rule}")
        
        # 创建模型生成器
        print("🔄 创建模型生成器...")
        model_generator = pyprt.ModelGenerator([initial_shape])
        print("✅ 模型生成器创建成功")
        
        # 设置CGA规则
        print("🔄 设置CGA规则...")
        model_generator.set_rule_file(cga_rule)
        print("✅ CGA规则设置成功")
        
        # 设置编码器为OBJ格式
        print("🔄 设置编码器...")
        encoder = pyprt.Encoder('com.esri.prt.codecs.OBJEncoder')
        print("✅ 编码器设置成功")
        
        # 生成模型
        print("🔄 正在生成3D模型...")
        result = model_generator.generate_model(encoder)
        print(f"✅ 模型生成成功，结果长度: {len(result)}")
        
        # 保存结果
        output_dir = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images"
        print(f"📁 输出目录: {output_dir}")
        
        os.makedirs(output_dir, exist_ok=True)
        print("✅ 输出目录创建/确认成功")
        
        output_path = os.path.join(output_dir, "test_building.obj")
        print(f"📄 输出文件: {output_path}")
        
        with open(output_path, 'w') as f:
            f.write(result)
        
        print(f"✅ 3D模型保存成功: {output_path}")
        print("🎉 测试完成！")
        
        return True
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 开始执行测试脚本...")
    success = test_with_sample_data()
    if success:
        print("✅ 测试成功完成")
    else:
        print("❌ 测试失败") 