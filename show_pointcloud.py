import FreeCAD, FreeCADGui
import Points
from PySide import QtGui

import lithophane_utils, toolbars
from utils.geometry_utils import linesToPointCloud
from utils.resource_utils import iconPath

def showPointCloud(pts, name):
    pointCloud = Points.Points()
    pointCloud.addPoints(linesToPointCloud(pts))

    Points.show(pointCloud, name)

class ShowPointCloudCommand:
    toolbarName = 'Debugging_Tools'
    commandName = 'Show_PointCloud'

    def GetResources(self):
        return {'MenuText': "Show PointCloud",
                'ToolTip' : "Show the point cloud generated for the selected image",
                'Pixmap': iconPath('ShowPointcloud.svg')}

    def Activated(self):
        lithophaneImage = lithophane_utils.findSelectedImage()

        if lithophaneImage is None:
          QtGui.QMessageBox.information(QtGui.qApp.activeWindow(), "No LithophaneImage selected", "Select exactly one LithophaneImage to continue")

          return
        
        showPointCloud(lithophaneImage.lines, 'ImagePointCloud')

        lithophane_utils.recomputeView()
    
    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = ShowPointCloudCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "No open Document", "There is no open document")
else:
   toolbars.toolbarManager.registerCommand(ShowPointCloudCommand())