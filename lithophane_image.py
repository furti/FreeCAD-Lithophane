'''Holds the image data for generating the Lithophane'''

from __future__ import division

import math
import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore
from pivy import coin

from image_viewer import ImageViewer
from utils.geometry_utils import pointCloudToLines
from lithophane_utils import toChunks, tupleToVector, vectorToTuple, processEvents
from utils.timer import Timer, computeOverallTime

class AverageVector:
    def __init__(self):
        self.baseVector = None
        self.heights = []
    
    def add(self, vector):
        if self.baseVector is None:
            self.baseVector = vector
        
        self.heights.append(vector.z)
    
    def average(self):
        averageHeight = sum(self.heights) / len(self.heights)

        return FreeCAD.Vector(self.baseVector.x, self.baseVector.y, averageHeight)

def mmPerPixel(ppi):
    pixelsPerMm = ppi / 25.4

    return 1 / pixelsPerMm

def readImage(imagePath):
    imageReader = QtGui.QImageReader(imagePath)

    if imageReader.canRead():
        image = imageReader.read() 

        if image.isNull():
            QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Image Read Error", "Can't read image: %s" % imageReader.errorString())

        return image
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Image Read Error", "Can't read image: %s" % imageReader.errorString())

def imageChanged(lithophaneImage, newPath):
    if not hasattr(lithophaneImage, 'image') or not hasattr(lithophaneImage, 'lastPath'):
        return True
    
    return newPath != lithophaneImage.lastPath

def imgToBase64(image):
    ba = QtCore.QByteArray()
    
    buffer = QtCore.QBuffer(ba)
    buffer.open(QtCore.QIODevice.WriteOnly)
    image.save(buffer, 'PNG')
    
    return ba.toBase64().data()

def imageFromBase64(base64):
    ba = QtCore.QByteArray.fromBase64(QtCore.QByteArray(base64))
    
    return QtGui.QImage.fromData(ba, 'PNG')

def calculatePixelHeight(image, x, y, baseHeight, maximumHeight):
    '''Calculate the height of the pixel based on its lightness value.
    Lighter colors mean lower height because the light must come through.
    Maximum lightness 255 means the base height
    Minium lightness 0 means the full height of base height + additional height
    '''
    color = QtGui.QColor(image.pixel(x, y))
    lightness = color.lightness()

    reversedLightness = (255 - lightness) # Reverse the value. Lighter means lower height
    percentage = (100 / 255) * reversedLightness

    return baseHeight.Value + ((maximumHeight.Value - baseHeight.Value) * percentage) / 100

def computeLines(image, ppi, baseHeight, maximumHeight):
        pixelSize = mmPerPixel(ppi)
        imageSize = image.size()
        imageHeight = imageSize.height()
        imageWidth = imageSize.width()

        pts = []

        maxHeight = 0

        # QImage 0,0 is in the top left corner. Our point clouds 0,0 is in the bottom left corner
        # So we itereate over the height in reverse order and use the imagewidth - y as coordinate.
        # So we get 0 for the bottom row of the image
        for y in range(imageHeight - 1, -1, -1):
            for x in range(imageWidth):
                pixelHeight = calculatePixelHeight(image, x, y, baseHeight, maximumHeight)

                if pixelHeight > maxHeight:
                    maxHeight = pixelHeight

                pts.append(FreeCAD.Vector(x * pixelSize, (imageHeight - (y + 1)) * pixelSize, pixelHeight))

        lines = pointCloudToLines(pts)

        return (lines, maxHeight)

def averageByNozzleSize(lines, ppi, nozzleSize):
    if nozzleSize == 0:
        return lines
    
    reducedLines = []
    pixelSize = mmPerPixel(ppi)
    numberOfPointsToReduce = int(round((nozzleSize.Value / pixelSize)))

    for linesToCombine in toChunks(lines, numberOfPointsToReduce):
        combined = []

        for line in linesToCombine:
            for index, rowsToCombine in enumerate(toChunks(line, numberOfPointsToReduce)):
                if len(combined) < index + 1:
                    combined.append(AverageVector())

                for point in rowsToCombine:
                    combined[index].add(point)

                del rowsToCombine

        reducedLines.append([vector.average() for vector in combined])
        del linesToCombine


    return reducedLines

def nearestLayerHeight(lines, layerHeight):
    if layerHeight == 0:
        return lines
    
    roundedLines = []
    tolerance = 0.0001

    for line in lines:
        roundedLine = []

        for point in line:
            mod = point.z % layerHeight
            reversedMod = layerHeight - mod

            if mod > tolerance:
                roundedZ = None

                if reversedMod < mod:
                    roundedZ = point.z + reversedMod
                else:
                    roundedZ = point.z - mod
                
                roundedLine.append(FreeCAD.Vector(point.x, point.y, roundedZ))
            else:
                roundedLine.append(point)
        
        roundedLines.append(roundedLine)

    return roundedLines

class LithophaneImage:
    def __init__(self, obj, imagePath):
        '''Add properties for image like path'''
        obj.addProperty("App::PropertyString","Path","LithophaneImage","Path to the original image").Path=imagePath
        obj.addProperty("App::PropertyFloat", "ppi", "LithophaneImage", "Pixels per Inch").ppi = 300
        obj.addProperty("App::PropertyLength", "NozzleSize", "LithophaneImage", "Size of your 3D printers Nozzle").NozzleSize = 0.4
        obj.addProperty("App::PropertyLength", "LayerHeight", "LithophaneImage", "The height of a single layer your 3D Printer can print").LayerHeight = 0.1
        obj.addProperty("App::PropertyLength", "BaseHeight", "LithophaneImage", "The height of the white color").BaseHeight = 0.5
        obj.addProperty("App::PropertyLength", "MaximumHeight", "LithophaneImage", "The height of the black color").MaximumHeight = 3
        
        obj.Proxy = self

        self.lastPath = imagePath
        self.pointCloudName = None

    def execute(self, fp):
        '''Recompute the image when something changed'''

        timers = []
        
        if imageChanged(self, fp.Path):
            timers.append(Timer('ReloadingImage (1/4)'))
            self.image = readImage(fp.Path)
            self.lastPath = fp.Path

            imageSize = self.image.size()
            self.imageHeight = imageSize.height()
            self.imageWidth = imageSize.width()
            timers[-1].stop()

        timers.append(Timer('Computing Point Cloud (2/4)'))
        pointData = computeLines(self.image, fp.ppi, fp.BaseHeight, fp.MaximumHeight)
        timers[-1].stop()

        timers.append(Timer('Computing Nozzle Size (3/4)'))
        lines = averageByNozzleSize(pointData[0], fp.ppi, fp.NozzleSize)
        timers[-1].stop()

        timers.append(Timer('Computing Layer Height (4/4)'))
        lines = nearestLayerHeight(lines, fp.LayerHeight.Value)
        timers[-1].stop()

        FreeCAD.Console.PrintMessage('Recalculating image took %.3f s' % (computeOverallTime(timers)))

        self.lines = lines
        self.maxHeight = pointData[1]

    def __getstate__(self):
        '''Store the image as base64 inside the document'''

        base64ImageOriginal = imgToBase64(self.image)

        lineTuples = []

        for line in self.lines:
            lineTuples.append([vectorToTuple(point) for point in line])
       
        return (base64ImageOriginal, self.lastPath, lineTuples, self.maxHeight)
 
    def __setstate__(self,state):
        '''Restore the state'''

        base64ImageOriginal = state[0]

        self.image = imageFromBase64(base64ImageOriginal)
        self.lastPath = state[1]
        self.lines = []
        self.maxHeight = state[3]

        for line in state[2]:
            self.lines.append([tupleToVector(point) for point in line])

        imageSize = self.image.size()
        self.imageHeight = imageSize.height()
        self.imageWidth = imageSize.width()

        return None

class ViewProviderLithophaneImage:
    def __init__(self, vobj):
        '''Only set our viewprovider as proxy. No properties needed'''
        vobj.Proxy = self
 
    def attach(self, vobj):
        '''Nothing to setup right now'''
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.LithophaneImage = self.Object.Proxy

        self.standard = coin.SoGroup()
        vobj.addDisplayMode(self.standard, "Standard");

        return

    def getDisplayModes(self,obj):
        '''Return a list of display modes.'''
        
        return ["Standard"]
 
    def getDefaultDisplayMode(self):
        '''Return the name of the default display mode. It must be defined in getDisplayModes.'''
       
        return "Standard"

    def updateData(self, fp, prop):
        '''Nothing to do when something changes'''
        return
 
    def onChanged(self, vp, prop):
        '''Nothing to do on change now'''
        return

    def doubleClicked(self,vobj):
        ImageViewer(self.LithophaneImage.image)

    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None
 

def createImage(imagePath):
    a=FreeCAD.ActiveDocument.addObject("App::FeaturePython","LithophaneImage")
    image = LithophaneImage(a, imagePath)
    ViewProviderLithophaneImage(a.ViewObject)

    return image

if __name__ == "__main__":
    import os
    imagePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), './testimages/medium.png')

    imageReader = QtGui.QImageReader(imagePath)
    image = imageReader.read()

    if image.isNull():
         FreeCAD.Console.PrintMessage(imageReader.errorString())
    else:
        createImage(imagePath).ppi = 2