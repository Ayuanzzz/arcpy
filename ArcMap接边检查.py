# coding:utf-8

import arcpy
import shutil
import time
import re

# 数据路径
filePath = r"D:\Desktop\攀枝花\temp\m"
movePath = "move.mdb"
stayPath = "stay.mdb"

print('任务执行中...')


# 路径拼接
def mergePath(filePath, layer):
    return "{filePath}\{layer}".format(filePath=filePath, layer=layer)


move = mergePath(filePath, movePath)
stay = mergePath(filePath, stayPath)

localtime = time.localtime(time.time())
min = str(localtime.tm_min)
sec = str(localtime.tm_sec)

# 创建合并数据库
arcpy.CreateFileGDB_management(filePath, "mergeGDB")
# 创建融合数据库
dissolveName = 'dissolve' + min + sec
arcpy.CreateFileGDB_management(filePath, dissolveName)

mergeGDBPath = mergePath(filePath, "mergeGDB.gdb")
dissolvePath = mergePath(filePath, dissolveName + '.gdb')


# 合并数据
def mergeData():
    arcpy.env.workspace = move
    for fc in arcpy.ListFeatureClasses():
        # 只匹配线面
        matchLine = re.match(r'.*L$', fc)
        matchArea = re.match(r'.*A$', fc)
        if matchLine or matchArea:
            print(fc)
            moveLayer = mergePath(move, fc)
            stayLayer = mergePath(stay, fc)
            outputLayer = mergePath(mergeGDBPath, fc)
            arcpy.Merge_management([moveLayer, stayLayer], outputLayer)


mergeData()

# 将数据字段转为列表并融合数据
fields_dict = dict()


def fieldsToList():
    arcpy.env.workspace = mergeGDBPath
    # 融合数据路径
    for fc in arcpy.ListFeatureClasses():
        fields = arcpy.ListFields(fc)
        fields_dict[fc] = list()
        for field in fields:
            if field.name not in ["OBJECTID", "Shape", "Shape_Area", "Shape_Length"]:
                fields_dict[fc].append(field.name)
        # 融合数据
        output_dissolve = mergePath(dissolvePath, fc)
        arcpy.Dissolve_management(fc, output_dissolve, fields_dict[fc], "", "SINGLE_PART")


fieldsToList()

# 接边检查*********************************************
# 创建相交线GDB
arcpy.CreateFileGDB_management(filePath, "IntersectGDB")
# 创建检查GDB

checkName = "check" + min + sec
arcpy.CreateFileGDB_management(filePath, checkName)

intersectPath = mergePath(filePath, "IntersectGDB.gdb")
checkPath = mergePath(filePath, checkName + ".gdb")


# CPTL相交
def intersect():
    inFeatures = [mergePath(move, "CPTL"), mergePath(stay, "CPTL")]
    intersectOutput = mergePath(intersectPath, "line")
    arcpy.Intersect_analysis(inFeatures, intersectOutput, "", "", "LINE")

intersect()


# 按位置选择
def selectByLoc(layer):
    in_layer = mergePath(dissolvePath, layer)
    select_features = mergePath(intersectPath, "line")
    tempLayer = layer + "Check"
    print(tempLayer)
    arcpy.MakeFeatureLayer_management(in_layer, tempLayer)
    arcpy.SelectLayerByLocation_management(tempLayer, "BOUNDARY_TOUCHES", select_features)
    matchcount = int(arcpy.GetCount_management(tempLayer).getOutput(0))
    if matchcount > 0:
        output = mergePath(checkPath, tempLayer)
        # 写入检查层
        arcpy.CopyFeatures_management(tempLayer, output)


# 遍历融合后数据
def iterDissolve():
    arcpy.env.workspace = dissolvePath
    for layer in arcpy.ListFeatureClasses():
        selectByLoc(layer)


iterDissolve()

# 删除多余GDB
shutil.rmtree(mergeGDBPath.decode('utf-8'), ignore_errors=True)
shutil.rmtree(intersectPath.decode('utf-8'), ignore_errors=True)
print("检查结果写入{fileName}".format(fileName=checkName))
print('任务执行完成')
print('☺huhu')
