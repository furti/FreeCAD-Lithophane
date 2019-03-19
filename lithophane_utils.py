import sys
IS_PY_2 = sys.version_info.major < 3

import math
import FreeCAD, FreeCADGui
import itertools, Mesh
from pivy import coin
import utils.qtutils as qtutils

def recomputeView():
    FreeCAD.ActiveDocument.recompute()
    FreeCADGui.updateGui()
    FreeCADGui.activeDocument().activeView().viewAxonometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")

def findSelectedImage(includeObject=False):
  selection = FreeCADGui.Selection.getSelection()

  if includeObject:
    notFound = (None, None, None)
  else:
    notFound = (None, None)
  
  if len(selection) != 1:
    return notFound
  
  selectedObject = selection[0]

  if not hasattr(selectedObject, 'Proxy') or selectedObject.Proxy is None:
    return notFound

  if not hasattr(selectedObject.Proxy, 'isLithophaneImage') or not selectedObject.Proxy.isLithophaneImage:
    return notFound
  
  if includeObject:
    return (selection[0].Proxy, selection[0].Label, selection[0])
  else:
    return (selection[0].Proxy, selection[0].Label)

def findSelectedMesh():
  selection = FreeCADGui.Selection.getSelection()
  
  if len(selection) != 1:
    return (None, None)
  
  selectedObject = selection[0]

  if not hasattr(selectedObject, 'Mesh'):
    return (None, None)

  return (selection[0].Mesh, selection[0].Label)

def vectorAtGround(vector):
  return FreeCAD.Vector(vector.x, vector.y, 0)

def toChunks(iterable, chunksize):
    """
   Splits the iterable into evenly sized chunks. The last chunk can be smaller when iterable contains not enough elements
    """
    i = iter(iterable)

    while True:
        wrapped_chunk = [list(itertools.islice(i, int(chunksize)))]

        if not wrapped_chunk[0]:
            break
        
        yield wrapped_chunk.pop()

def vectorToTuple(vector):
  return (vector.x, vector.y, vector.z)

def tupleToVector(t):
  return FreeCAD.Vector(t[0], t[1], t[2])

def convertImageToTexture(image):
    size = coin.SbVec2s(image.width(), image.height())
    buffersize = image.byteCount()

    soImage = coin.SoSFImage()
    width = size[0]
    height = size[1]
    # imageBytes = b''

    byteList = []
    
    for y in range(height -1, -1, -1):
          for x in range(width):
              
              rgb = image.pixel(x,y)
              color = qtutils.QColor()
              color.setRgba(rgb)
              alpha = color.alpha()
              value = 0

              if alpha < 255:
                  value = 254 - alpha
              else:
                  value = color.lightness()
              
              if IS_PY_2:
                  byteList.append(chr(value))
              else:
                  byteList.append(chr(value).encode('latin-1'))

    imageBytes = b''.join(byteList)
    soImage.setValue(size, 1, imageBytes)

    return soImage

def diameterFromPerimeter(perimeter):
  return perimeter / math.pi

def perimeterFromDiameter(diameter):
  return diameter * math.pi

if __name__ == '__main__':
  imagePath = 'C:\\Meine Daten\\projects\\02_Lithophane\\Nachttischlampe_Rund\\Bauernhof.jpg'
  image = qtutils.readImage(imagePath)

  print(convertImageToTexture(image))