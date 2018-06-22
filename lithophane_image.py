'''Holds the image data for generating the Lithophane'''

from __future__ import division
import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore
from pivy import coin
from image_viewer import ImageViewer
import ReverseEngineering as Reen
import Points
import Mesh


baseHeight = 0.5 # basically the height for white color
maximumHeight = 0.6 # The maximum height for black colors

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

def reducePoints(pts, columns, rows):
    '''We can skip some points from the list when they have the same height.
       We can simple connect to the next point later on
    '''
    filteredPoints = []

    lastRow = rows - 1
    lastColumn = columns - 1

    
    for y in range(rows):
        rowOffset = y * columns

        for x in range(columns):
            actualPoint = pts[rowOffset + x]
            
            # keep the corners as they are
            if (x == 0 and y == 0) or (x == lastColumn and y == lastRow) or (x == 0 and y == lastRow) or (x == lastColumn and y == 0):
                filteredPoints.append(actualPoint)
            else:
                # find neighbours
                neighbours = []

                # Same row prev column
                if x != 0:
                    neighbours.append(pts[rowOffset + x - 1])
                
                # Same row next column
                if x < lastColumn:
                    neighbours.append(pts[rowOffset + x + 1])

                # Same column next row
                if y < lastRow:
                    neighbours.append(pts[rowOffset + columns + x])

                # Same column prev row
                if y != 0:
                    neighbours.append(pts[rowOffset - columns + x])
                
                FreeCAD.Console.PrintMessage("Neighbours: ")
                FreeCAD.Console.PrintMessage(("X: " + str(x), "Y: " + str(y), actualPoint, neighbours))
                FreeCAD.Console.PrintMessage("\n\n")

                # Add point only if all neighbours have the same height
                neighboursWithDifferentHeight = [n for n in neighbours if n.z != actualPoint.z]
                if len(neighboursWithDifferentHeight) > 0:
                    filteredPoints.append(actualPoint)

                pass


    return filteredPoints

def calculatePixelHeight(image, x, y):
    '''Calculate the height of the pixel based on its lightness value.
    Lighter colors mean lower height because the light must come through.
    Maximum lightness 255 means the base height
    Minium lightness 0 means the full height of base height + additional height
    '''
    color = QtGui.QColor(image.pixel(x, y))
    lightness = color.lightness()

    reversedLightness = (255 - lightness) # Reverse the value. Lighter means lower height
    percentage = (100 / 255) * reversedLightness

    return baseHeight + ((maximumHeight - baseHeight) * percentage) / 100

def computePointCloud(image, ppi):
        pixelSize = mmPerPixel(ppi)
        imageSize = image.size()
        imageHeight = imageSize.height()
        imageWidth = imageSize.width()

        cloud = Points.Points()

        #pts=[(0, 0, 0), (0, imageSize.height() * pixelSize, 0), (imageSize.width() * pixelSize, imageSize.height() * pixelSize, 0), (imageSize.width() * pixelSize, 0, 0)]
        pts = []

        maxHeight = 0

        # QImage 0,0 is in the top left corner. Our point clouds 0,0 is in the bottom left corner
        # So we itereate over the height in reverse order and use the imagewidth - y as coordinate.
        # So we get 0 for the bottom row of the image
        for y in range(imageHeight - 1, -1, -1):
            for x in range(imageWidth):
                pixelHeight = calculatePixelHeight(image, x, y)

                if pixelHeight > maxHeight:
                    maxHeight = pixelHeight

                pts.append((x * pixelSize, (imageHeight - (y + 1)) * pixelSize, pixelHeight))

        #pts = reducePoints(pts, imageWidth, imageHeight)

        cloud.addPoints(pts)

        #FreeCAD.Console.PrintMessage(maxHeight)
        FreeCAD.Console.PrintMessage(pts)

        return cloud

class LithophaneImage:
    def __init__(self, obj, imagePath):
        '''Add properties for image like path'''
        obj.addProperty("App::PropertyString","Path","LithophaneImage","Path to the original image").Path=imagePath
        obj.addProperty("Points::PropertyPointKernel", "PointCloud", "LithophaneImage", "The PointCloud generated for the image")
        obj.addProperty("App::PropertyInteger", "ppi", "LithophaneImage", "Pixels per Inch").ppi = 300
        obj.Proxy = self

        self.lastPath = imagePath

 
    def execute(self, fp):
        '''Recompute the image when something changed'''

        if imageChanged(self, fp.Path):
            FreeCAD.Console.PrintMessage("LithophaneImage: Reloading image...\n")
            self.image = readImage(fp.Path)
            self.lastPath = fp.Path

        FreeCAD.Console.PrintMessage("LithophaneImage: Recompute Point cloud" + str(self) + "\n")

        self.PointCloud = computePointCloud(self.image, fp.ppi)

        Points.show(self.PointCloud)
        m=Reen.triangulate(Points=self.PointCloud, SearchRadius=2, KSearch=10)
        Mesh.show(m)

    def __getstate__(self):
        '''Store the image as base64 inside the document'''

        base64ImageOriginal = imgToBase64(self.image)
       
        return (base64ImageOriginal, self.lastPath)
 
    def __setstate__(self,state):
        '''Restore the state'''

        base64ImageOriginal = state[0]

        self.image = imageFromBase64(base64ImageOriginal)
        self.lastPath = state[1]

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
    imagePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), './testimages/tini.png')

    imageReader = QtGui.QImageReader(imagePath)
    image = imageReader.read()

    if image.isNull():
         FreeCAD.Console.PrintMessage(imageReader.errorString())
    else:
        createImage(imagePath).ppi = 2