#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试RPK文件是否正确
"""

import os
import zipfile
import pyprt

def test_rpk_file(rpk_path):
    """测试RPK文件"""
    print(f"🧪 测试RPK文件: {rpk_path}")
    print("=" * 50)
    
    # 1. 检查RPK文件是否存在
    if not os.path.exists(rpk_path):
        print(f"❌ RPK文件不存在: {rpk_path}")
        return False
    
    # 2. 检查RPK文件内容
    try:
        with zipfile.ZipFile(rpk_path, 'r') as zip_file:
            file_list = zip_file.namelist()
            print(f"✅ RPK文件内容:")
            for file in file_list:
                print(f"   - {file}")
            
            # 检查是否有rule.cga文件
            if 'rule.cga' in file_list:
                print("✅ 找到rule.cga文件")
                # 读取rule.cga内容
                with zip_file.open('rule.cga') as f:
                    cga_content = f.read().decode('utf-8')
                    print(f"CGA内容:\n{cga_content}")
            else:
                print("❌ 没有找到rule.cga文件")
                return False
    except Exception as e:
        print(f"❌ 读取RPK文件失败: {e}")
        return False
    
    # 3. 测试简单的几何体
    print("\n🔄 测试简单几何体...")
    try:
        # 创建一个简单的矩形
        coords = [0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10, 0]
        initial_shape = pyprt.InitialShape(coords)
        print(f"✅ 创建初始形状: {len(coords)//3} 个点")
        
        # 设置属性
        shape_attributes = [{'height': 30.0}]
        
        # 设置编码器
        encoder_id = "com.esri.prt.codecs.OBJEncoder"
        encoder_options = {}
        
        # 生成模型
        model_generator = pyprt.ModelGenerator([initial_shape])
        models = model_generator.generate_model(shape_attributes, rpk_path, encoder_id, encoder_options)
        
        print(f"✅ 生成了 {len(models)} 个模型")
        
        if len(models) > 0:
            print("🎉 RPK文件工作正常！")
            return True
        else:
            print("❌ RPK文件无法生成模型")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # 测试你的RPK文件
    rpk_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/data/rule1.rpk"
    test_rpk_file(rpk_path) 