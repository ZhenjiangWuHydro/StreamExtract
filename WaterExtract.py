# -*- coding: UTF-8 -*-
import os
import shutil
import arcpy
from arcpy import env
from arcpy.sa import *
import xml.etree.ElementTree as ET

arcpy.CheckOutExtension("Spatial")


class MakeStream(object):
    def __init__(self, InputDem, OutputFolder, Threshold):
        super(MakeStream, self).__init__()
        self.inputDemPath = InputDem
        self.inputDemName, _ = os.path.splitext(os.path.basename(InputDem))
        self.outputFolder = OutputFolder
        self.threshold = Threshold

    def __CheckPath(self):
        if not os.path.exists(self.inputDemPath):
            raise IOError("DEM输入不存在！")
        if os.path.exists(self.outputFolder):
            shutil.rmtree(self.outputFolder)
            os.makedirs(self.outputFolder)
        else:
            print("指定的路径不存在，正在创建...")
            os.makedirs(self.outputFolder)
            print("路径已创建。")

    def __Fill(self):
        output_filled_dem = Fill(self.inputDemPath)
        output_filled_dem.save(os.path.join(self.outputFolder, self.inputDemName + "_Fill.tif"))
        print("填洼操作已完成")
        return output_filled_dem

    def __FlowDir(self, inputFill):
        output_flowdir_dem = FlowDirection(inputFill)
        output_flowdir_dem.save(os.path.join(self.outputFolder, self.inputDemName + "_FlowDir.tif"))
        print("流向分析操作已完成")
        return output_flowdir_dem

    def __FlowAcc(self, inputFlowDir):
        output_flowacc_dem = FlowAccumulation(inputFlowDir)
        output_flowacc_dem.save(os.path.join(self.outputFolder, self.inputDemName + "_FlowAcc.tif"))
        print("流量统计操作已完成")
        return output_flowacc_dem

    def __Threshold(self, inputFlowAcc):
        expression = "Value > " + self.threshold
        output_threshold_dem = arcpy.sa.Con(inputFlowAcc, inputFlowAcc, "", expression)
        output_threshold_dem.save(os.path.join(self.outputFolder, self.inputDemName + "_Threshold.tif"))
        print("栅格计算器已完成")
        return output_threshold_dem

    def __StreamLink(self, inputThreshold, inputFlowDir):
        output_streamlink_dem = StreamLink(inputThreshold, inputFlowDir)
        output_streamlink_dem.save(os.path.join(self.outputFolder, self.inputDemName + "_StreamLink.tif"))
        print("河流链接操作已完成")
        return output_streamlink_dem

    def __StreamOrder(self, inputStreamLink, inputFlowDir):
        output_streamorderdem = StreamOrder(inputStreamLink, inputFlowDir, "STRAHLER")
        output_streamorderdem.save(os.path.join(self.outputFolder, self.inputDemName + "_StreamOrder.tif"))
        print("河流分级操作已完成")
        return output_streamorderdem

    def __StreamToFeature(self, inputStreamLink, inputFlowDir):
        StreamToFeature(inputStreamLink, inputFlowDir,
                        os.path.join(self.outputFolder, self.inputDemName + "_Stream.shp"))
        print("河网栅格河流矢量化操作已完成")

    def __StreamOrderToFeature(self, inputStreamLink, inputFlowDir):
        StreamToFeature(inputStreamLink, inputFlowDir,
                        os.path.join(self.outputFolder, self.inputDemName + "_StreamOrder.shp"))
        print("分级河网栅格河流矢量化操作已完成")

    def RunModel(self):
        """
        运行模型，生成河网
        :return: None
        """
        self.__CheckPath()
        fillDem = self.__Fill()
        flowDirTif = self.__FlowDir(fillDem)
        flowAccTif = self.__FlowAcc(flowDirTif)
        thresholdTif = self.__Threshold(flowAccTif)
        streamLinkTif = self.__StreamLink(thresholdTif, flowDirTif)
        streamOrderTif = self.__StreamOrder(streamLinkTif, flowDirTif)
        self.__StreamToFeature(streamLinkTif, flowDirTif)
        self.__StreamOrderToFeature(streamOrderTif, flowDirTif)


if __name__ == "__main__":
    tree = ET.parse("WaterExtract.xml")
    root = tree.getroot()
    inputDem = root.find('InputDemFilePath').text.encode('utf-8').decode('utf-8')
    outputFolder = root.find('OutputFolderPath').text.encode('utf-8').decode('utf-8')
    threshold = root.find('Threshold').text
    env.workspace = os.path.dirname(inputDem)
    stream = MakeStream(inputDem, outputFolder, threshold)
    stream.RunModel()
