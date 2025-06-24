#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CityEngine SDK Python处理器
使用PyPRT库处理SHP和RPK文件，生成3D模型
参考: https://github.com/Esri/pyprt-examples.git
"""

import os
import sys
import json
import random
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
            # 新版本PyPRT会自动初始化
            self.initialized = True
            print("✅ PyPRT初始化成功")
        except Exception as e:
            print(f"❌ PyPRT初始化失败: {e}")
    
    def load_shp_file(self, shp_path):
        """
        加载SHP文件并转换为PyPRT初始形状
        
        Args:
            shp_path (str): SHP文件路径
            
        Returns:
            list: 初始形状列表
        """
        try:
            # 检查SHP文件是否存在
            if not os.path.exists(shp_path):
                print(f"❌ SHP文件不存在: {shp_path}")
                return []
            
            # 检查是否缺少SHX文件
            shx_path = shp_path.replace('.shp', '.shx')
            if not os.path.exists(shx_path):
                print(f"❌ 缺少SHX文件: {shx_path}")
                print("   请确保SHP文件包含完整的Shapefile格式文件集(.shp, .shx, .dbf, .prj)")
                return []
            
            # 使用geopandas读取SHP文件
            gdf = gpd.read_file(shp_path)
            print(f"✅ 成功加载SHP文件: {shp_path}")
            print(f"   包含 {len(gdf)} 个要素")
            print(f"   坐标系统: {gdf.crs}")
            
            # 检查是否需要坐标转换
            if gdf.crs and 'EPSG:32649' in str(gdf.crs):
                print("🔄 检测到UTM坐标系，转换为局部坐标系...")
                # 获取边界框
                bounds = gdf.total_bounds
                min_x, min_y = bounds[0], bounds[1]
                print(f"   原始边界: {bounds}")
                print(f"   偏移量: X={min_x:.2f}, Y={min_y:.2f}")
                
                # 转换为局部坐标系（相对于边界框左下角）
                gdf_local = gdf.copy()
                gdf_local['geometry'] = gdf_local.translate(-min_x, -min_y)
                
                # 更新边界框
                bounds_local = gdf_local.total_bounds
                print(f"   转换后边界: {bounds_local}")
            else:
                gdf_local = gdf
                min_x, min_y = 0, 0
            
            initial_shapes = []
            for idx, row in gdf_local.iterrows():
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
            if min_x != 0 or min_y != 0:
                print(f"   坐标已偏移: X-{min_x:.2f}, Y-{min_y:.2f}")
            return initial_shapes
            
        except Exception as e:
            print(f"❌ 加载SHP文件失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def generate_3d_model(self, initial_shapes, rpk_path, output_dir, attributes=None):
        """
        生成3D模型
        
        Args:
            initial_shapes (list): 初始形状列表
            rpk_path (str): RPK文件路径
            output_dir (str): 输出目录
            attributes (dict): 属性参数，如果为None则使用默认属性
            
        Returns:
            bool: 是否成功
        """
        if not self.initialized:
            print("❌ PyPRT未初始化")
            return False
        
        try:
            # 检查RPK文件是否存在
            if not os.path.exists(rpk_path):
                print(f"❌ RPK文件不存在: {rpk_path}")
                return False
            
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            # 使用OBJ编码器直接生成OBJ文件
            encoder_id = "com.esri.prt.codecs.OBJEncoder"
            encoder_options = {
                'outputPath': output_dir,
                'baseName': 'generated'
            }
            
            # 设置属性 - 根据CGA规则设置
            if attributes is None:
                # 使用CGA中定义的默认属性
                default_attributes = {
                    'height': 30.0  # 对应CGA中的 attr height = 30
                }
            else:
                default_attributes = attributes
            
            # 为每个初始形状创建属性字典
            shape_attributes = [default_attributes for _ in initial_shapes]
            print("\n\n\nshape_attributes\n\n\n", shape_attributes)
            # raise
            
            print("🔄 正在生成3D模型...")
            print(f"   RPK文件: {rpk_path}")
            print(f"   初始形状数量: {len(initial_shapes)}")
            print(f"   编码器: {encoder_id}")
            print(f"   输出目录: {output_dir}")
            print(f"   使用属性: {default_attributes}")
            
            # 使用OBJ编码器生成模型
            model_generator = pyprt.ModelGenerator(initial_shapes)
            models = model_generator.generate_model(shape_attributes, rpk_path, encoder_id, encoder_options)
            print(f"✅ 生成了 {len(models)} 个模型")
            
            # 检查生成结果 - OBJEncoder 可能返回空列表但文件已生成
            if len(models) == 0:
                print("⚠️  模型列表为空，检查是否生成了文件...")
            
            # 检查输出文件
            import glob
            obj_files = glob.glob(os.path.join(output_dir, "generated*.obj"))
            if obj_files:
                print(f"✅ 成功生成OBJ文件:")
                for obj_file in obj_files:
                    file_size = os.path.getsize(obj_file)
                    print(f"   - {os.path.basename(obj_file)} ({file_size} 字节)")
                return True
            else:
                print("❌ 没有找到生成的OBJ文件")
                return False
            
        except Exception as e:
            print(f"❌ 生成3D模型失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def process_files(self, shp_path, rpk_path, output_dir, attributes=None):
        """
        处理SHP和RPK文件
        
        Args:
            shp_path (str): SHP文件路径
            rpk_path (str): RPK文件路径
            output_dir (str): 输出目录
            attributes (dict): 属性参数
        """
        print("🚀 开始处理CityEngine文件...")
        
        # 加载SHP文件
        initial_shapes = self.load_shp_file(shp_path)
        if not initial_shapes:
            print("❌ 没有可用的初始形状")
            return False
        
        # 生成3D模型
        success = self.generate_3d_model(initial_shapes, rpk_path, output_dir, attributes)
        
        if success:
            print("🎉 处理完成！")
        else:
            print("❌ 处理失败")
        
        return success

def create_simple_rpk_from_cga(cga_path, output_rpk_path):
    """
    从CGA文件创建简单的RPK文件（临时解决方案）
    注意：这只是一个示例，实际使用中应该用CityEngine GUI导出RPK
    """
    print(f"⚠️  注意：CGA文件需要转换为RPK格式")
    print(f"   请使用CityEngine GUI将 {cga_path} 导出为RPK文件")
    print(f"   或者使用示例数据中的RPK文件")
    return False

def main():
    """主函数"""
    print("🏙️ CityEngine SDK Python处理器")
    print("=" * 50)
    
    # 创建处理器
    processor = CityEngineProcessor()
    
    if not processor.initialized:
        print("❌ 无法初始化PyPRT，请检查安装")
        return
    
    # 给定路径
    shp_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data_shp/site01_utm_final/site01_utm_final.shp"
    
    # 使用官方示例的RPK文件进行测试
    # rpk_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/cityengine-sdk/data/candler.rpk"
    rpk_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/data/shangye.rpk"
    # rpk_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/data/shangye.cga"
    output_dir = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images"
    

    #  动态参数
    setback_dis = random.uniform(7,20)
    street_jiao = random.uniform(30,70)
    street_jiao_1 = random.uniform(30,70)
    Far = random.uniform(5,12)
    BD_set_dis_min = random.uniform(30,70)
    BD_set_dis_max = random.uniform(BD_set_dis_min,100)
    BD_kuandu = random.uniform(30,100)
    BD_kaikou = random.uniform(0.8,1.0)
    BD_gaocen_kaundu = random.uniform(30,100)
    BD_gaocen_shengdu = random.uniform(30,100)
    BD_gaocen_site = random.uniform(10,2000)
    BD_gaocen_kaundu = random.uniform(30,100)
    gao_per = random.uniform(0.4,0.7)
    zhong_per = random.uniform(0,1-gao_per)
    di_per = 1 - gao_per - zhong_per
    BD_dicen_chang = random.uniform(80,300)
    BD_dicen_kuan = random.uniform(80,300)


    # 使用简化的属性（只保留必要的）todo
    attributes = {
        'height': 30.0,  # 对应CGA中的 attr height = 30
        'Mode': 'Visualization',

        # 'jiejiao_color': '#000000',
        'setback_dis': setback_dis,
        'street_jiao': street_jiao,
        'street_jiao_1': street_jiao_1,
        'Far': Far,
        'BD_set_dis_min': BD_set_dis_min,
        'BD_set_dis_max': BD_set_dis_max,
        'BD_kuandu': BD_kuandu,
        'BD_kaikou': BD_kaikou,
        'BD_gaocen_kaundu': BD_gaocen_kaundu,
        'BD_gaocen_shengdu': BD_gaocen_shengdu,
        'BD_gaocen_site': BD_gaocen_site,
        'BD_gaocen_kaundu': BD_gaocen_kaundu,
        'gao_per': gao_per,
        'zhong_per': zhong_per,
        'di_per': di_per,
        'BD_dicen_chang': BD_dicen_chang,
        'BD_dicen_kuan': BD_dicen_kuan,

    }
    
    print("🔄 开始处理文件...")
    print(f"   使用官方示例RPK: {rpk_path}")
    print(f"   使用简化属性: {attributes}")
    # print("   ⚠️  注意：这是测试版本，使用candler.rpk的规则")
    # print("   要使用你的CGA规则，请在CityEngine中正确导出RPK文件")
    print("   ⚠️  注意: 使用shangye.rpk的规则")
    
    # 处理文件
    processor.process_files(shp_path, rpk_path, output_dir, attributes)

if __name__ == "__main__":
    main() 