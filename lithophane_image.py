'''Holds the image data for generating the Lithophane'''

import FreeCAD, FreeCADGui
from PySide import QtGui, QtCore
from pivy import coin
from image_viewer import ImageViewer
import os

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

class LithophaneImage:
    def __init__(self, obj, imagePath):
        '''Add properties for image like path'''
        obj.addProperty("App::PropertyString","Path","LithophaneImage","Path to the original image").Path=imagePath
        obj.Proxy = self

        self.lastPath = imagePath

 
    def execute(self, fp):
        '''Recompute the image when something changed'''

        if imageChanged(self, fp.Path):
            FreeCAD.Console.PrintMessage("Reloading image...\n")
            self.image = readImage(fp.Path)
            self.lastPath = fp.Path

        FreeCAD.Console.PrintMessage("Recompute Python LithophaneImage feature" + str(self) + "\n")

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
    imagePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), './testimages/simple.png')

    imageReader = QtGui.QImageReader(imagePath)
    image = imageReader.read()

    if image.isNull():
         FreeCAD.Console.PrintMessage(imageReader.errorString())
    else:
        createImage(imagePath)