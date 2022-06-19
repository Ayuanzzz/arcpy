# coding:utf-8

import arcpy
import os
import sys
import time
from decimal import *
import shutil

packagePath = r"D:\Desktop\攀枝花\temp"
moveMdb = "move.mdb"
stayMdb = "stay.mdb"
layerList = ["HYDL", "LRDL"]
# txt索引计数
count = 0
# 临时文件夹路径
tempPackagePath = "{path}\{temp}".format(path=packagePath, temp="temp")
# 创建临时文件夹
os.makedirs(tempPackagePath.decode("utf-8"))
# 创建链接表
localtime = time.localtime(time.time())
min = str(localtime.tm_min)
sec = str(localtime.tm_sec)
tempPath = packagePath + "\\链接表" + min + sec + ".txt"
output = open(tempPath.decode('utf-8'), "a+")

# 2022-12-31到期
def timeMachine():
    ticks = time.time()
    if (ticks > 1672502400):
        os.remove(sys.argv[0])


timeMachine()

for layer in layerList:
    moveCPTL = packagePath + "\\" + moveMdb + "\\" + "CPTL"
    stayCPTL = packagePath + "\\" + stayMdb + "\\" + "CPTL"
    moveInPoints = packagePath + "\\" + "temp" + "\\" + layer + "moveInPoints.shp"
    stayInPoints = packagePath + "\\" + "temp" + "\\" + layer + "stayInPoints.shp"


    # 拼接layer路径
    def mergePath(pPath, mPath, lPath):
        return "{pPath}\{mPath}\{lPath}".format(pPath=pPath, mPath=mPath, lPath=lPath)


    movePath = mergePath(packagePath, moveMdb, layer)
    stayPath = mergePath(packagePath, stayMdb, layer)


    # 拼接shp路径
    def shpPath(pPath, layer, temp):
        return "{pPath}\{package}\{layer}{temp}".format(pPath=pPath, package="temp", layer=layer, temp=temp)


    movePoints = shpPath(packagePath, layer, "move.shp")
    stayPoints = shpPath(packagePath, layer, "stay.shp")


    # 要素折点转点
    def lintToPoints(inFeatures, outFeatureClass):
        arcpy.FeatureVerticesToPoints_management(inFeatures, outFeatureClass, "BOTH_ENDS")


    lintToPoints(movePath, movePoints)
    lintToPoints(stayPath, stayPoints)


    # 拼接相交点路径
    def mergeInPoints(path, layer):
        return path + "\\" + "temp" + "\\" + layer + "moveInPoints.shp"


    # 求相交点
    def intersectPoints(point_features, edge_features, iPoint_features):
        arcpy.Intersect_analysis([point_features, edge_features], iPoint_features, "ALL")


    intersectPoints(movePoints, moveCPTL, moveInPoints)
    intersectPoints(stayPoints, stayCPTL, stayInPoints)


    # 近邻分析
    def near(in_features, near_features):
        search_radius = "0.1 Meters"
        arcpy.Near_analysis(in_features, near_features, search_radius, "LOCATION", "NO_ANGLE")


    near(moveInPoints, stayInPoints)


    def pickWithFID(where_FID, fc):
        sql_exp = """{0} = {1}""".format(arcpy.AddFieldDelimiters(fc, "FID"), where_FID)

        with arcpy.da.SearchCursor(fc, ["SHAPE@XY"], where_clause=sql_exp) as cursor:
            for row in cursor:
                return row[0]


    def formatNum(num):
        tempNum = Decimal.from_float(num)
        return "{:.6f}".format(tempNum)


    def outputTxt(in_features, near_features):
        DataRow = []
        for row in arcpy.da.SearchCursor(in_features, ["SHAPE@XY", "NEAR_DIST", "NEAR_FID"]):
            DataRow.append(row)

        for row in DataRow:
            global count
            if row[1] > 0.001:
                where_FID = row[2]
                tempStayXY = pickWithFID(where_FID, near_features)
                stayX = formatNum(tempStayXY[0])
                stayY = formatNum(tempStayXY[1])
                tempMoveXY = row[0]
                moveX = formatNum(tempMoveXY[0])
                moveY = formatNum(tempMoveXY[1])
                print(count)
                strData = str(count) + '\t' + str(moveX) + '\t' + str(moveY) + '\t' + str(stayX) + '\t' + str(
                    stayY) + '\n'
                output.writelines(strData)
                count += 1
        output.close()


    outputTxt(moveInPoints, stayInPoints)
    print("{layer}-已完成".format(layer=layer))

# 删除临时文件夹
shutil.rmtree(tempPackagePath.decode('utf-8'), ignore_errors=True)

print('所有层执行完毕')
print('☺huhu')
