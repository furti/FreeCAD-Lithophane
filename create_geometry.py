'''Creates the wires and part objects'''

import FreeCAD, FreeCADGui
import Draft, Part, BOPTools
import PartDesignGui
from PySide import QtGui

from lithophane_image import LithophaneImage

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

def makeWires(points, columns, rows):
    imagePlaneWires = []

    for row in range(rows):
        rowOffset = row * columns
        pointsOfRow = []

        for column in range(columns):
            point = points[rowOffset + column]

            pointsOfRow.append(point)

        imagePlaneWires.append(Draft.makeWire(pointsOfRow, closed=False, face=False, support=None))

    return imagePlaneWires

def makeLoft(wires, name):
  loft=FreeCAD.activeDocument().addObject('Part::Loft', name)
  loft.Sections=wires
  loft.Ruled = True

  return loft

def makeBlockBase(points, maxHeight):
  firstPoint = points[0]
  lastPoint = points[-1]

  length = lastPoint[0] - firstPoint[0]
  width = lastPoint[1] - firstPoint[1]

  block = App.ActiveDocument.addObject("Part::Box","ImageBase")
  block.Length = length
  block.Width = width
  block.Height = maxHeight

  return block
  
def performSlice(imageBase, imagePlane):
  s = BOPTools.SplitFeatures.makeSlice(name= 'Slice')
  s.Base = imageBase
  s.Tools = imagePlane
  s.Mode = 'Split'
  s.Proxy.execute(s)
  s.purgeTouched()

  return s

def downgradeSlice(s):
  downgrade = Draft.downgrade(s, delete=True)
  FreeCAD.ActiveDocument.recompute()
  
  downgrade = Draft.downgrade(downgrade[0][0], delete=True)
  FreeCAD.ActiveDocument.recompute()

  image = downgrade[0][0]

  FreeCAD.ActiveDocument.removeObject(downgrade[0][1].Name)

def hideElements(elements):
  for element in elements:
    element.ViewObject.Visibility = False

class CreateGeometryCommand:
    toolbarName = 'Image_Tools'
    commandName = 'Create_Geometry'

    def GetResources(self):
        # Add pixmap some time 'Pixmap'  : 'My_Command_Icon
        return {'MenuText': "Create Geometry",
                'ToolTip' : "Creates the geometry of the selected Lithophane Image"}

    def Activated(self):
        lithophaneImage = findSelectedImage()

        if lithophaneImage is None:
          QtGui.QMessageBox.information(QtGui.qApp.activeWindow(), "No LithophaneImage selected", "Select exactly one LithophaneImage to continue")

          return
        
        wires = makeWires(lithophaneImage.PointCloud, lithophaneImage.imageWidth, lithophaneImage.imageHeight)
        FreeCAD.ActiveDocument.recompute()
        
        loft = makeLoft(wires, 'ImagePlane')
        FreeCAD.ActiveDocument.recompute()
        
        block = makeBlockBase(lithophaneImage.PointCloud, lithophaneImage.maxHeight)
        FreeCAD.ActiveDocument.recompute()
        
        s = performSlice(block, loft)
        hideElements(wires)
        hideElements([loft, block])
        FreeCAD.ActiveDocument.recompute()

        imagePart = downgradeSlice(s)

        FreeCAD.ActiveDocument.recompute()
        FreeCADGui.updateGui()
        Gui.activeDocument().activeView().viewAxonometric()
        FreeCADGui.SendMsgToActiveView("ViewFit")
    
    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None


if __name__ == "__main__":
    command = CreateGeometryCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "No open Document", "There is no open document")
else:
   toolbars.toolbarManager.registerCommand(CreateGeometryCommand())