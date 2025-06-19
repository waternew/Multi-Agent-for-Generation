import os
from scripting import CE
from jscripting.ImageExportTerrainSettings import ImageExportTerrainSettings

def main():
    print("✅ 脚本开始执行...")

    try:
        ce = CE()
        
        for obj in ce.getObjectsFrom(ce.scene, ce.isModel()):
            print("🔍 场景中的模型对象:", obj.name)
        
        ce.setSceneCoordSystem("EPSG:26954")
        terrain = ce.getObjectsFrom(ce.scene, ce.withName("'Heightmap'"))[0]
        settings = ImageExportTerrainSettings()
        
        # 设置输出路径和分辨率
        settings.setFilename("E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/layout_image2.png")
        
        # 设置是否导出地形、模型等
        settings.setExportModel(True)
        settings.setExportGround(True)
        settings.setExportSky(True)
        
        # 执行导出
        ce.export(terrain, exportSettings)
        
        print("🎉 successfully output")

    except Exception as e:
        print("error:", str(e))

if __name__ == '__main__':
    main()