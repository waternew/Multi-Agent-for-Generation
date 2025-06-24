#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CityEngine SDK Python处理器 - 直接使用CGA文件
"""

import os
import sys
import json
from pathlib import Path
import pyprt
import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np

class CityEngineProcessor:
    def __init__(self):
        """初始化CityEngine处理器"""
        self.initialized = False
        try:
            self.initialized = True
            print("✅ PyPRT初始化成功")
        except Exception as e:
            print(f"❌ PyPRT初始化失败: {e}")
    
    def load_shp_file(self, shp_path):
        """加载SHP文件并转换为PyPRT初始形状"""
        try:
            if not os.path.exists(shp_path):
                print(f"❌ SHP文件不存在: {shp_path}")
                return []
            
            shx_path = shp_path.replace('.shp', '.shx')
            if not os.path.exists(shx_path):
                print(f"❌ 缺少SHX文件: {shx_path}")
                return []
            
            gdf = gpd.read_file(shp_path)
            print(f"✅ 成功加载SHP文件: {shp_path}")
            print(f"   包含 {len(gdf)} 个要素")
            
            initial_shapes = []
            for idx, row in gdf.iterrows():
                geom = row.geometry
                if geom.geom_type == 'Polygon':
                    coords = list(geom.exterior.coords)
                    if coords[0] == coords[-1]:
                        coords = coords[:-1]
                    coords_3d = []
                    for x, y in coords:
                        coords_3d.extend([x, y, 0.0])
                    try:
                        initial_shape = pyprt.InitialShape(coords_3d)
                        initial_shapes.append(initial_shape)
                        print(f"   ✅ 要素 {idx}: 转换成功 ({len(coords)} 个点)")
                    except Exception as e:
                        print(f"   ❌ 要素 {idx}: 转换失败 - {e}")
                        continue
                    
            print(f"✅ 成功转换了 {len(initial_shapes)} 个初始形状")
            return initial_shapes
            
        except Exception as e:
            print(f"❌ 加载SHP文件失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def load_cga_file(self, cga_path):
        """加载CGA文件内容"""
        try:
            if not os.path.exists(cga_path):
                print(f"❌ CGA文件不存在: {cga_path}")
                return None
                
            with open(cga_path, 'r', encoding='utf-8') as f:
                cga_content = f.read()
            print(f"✅ 成功加载CGA文件: {cga_path}")
            return cga_content
        except Exception as e:
            print(f"❌ 加载CGA文件失败: {e}")
            return None
    
    def create_temp_rpk(self, cga_content, temp_rpk_path):
        """创建临时RPK文件"""
        try:
            import zipfile
            
            # 创建临时RPK文件
            with zipfile.ZipFile(temp_rpk_path, 'w') as zip_file:
                # 添加CGA规则文件
                zip_file.writestr('rule.cga', cga_content)
                
                # 添加RPK配置文件
                rpk_config = '''<?xml version="1.0" encoding="UTF-8"?>
<RulePackage>
    <RuleFile>rule.cga</RuleFile>
    <StartRule>Lot</StartRule>
</RulePackage>'''
                zip_file.writestr('rules/rule.xml', rpk_config)
            
            print(f"✅ 创建临时RPK文件: {temp_rpk_path}")
            return True
            
        except Exception as e:
            print(f"❌ 创建临时RPK文件失败: {e}")
            return False
    
    def generate_3d_model(self, initial_shapes, cga_path, output_dir, attributes=None):
        """生成3D模型"""
        if not self.initialized:
            print("❌ PyPRT未初始化")
            return False
        
        try:
            # 加载CGA文件
            cga_content = self.load_cga_file(cga_path)
            if not cga_content:
                return False
            
            # 创建临时RPK文件
            temp_rpk_path = os.path.join(output_dir, "temp_rule.rpk")
            if not self.create_temp_rpk(cga_content, temp_rpk_path):
                return False
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 设置编码器选项
            encoder_id = "com.esri.prt.codecs.OBJEncoder"
            encoder_options = {}
            
            # 设置属性
            if attributes is None:
                default_attributes = {'height': 30.0}
            else:
                default_attributes = attributes
            
            shape_attributes = [default_attributes for _ in initial_shapes]
            
            print("🔄 正在生成3D模型...")
            print(f"   CGA文件: {cga_path}")
            print(f"   临时RPK: {temp_rpk_path}")
            print(f"   初始形状数量: {len(initial_shapes)}")
            print(f"   编码器: {encoder_id}")
            print(f"   输出目录: {output_dir}")
            print(f"   使用属性: {default_attributes}")
            
            # 生成模型
            model_generator = pyprt.ModelGenerator(initial_shapes)
            models = model_generator.generate_model(shape_attributes, temp_rpk_path, encoder_id, encoder_options)
            
            print(f"✅ 生成了 {len(models)} 个模型")
            
            # 检查生成结果
            if len(models) == 0:
                print("⚠️  警告：没有生成任何模型")
                return False
            
            # 保存结果
            for i, model in enumerate(models):
                try:
                    data = model.get_data()
                    if data:
                        output_path = os.path.join(output_dir, f"generated_{i}.obj")
                        with open(output_path, 'wb') as f:
                            f.write(data)
                        print(f"✅ 模型保存成功: {output_path}")
                    else:
                        print(f"⚠️  模型 {i} 没有数据")
                except Exception as e:
                    print(f"❌ 保存模型 {i} 失败: {e}")
            
            # 清理临时文件
            try:
                os.remove(temp_rpk_path)
                print("✅ 清理临时RPK文件")
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"❌ 生成3D模型失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_files(self, shp_path, cga_path, output_dir, attributes=None):
        """处理SHP和CGA文件"""
        print("🚀 开始处理CityEngine文件...")
        
        # 加载SHP文件
        initial_shapes = self.load_shp_file(shp_path)
        if not initial_shapes:
            print("❌ 没有可用的初始形状")
            return False
        
        # 生成3D模型
        success = self.generate_3d_model(initial_shapes, cga_path, output_dir, attributes)
        
        if success:
            print("🎉 处理完成！")
        else:
            print("❌ 处理失败")
        
        return success

def main():
    """主函数"""
    print("🏙️ CityEngine SDK Python处理器 (CGA版本)")
    print("=" * 50)
    
    # 创建处理器
    processor = CityEngineProcessor()
    
    if not processor.initialized:
        print("❌ 无法初始化PyPRT，请检查安装")
        return
    
    # 给定路径
    shp_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data_shp/site01_utm_final/site01_utm_final.shp"
    cga_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/data/rule1.cga"
    output_dir = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images"
    
    # 根据你的CGA规则设置属性
    attributes = {
        'height': 30.0  # 对应CGA中的 attr height = 30
    }
    
    print("🔄 开始处理文件...")
    print(f"   使用属性: {attributes}")
    
    # 处理文件
    processor.process_files(shp_path, cga_path, output_dir, attributes)

if __name__ == "__main__":
    main() 