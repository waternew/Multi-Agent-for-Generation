'''
Created on Jun 19, 2025

@author: 12407
'''
from scripting import *

# Get a CityEngine instance
ce = CE()

# Called before the export start.
def initExport(exportContextOID):
    ctx = ScriptExportModelSettings(exportContextOID)
    
# Called for each shape before generation.
def initModel(exportContextOID, shapeOID):
    ctx = ScriptExportModelSettings(exportContextOID)
    shape = Shape(shapeOID)
    
# Called for each shape after generation.
def finishModel(exportContextOID, shapeOID, modelOID):
    ctx = ScriptExportModelSettings(exportContextOID)
    shape = Shape(shapeOID)
    model = Model(modelOID)
    
# Called after all shapes are generated.
def finishExport(exportContextOID):
    ctx = ScriptExportModelSettings(exportContextOID)