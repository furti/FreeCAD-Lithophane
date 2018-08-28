import FreeCAD, FreeCADGui
import itertools, Mesh

def recomputeView():
    FreeCAD.ActiveDocument.recompute()
    FreeCADGui.updateGui()
    FreeCADGui.activeDocument().activeView().viewAxonometric()
    FreeCADGui.SendMsgToActiveView("ViewFit")

def findSelectedImage():
  selection = FreeCADGui.Selection.getSelection()
  
  if len(selection) != 1:
    return None
  
  selectedObject = selection[0]

  if selectedObject.Proxy is None:
    return None

  #if not isinstance(selectedObject.Proxy, LithophaneImage):
  #  return None
  
  return (selection[0].Proxy, selection[0].Label)

def findSelectedMesh():
  selection = FreeCADGui.Selection.getSelection()
  
  if len(selection) != 1:
    return None
  
  selectedObject = selection[0]

  if not hasattr(selectedObject, 'Mesh'):
    return None

  return selection[0].Mesh, selection[0].Label

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