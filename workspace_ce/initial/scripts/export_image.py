'''
Created on Jun 19, 2025

@author: 12407
'''
import os
from scripting import CE

print("✅ 脚本开始执行...")

# 初始化 CityEngine 实例
ce = CE()

# 获取当前视图
view = ce.getObjectsByType(ce.VIEWPORT)[0]
print("✅ 脚本执行...")
# 导出为 PNG
ce.exportViewport(view, "E:/HKUST/202505_Agent_Urban_Design/MetaGPT/workspace_ce/initial/images/output_view.png", 1920, 1080)
print("successfully export")

# Get a CityEngine instance
# ce = CE()

# Called before the export start.
# def initExport(exportContextOID):
#     ctx = ScriptExportModelSettings(exportContextOID)
    
# Called for each shape before generation.
# def initModel(exportContextOID, shapeOID):
#     ctx = ScriptExportModelSettings(exportContextOID)
#     shape = Shape(shapeOID)
    
# Called for each shape after generation.
# def finishModel(exportContextOID, shapeOID, modelOID):
#     ctx = ScriptExportModelSettings(exportContextOID)
#     shape = Shape(shapeOID)
#     model = Model(modelOID)
    
# Called after all shapes are generated.
# def finishExport(exportContextOID):
#     ctx = ScriptExportModelSettings(exportContextOID)
