import FreeCAD, FreeCADGui

import lithophane_utils
from utils.resource_utils import iconPath, uiPath
from utils.format_utils import formatLength
import utils.qtutils as qtutils

class ScalePanel():
    def __init__(self, image, freeCadObject):
        self.image = image
        self.freeCadObject = freeCadObject
        self.originalLength = image.length()
        self.originalWidth = image.width()
        self.scaleFactor = 1

        self.form = FreeCADGui.PySideUic.loadUi(uiPath('scale_dialog.ui'))

        self.LengthBox = self.form.LengthBox
        self.WidthBox = self.form.WidthBox
        self.InfoLabel = self.form.InfoLabel
        self.LengthBox.setValue(self.originalLength)
        self.WidthBox.setValue(self.originalWidth)

        self.LengthBox.valueChanged.connect(self.lengthChanged)
        self.WidthBox.valueChanged.connect(self.widthChanged)
    
    def accept(self):
        FreeCADGui.Control.closeDialog()
        
        if self.scaleFactor != 1:
            self.InfoLabel.setText('The image is recomputed. This might take a while...')
            qtutils.processEvents()

            originalPpi = self.freeCadObject.ppi

            # smaller ppi means larger image. So division not multiplication
            self.freeCadObject.ppi = originalPpi / self.scaleFactor

            lithophane_utils.recomputeView()

    def reject(self):
        FreeCADGui.Control.closeDialog()
    
    def lengthChanged(self):
        self.updateScaleFactor(self.originalLength, self.LengthBox.value())
        
        newWidth = self.originalWidth * self.scaleFactor

        if self.WidthBox.value() != newWidth:
            self.WidthBox.setValue(newWidth)

    def widthChanged(self):
        self.updateScaleFactor(self.originalWidth, self.WidthBox.value())
        
        newLength = self.originalLength * self.scaleFactor

        if self.LengthBox.value() != newLength:
            self.LengthBox.setValue(newLength)
    
    def updateScaleFactor(self, old, new):
        self.scaleFactor = new / old

class ScaleCommand:
    toolbarName = 'Image_Tools'
    commandName = 'Scale_Image'

    def GetResources(self):
        return {'MenuText': "Scale",
                'ToolTip' : "Adjusts the dpi value to scale the final geometry",
                'Pixmap': iconPath('Scale.svg')}

    def Activated(self):
        (image, label, freeCadObject) = lithophane_utils.findSelectedImage(includeObject=True)

        if image is None:
          qtutils.showInfo("No LithophaneImage selected", "Select exactly one LithophaneImage to continue")

          return
        
        panel = ScalePanel(image, freeCadObject)
        FreeCADGui.Control.showDialog(panel)
    
    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = ScaleCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(ScaleCommand())