#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查SHP文件的坐标范围
"""

import geopandas as gpd
import numpy as np

def check_shp_coordinates(shp_path):
    """检查SHP文件的坐标范围"""
    print(f"🔍 检查SHP文件坐标: {shp_path}")
    print("=" * 50)
    
    try:
        # 读取SHP文件
        gdf = gpd.read_file(shp_path)
        print(f"✅ 成功加载SHP文件")
        print(f"   要素数量: {len(gdf)}")
        print(f"   坐标系统: {gdf.crs}")
        
        # 获取边界框
        bounds = gdf.total_bounds
        print(f"   边界框: {bounds}")
        print(f"   X范围: {bounds[0]:.2f} 到 {bounds[2]:.2f}")
        print(f"   Y范围: {bounds[1]:.2f} 到 {bounds[3]:.2f}")
        
        # 检查坐标范围是否合理
        x_range = bounds[2] - bounds[0]
        y_range = bounds[3] - bounds[1]
        print(f"   X范围大小: {x_range:.2f}")
        print(f"   Y范围大小: {y_range:.2f}")
        
        # 检查前几个要素的坐标
        print("\n📊 前5个要素的坐标:")
        for i in range(min(5, len(gdf))):
            geom = gdf.iloc[i].geometry
            if geom.geom_type == 'Polygon':
                coords = list(geom.exterior.coords)
                print(f"   要素 {i}: {len(coords)} 个点")
                print(f"     前3个点: {coords[:3]}")
        
        # 检查坐标是否过大或过小
        if x_range > 1000000 or y_range > 1000000:
            print("⚠️  警告：坐标范围可能过大，建议转换到局部坐标系")
        elif x_range < 0.1 or y_range < 0.1:
            print("⚠️  警告：坐标范围可能过小")
        else:
            print("✅ 坐标范围看起来合理")
            
        return True
        
    except Exception as e:
        print(f"❌ 检查坐标失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    shp_path = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/data_shp/site01_utm_final/site01_utm_final.shp"
    check_shp_coordinates(shp_path) 