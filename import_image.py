import FreeCAD, FreeCADGui
from PySide import QtGui
import toolbars
import lithophane_image
from utils.resource_utils import iconPath

class ImportImageCommand:
    toolbarName = 'Image_Tools'
    commandName = 'Import_Image'

    def GetResources(self):
        return {'MenuText': "Import Image",
                'ToolTip' : "Imports an image to be converted to a Lithophane",
                'Pixmap': iconPath('ImportImage.svg')}

    def Activated(self):
        fileName = QtGui.QFileDialog.getOpenFileName(QtGui.qApp.activeWindow(), "Open Image", '', "Image Files (*.png *.jpg *.bmp)")[0]

        if fileName is None or fileName == '':
            FreeCAD.Console.PrintMessage('No File Selected')
        else:
            image = lithophane_image.createImage(fileName)
            
            FreeCAD.ActiveDocument.recompute()


    def IsActive(self):
        """If there is no active document we can't add a image to it."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = ImportImageCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "No open Document", "There is no open document")
else:
   toolbars.toolbarManager.registerCommand(ImportImageCommand()) 