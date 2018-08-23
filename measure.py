import FreeCAD, FreeCADGui
from PySide import QtGui

import lithophane_utils
from utils.resource_utils import iconPath
from utils.format_utils import formatLength

class MeasureCommand:
    toolbarName = 'Debugging_Tools'
    commandName = 'Measure_Mesh'

    def GetResources(self):
        return {'MenuText': "Measure",
                'ToolTip' : "Displays the dimension of the selected mesh",
                'Pixmap': iconPath('Measure.svg')}

    def Activated(self):
        mesh = lithophane_utils.findSelectedMesh()

        if mesh is None:
          QtGui.QMessageBox.information(QtGui.qApp.activeWindow(), "No Mesh selected", "Select exactly one Mesh to continue")

          return
        
        boundBox = mesh.BoundBox

        length = formatLength(boundBox.XMax - boundBox.XMin)
        width = formatLength(boundBox.YMax - boundBox.YMin)
        height = formatLength(boundBox.ZMax - boundBox.ZMin)

        message = "Length (X): %s\n\nWidth (Y): %s\n\nHeight (Z): %s" %(length, width, height)

        QtGui.QMessageBox.information(QtGui.qApp.activeWindow(), "Bounding Informations", message)
    
    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = MeasureCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(MeasureCommand())