'''Holds the image data for generating the Lithophane'''
from __future__ import division

import sys

IS_PY_3 = sys.version_info.major == 3

import math, os
import FreeCAD, FreeCADGui
from pivy import coin

from image_viewer import ImageViewer
from utils.geometry_utils import pointCloudToLines
from lithophane_utils import toChunks, tupleToVector, vectorToTuple, convertImageToTexture, recomputeView
from utils.timer import Timer, computeOverallTime
import utils.qtutils as qtutils
from base_lithophane_processor import BaseLithophaneProcessor

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

def imageChanged(lithophaneImage, newPath):
    if not hasattr(lithophaneImage, 'image') or not hasattr(lithophaneImage, 'lastPath'):
        return True
    
    return newPath != lithophaneImage.lastPath

def imgToBase64(image):
    ba = qtutils.QByteArray()
    
    buffer = qtutils.QBuffer(ba)
    buffer.open(qtutils.QIODevice.WriteOnly)
    image.save(buffer, 'PNG')
    
    base64Data = ba.toBase64().data()

    if IS_PY_3:
        base64Data = base64Data.decode('utf-8')

    return base64Data

def imageFromBase64(base64):
    base64Data = base64

    if IS_PY_3:
        base64Data = base64Data.encode('utf-8')

    ba = qtutils.QByteArray.fromBase64(qtutils.QByteArray(base64Data))
    
    return qtutils.QImage.fromData(ba, 'PNG')

def calculatePixelHeight(image, x, y, baseHeight, maximumHeight):
    '''Calculate the height of the pixel based on its lightness value.
    Lighter colors mean lower height because the light must come through.
    Maximum lightness 255 means the base height
    Minimum lightness 0 means the full height of base height + additional height

    When alpha channel has some transparency (alpha value < 255) we calculate the height
    based on the alpha value. 254 means maximumHeight and 0 means baseHeight
    '''
    color = qtutils.QColor()
    color.setRgba(image.pixel(x, y))

    percentage = 0
    alpha = color.alpha()

    if(alpha < 255):
        percentage = (100 / 254) * alpha
    else:
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

class LithophaneImage(BaseLithophaneProcessor):
    def __init__(self, obj, imagePath):
        '''Add properties for image like path'''
        super(LithophaneImage, self).__init__('Recalculate Image')

        obj.addProperty("App::PropertyString","Path","LithophaneImage","Path to the original image").Path=imagePath
        obj.addProperty("App::PropertyFloat", "ppi", "LithophaneImage", "Pixels per Inch").ppi = 300
        obj.addProperty("App::PropertyLength", "NozzleSize", "LithophaneImage", "Size of your 3D printers Nozzle").NozzleSize = 0.4
        obj.addProperty("App::PropertyLength", "LayerHeight", "LithophaneImage", "The height of a single layer your 3D Printer can print").LayerHeight = 0.1
        obj.addProperty("App::PropertyLength", "BaseHeight", "LithophaneImage", "The height of the white color").BaseHeight = 0.5
        obj.addProperty("App::PropertyLength", "MaximumHeight", "LithophaneImage", "The height of the black color").MaximumHeight = 3
        
        obj.addProperty("App::PropertyFloat", "UpdateNotifier", "LithophaneImage", "Notifies the View Provider that something changed.").UpdateNotifier = -1
        
        obj.Proxy = self

        self.lastPath = imagePath
        self.isLithophaneImage = True

    def getProcessingSteps(self, fp):
        return [('Reload Image', self.reloadImage), 
        ('Compute Point Cloud', self.computePointcloud), 
        ('Compute Nozzle Size', self.computeNozzleSize), 
        ('Compute Layer Height', self.computeLayerHeight)]

    def reloadImage(self, fp):
        if imageChanged(self, fp.Path):
            self.image = qtutils.readImage(fp.Path)
            self.lastPath = fp.Path

            imageSize = self.image.size()
            self.imageHeight = imageSize.height()
            self.imageWidth = imageSize.width()
    
    def computePointcloud(self, fp):
        return computeLines(self.image, fp.ppi, fp.BaseHeight, fp.MaximumHeight)
    
    def computeNozzleSize(self, fp, pointData):
        return (averageByNozzleSize(pointData[0], fp.ppi, fp.NozzleSize), pointData[1])
    
    def computeLayerHeight(self, fp, lineData):
        return (nearestLayerHeight(lineData[0], fp.LayerHeight.Value), lineData[1])
    
    def processingDone(self, fp, lineData):
        self.lines = lineData[0]
        self.maxHeight = lineData[1]

        fp.UpdateNotifier += 1

    def length(self):
        return self.lines[-1][-1].x

    def width(self):
        return self.lines[-1][-1].y

    def __getstate__(self):
        '''Store the image as base64 inside the document'''

        base64ImageOriginal = imgToBase64(self.image)

        lineTuples = []

        for line in self.lines:
            lineTuples.append([vectorToTuple(point) for point in line])
       
        return (base64ImageOriginal, self.lastPath, lineTuples, self.maxHeight)
 
    def __setstate__(self,state):
        '''Restore the state'''

        super(LithophaneImage, self).__init__('Recalculate Image')

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

        self.isLithophaneImage = True
        
        return None
    
class ViewProviderLithophaneImage:
    def __init__(self, vobj):
        '''Only set our viewprovider as proxy. No properties needed'''
        vobj.Proxy = self
 
    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.LithophaneImage = self.Object.Proxy

        self.Object.setEditorMode("UpdateNotifier", 2)

        self.imageNode = coin.SoSeparator()

        self.coords = coin.SoCoordinate3()
        self.coords.point.set1Value(0, 0, 0, -1)
        self.coords.point.set1Value(1, 1, 0, -1)
        self.coords.point.set1Value(2, 1, 1, -1)
        self.coords.point.set1Value(3, 0, 1, -1)

        textureCoords = coin.SoTextureCoordinate2()
        textureCoords.point.set1Value(0, 0, 0)
        textureCoords.point.set1Value(1, 1, 0)
        textureCoords.point.set1Value(2, 1, 1)
        textureCoords.point.set1Value(3, 0, 1)

        faceset = coin.SoFaceSet()
        faceset.numVertices.set1Value(0, 4)

        # This makes it possible to select the object in the 3D View
        selectionNode = coin.SoType.fromName("SoFCSelection").createInstance()
        selectionNode.documentName.setValue(FreeCAD.ActiveDocument.Name)
        selectionNode.objectName.setValue(self.Object.Name)
        selectionNode.subElementName.setValue("Face")
        selectionNode.addChild(faceset)

        self.texture = coin.SoTexture2()

        self.imageNode.addChild(self.coords)
        self.imageNode.addChild(textureCoords)
        self.imageNode.addChild(self.texture)
        self.imageNode.addChild(selectionNode)

        vobj.addDisplayMode(self.imageNode, "LithophaneImage");

    def getDisplayModes(self,obj):
        '''Return a list of display modes.'''
        
        return ["LithophaneImage"]
 
    def getDefaultDisplayMode(self):
        '''Return the name of the default display mode. It must be defined in getDisplayModes.'''
       
        return "LithophaneImage"

    def updateData(self, fp, prop):
        '''Nothing to do when some properties are changed'''
        
        if prop == 'UpdateNotifier' and self.Object.UpdateNotifier > -1:
            lithophaneImage = self.LithophaneImage

            self.texture.image = convertImageToTexture(lithophaneImage.image)

            length = lithophaneImage.length()
            width = lithophaneImage.width()
            
            self.coords.point.set1Value(1, length, 0, -1)
            self.coords.point.set1Value(2, length, width, -1)
            self.coords.point.set1Value(3, 0, width, -1)

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
    fileName = os.path.split(imagePath)[1]
    imageName = os.path.splitext(fileName)[0]

    a=FreeCAD.ActiveDocument.addObject("App::FeaturePython", imageName)
    image = LithophaneImage(a, imagePath)
    ViewProviderLithophaneImage(a.ViewObject)

    recomputeView()

    return image

if __name__ == "__main__":
    imagePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'testimages', 'medium.png')

    image = qtutils.readImage(imagePath)

    if image.isNull():
         FreeCAD.Console.PrintMessage(imageReader.errorString())
    else:
        createImage(imagePath).ppi = 2