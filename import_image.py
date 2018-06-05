import FreeCAD, FreeCADGui
from PySide import QtGui
import toolbars

class ImportImageCommand:
    toolbarName = 'Image_Tools'
    commandName = 'Import_Image'

    def GetResources(self):
        # Add pixmap some time 'Pixmap'  : 'My_Command_Icon
        return {'MenuText': "Import Image",
                'ToolTip' : "Imports an image to be converted to a Lithophane"}

    def Activated(self):
        FreeCAD.Console.PrintMessage('Test');

    def IsActive(self):
        """If there is no active document we can't add a sketch to it."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = ImportImageCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "No open Document", "There is no open document")
else:
   toolbars.toolbarManager.registerCommand(ImportImageCommand()) 