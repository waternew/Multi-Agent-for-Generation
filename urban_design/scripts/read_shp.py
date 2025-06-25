import geopandas as gpd
import matplotlib.pyplot as plt
import os

def read_shapefile(shapefile_path):
    """
    读取shapefile文件并返回GeoDataFrame对象
    
    参数:
    shapefile_path (str): shapefile文件路径
    
    返回:
    gdf (GeoDataFrame): 包含shapefile数据的GeoDataFrame对象
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(shapefile_path):
            print(f"错误: 文件 {shapefile_path} 不存在")
            return None
        
        # 读取shapefile
        gdf = gpd.read_file(shapefile_path)
        print(f"成功读取shapefile文件: {shapefile_path}")
        print(f"数据集信息:")
        print(f"- 记录数: {len(gdf)}")
        print(f"- 坐标参考系统: {gdf.crs}")
        print(f"- 几何类型: {gdf.geometry.geom_type.unique()}")
        print(f"- 列: {list(gdf.columns)}")
        
        return gdf
    except Exception as e:
        print(f"读取shapefile时出错: {e}")
        return None

def plot_shapefile(gdf, title="Shapefile数据可视化"):
    """
    可视化shapefile数据
    
    参数:
    gdf (GeoDataFrame): 包含shapefile数据的GeoDataFrame对象
    title (str): 图表标题
    """
    if gdf is None:
        print("无法绘制图形: GeoDataFrame为空")
        return
    
    try:
        fig, ax = plt.subplots(figsize=(12, 8))
        gdf.plot(ax=ax)
        ax.set_title(title)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"绘制shapefile时出错: {e}")


def calulate_centroid(gdf):
    # 直接从 geometry 列计算质心的 x 和 y 坐标
    gdf["Centroid_X"] = gdf.geometry.centroid.x
    gdf["Centroid_Y"] = gdf.geometry.centroid.y

    # 重新排列列顺序，将 centroid_x 和 centroid_y 放在 Level2 后
    cols = list(gdf.columns)
    if "Level2" in cols:
        level2_idx = cols.index("Level2")
    else:
        raise ValueError("列 'Level2' 不存在，请检查列名。")

    # 构造新列顺序
    new_cols = (
        cols[:level2_idx+1] +
        ["Centroid_X", "Centroid_Y"] +
        [col for col in cols[level2_idx+1:] if col not in ["Centroid_X", "Centroid_Y"]]
    )
    return gdf[new_cols]


def main():
    # 这里需要修改为您的shapefile的实际路径
    # shapefile_path = "E:\AAARA\hkustgz\Agent for Design\Intelli-Planner\data\BEIJING"
    # shapefile_path = "/Users/ronghuang/Documents/HKUST/202412_MAS_Design/4_Code/Data/site01_utm_final"
    shapefile_path = "E:\AAARA\hkustgz\Agent for Design\Intelli-Planner\data\OURS\site01_utm_final"
    
    # 读取shapefile
    gdf = read_shapefile(shapefile_path)

    print(gdf.head())

    print(gdf.columns.tolist())
    
    # 确认当前坐标系（从 .prj 文件中自动读取）
    print("当前坐标系：", gdf.crs)
    
    # 计算质心
    new_gdf = calulate_centroid(gdf)

    # 保存为 CSV
    gdf.to_csv("Site_01_UTM.csv", index=False)
    new_gdf.to_csv("Site_01_UTM_with_centroid.csv", index=False)

    # 显示数据的前几行
    if gdf is not None and new_gdf is not None:
        print("\ngdf数据预览:")
        print(gdf.head())

        print("\nnew_gdf数据预览:")
        print(new_gdf.head())
        
        # 可视化数据
        plot_shapefile(gdf, title="Site 01 UTM数据")

if __name__ == "__main__":
    main() 