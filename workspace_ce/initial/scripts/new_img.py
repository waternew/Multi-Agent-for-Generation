# -*- coding: utf-8 -*-
'''
Created on Jun 19, 2025

@author: 12407
'''

import os
from scripting import CE
from scripting import OBJExportModelSettings

def main():
    print("✅ 脚本开始执行...")

    try:
        ce = CE()

        # 获取当前脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print("current dir:", script_dir)

        # 切换到该目录（可选）
        os.chdir(script_dir)

        # 确保有选中对象
        selection = ce.selection()
        if not selection:
            raise Exception("not select any layer")

        # 构建输出路径
        output_dir = "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images"
        base_name = "layout_obj"

        # 创建输出目录（如果不存在）
        # os.makedirs(output_dir, exist_ok=True)

        # 初始化导出设置
        exportSettings = OBJExportModelSettings()
        exportSettings.setOutputPath(output_dir)  # ✅ 设置输出目录
        exportSettings.setBaseName(base_name)          # ✅ 设置基础文件名
        exportSettings.setMeshGranularity("AS_GENERATED")
        exportSettings.setLocalOffset("SHAPE_CENTROID")
        exportSettings.setTerrainLayers(exportSettings.TERRAIN_NONE)

        # 可选：关闭全局偏移，避免模型跑飞
        # exportSettings.setGlobalOffset([0, 0, 0])

        # 执行导出
        ce.export(selection[0], exportSettings)

        print("🎉 successfully output")

    except Exception as e:
        print("error:", str(e))

if __name__ == '__main__':
    main()