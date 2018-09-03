import FreeCAD

def getObject(objectName):
    return FreeCAD.ActiveDocument.getObject(objectName)

def recompute():
    FreeCAD.ActiveDocument.recompute()

def vector(x, y, z):
    return FreeCAD.Vector(x, y, z)