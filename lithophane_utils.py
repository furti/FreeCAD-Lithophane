import FreeCAD, FreeCADGui

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
  
  return selection[0].Proxy