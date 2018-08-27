import FreeCAD, FreeCADGui

import lithophane_image
from utils.resource_utils import iconPath
import utils.qtutils as qtutils

class ImportImageCommand:
    toolbarName = 'Image_Tools'
    commandName = 'Import_Image'

    def GetResources(self):
        return {'MenuText': "Import Image",
                'ToolTip' : "Imports an image to be converted to a Lithophane",
                'Pixmap': iconPath('ImportImage.svg')}

    def Activated(self):
        fileName = qtutils.userSelectedFile("Open Image", qtutils.IMAGE_FILES)

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
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(ImportImageCommand()) 