#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试PyEncoder生成的模型对象
"""

import pyprt

def debug_pyencoder():
    """调试PyEncoder"""
    print("🔍 调试PyEncoder生成的模型对象")
    print("=" * 40)
    
    try:
        # 创建一个简单的正方形
        coords = [0, 0, 0, 10, 0, 0, 10, 10, 0, 0, 10, 0]
        initial_shape = pyprt.InitialShape(coords)
        print(f"✅ 创建初始形状: {len(coords)//3} 个点")
        
        # 使用官方示例的RPK
        rpk_path = "E:/HKUST/202505_Agent_Urban_Design/pyprt-examples/data/extrusion_rule.rpk"
        
        # 设置编码器
        encoder_id = "com.esri.pyprt.PyEncoder"
        encoder_options = {
            'emitGeometry': True, 
            'emitReport': True
        }
        
        # 生成模型
        model_generator = pyprt.ModelGenerator([initial_shape])
        models = model_generator.generate_model([{}], rpk_path, encoder_id, encoder_options)
        
        print(f"✅ 生成了 {len(models)} 个模型")
        
        if len(models) > 0:
            model = models[0]
            print(f"\n📋 模型对象类型: {type(model)}")
            print(f"📋 模型对象方法:")
            
            # 查看所有方法
            methods = [method for method in dir(model) if not method.startswith('_')]
            for method in methods:
                print(f"   - {method}")
            
            # 尝试获取几何体数据
            print(f"\n🔍 尝试获取几何体数据:")
            try:
                vertices = model.get_vertices()
                print(f"   ✅ get_vertices(): {len(vertices)} 个顶点")
                print(f"      前3个顶点: {vertices[:9] if len(vertices) >= 9 else vertices}")
            except Exception as e:
                print(f"   ❌ get_vertices() 失败: {e}")
            
            try:
                indices = model.get_indices()
                print(f"   ✅ get_indices(): {len(indices)} 个索引")
                print(f"      前6个索引: {indices[:6] if len(indices) >= 6 else indices}")
            except Exception as e:
                print(f"   ❌ get_indices() 失败: {e}")
            
            try:
                report = model.get_report()
                print(f"   ✅ get_report(): {len(report)} 个报告项")
                print(f"      报告内容: {report}")
            except Exception as e:
                print(f"   ❌ get_report() 失败: {e}")
            
            # 尝试保存为OBJ格式
            print(f"\n💾 尝试保存为OBJ格式:")
            try:
                # 使用OBJ编码器重新生成
                obj_encoder_id = "com.esri.prt.codecs.OBJEncoder"
                obj_encoder_options = {}
                
                obj_models = model_generator.generate_model([{}], rpk_path, obj_encoder_id, obj_encoder_options)
                print(f"   ✅ OBJ编码器生成了 {len(obj_models)} 个模型")
                
                if len(obj_models) > 0:
                    obj_data = obj_models[0].get_data()
                    if obj_data:
                        with open("debug_model.obj", 'wb') as f:
                            f.write(obj_data)
                        print(f"   ✅ 保存OBJ文件: debug_model.obj")
                    else:
                        print(f"   ❌ OBJ模型没有数据")
                else:
                    print(f"   ❌ OBJ编码器没有生成模型")
                    
            except Exception as e:
                print(f"   ❌ OBJ编码器失败: {e}")
                
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_pyencoder() 