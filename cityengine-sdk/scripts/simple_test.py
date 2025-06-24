#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简单的PyPRT测试
"""

import pyprt

def simple_test():
    """最简单的测试"""
    print("🧪 最简单的PyPRT测试")
    print("=" * 30)
    
    try:
        # 创建一个简单的正方形
        coords = [0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10, 0]
        initial_shape = pyprt.InitialShape(coords)
        print(f"✅ 创建初始形状: {len(coords)//3} 个点")
        
        # 使用你的CGA规则创建临时RPK
        import zipfile
        import os
        
        temp_rpk = "temp_simple.rpk"
        cga_content = '''version "2024.1"

@StartRule

Lot -->
    extrude(height)
    comp(f) { 
        top : Roof  
    }

attr height = 30

Roof -->
    color("#87CEFA")'''
        
        # 创建临时RPK
        with zipfile.ZipFile(temp_rpk, 'w') as zip_file:
            zip_file.writestr('rule.cga', cga_content)
            rpk_config = '''<?xml version="1.0" encoding="UTF-8"?>
<RulePackage>
    <RuleFile>rule.cga</RuleFile>
    <StartRule>Lot</StartRule>
</RulePackage>'''
            zip_file.writestr('rules/rule.xml', rpk_config)
        
        print(f"✅ 创建临时RPK: {temp_rpk}")
        
        # 设置属性
        shape_attributes = [{'height': 30.0}]
        
        # 设置编码器
        encoder_id = "com.esri.prt.codecs.OBJEncoder"
        encoder_options = {}
        
        # 生成模型
        model_generator = pyprt.ModelGenerator([initial_shape])
        models = model_generator.generate_model(shape_attributes, temp_rpk, encoder_id, encoder_options)
        
        print(f"✅ 生成了 {len(models)} 个模型")
        
        if len(models) > 0:
            print("🎉 测试成功！")
            # 保存模型
            for i, model in enumerate(models):
                data = model.get_data()
                if data:
                    with open(f"test_model_{i}.obj", 'wb') as f:
                        f.write(data)
                    print(f"✅ 保存模型: test_model_{i}.obj")
        else:
            print("❌ 测试失败：没有生成模型")
        
        # 清理
        try:
            os.remove(temp_rpk)
        except:
            pass
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test() 