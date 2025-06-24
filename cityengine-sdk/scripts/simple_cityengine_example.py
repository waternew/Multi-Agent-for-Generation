#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的CityEngine SDK示例
演示如何使用PyPRT处理几何体和CGA规则
"""

import os
import pyprt

def create_simple_building():
    """创建一个简单的建筑示例"""
    
    print("🏙️ CityEngine SDK 简单示例")
    print("=" * 40)
    
    try:
        # 初始化PyPRT
        print("🔄 初始化PyPRT...")
        pyprt.initialize_prt()
        print("✅ PyPRT初始化成功")
        
        # 创建一个简单的矩形几何体（建筑基底）
        # 使用InitialShape创建几何体
        coords = [0, 0, 10, 0, 10, 10, 0, 10]
        
        # 创建PyPRT初始形状
        initial_shape = pyprt.InitialShape(coords)
        print(f"✅ 创建初始形状: {coords}")
        
        # 创建一个简单的CGA规则
        cga_rule = """
        @StartRule
        attr height = 20
        
        @StartRule
        extrude(height)
        split(y) { 1 : color(1, 0, 0) | 1 : color(0, 1, 0) | 1 : color(0, 0, 1) }
        """
        
        print("✅ 创建CGA规则")
        
        # 创建模型生成器
        model_generator = pyprt.ModelGenerator([initial_shape])
        
        # 设置CGA规则
        model_generator.set_rule_file(cga_rule)
        
        # 设置编码器为OBJ格式
        encoder = pyprt.Encoder('com.esri.prt.codecs.OBJEncoder')
        
        # 生成模型
        print("🔄 正在生成3D模型...")
        result = model_generator.generate_model(encoder)
        
        # 保存结果
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "simple_building.obj")
        with open(output_path, 'w') as f:
            f.write(result)
        
        print(f"✅ 3D模型生成成功: {output_path}")
        print("🎉 示例完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    finally:
        # 清理资源
        try:
            pyprt.shutdown_prt()
            print("✅ PyPRT已关闭")
        except:
            pass

def test_pyprt_installation():
    """测试PyPRT安装"""
    print("🧪 测试PyPRT安装...")
    
    try:
        import pyprt
        print("✅ PyPRT模块导入成功")
        
        # 尝试初始化
        pyprt.initialize_prt()
        print("✅ PyPRT初始化成功")
        
        # 尝试创建初始形状
        coords = [0, 0, 1, 0, 1, 1, 0, 1]
        initial_shape = pyprt.InitialShape(coords)
        print("✅ 初始形状创建成功")
        
        pyprt.shutdown_prt()
        print("✅ PyPRT关闭成功")
        
        return True
        
    except Exception as e:
        print(f"❌ PyPRT测试失败: {e}")
        return False

if __name__ == "__main__":
    # 首先测试安装
    if test_pyprt_installation():
        print("\n" + "="*50)
        # 运行示例
        create_simple_building()
    else:
        print("❌ PyPRT安装有问题，请检查安装") 