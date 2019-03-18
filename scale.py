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
        self.selectedWire = None
        self.scaleFactor = 1
        self.skipEvents = False

        self.form = FreeCADGui.PySideUic.loadUi(uiPath('scale_dialog.ui'))

        self.InfoLabel = self.form.InfoLabel
        
        self.LengthBox = self.form.LengthBox
        self.WidthBox = self.form.WidthBox
        
        self.LineInfo = self.form.LineInfo
        self.LineLengthBox = self.form.LineLengthBox

        self.DiameterBox = self.form.DiameterBox

        self.LengthBox.valueChanged.connect(self.lengthChanged)
        self.WidthBox.valueChanged.connect(self.widthChanged)
        self.LineLengthBox.valueChanged.connect(self.lineLengthChanged)
        self.form.SelectLineButton.clicked.connect(self.selectLine)
        self.DiameterBox.valueChanged.connect(self.diameterChanged)

        self.updateValues()
    
    def updateValues(self):
        self.skipEvents = True

        self.LengthBox.setValue(self.originalLength * self.scaleFactor)
        self.WidthBox.setValue(self.originalWidth * self.scaleFactor)
        self.DiameterBox.setValue(lithophane_utils.diameterFromPerimeter(self.originalLength * self.scaleFactor))
        
        self.skipEvents = False
    
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
        if self.skipEvents:
            return

        self.updateScaleFactor(self.originalLength, self.LengthBox.value())

        self.updateValues()
        
    def widthChanged(self):
        if self.skipEvents:
            return

        self.updateScaleFactor(self.originalWidth, self.WidthBox.value())
        self.updateValues()
        
    def lineLengthChanged(self):
        if self.selectedWire is None or self.skipEvents:
            return
        
        originalLength = self.selectedWire.Length.Value
        newLength = self.LineLengthBox.value()

        if originalLength == newLength:
            return
        
        self.updateScaleFactor(originalLength, newLength)
        self.updateValues()
    
    def diameterChanged(self):
        if self.skipEvents:
            return
        
        newDiameter = self.DiameterBox.value()
        newPerimeter = lithophane_utils.perimeterFromDiameter(newDiameter)

        self.updateScaleFactor(self.originalLength, newPerimeter)
        self.updateValues()

    def selectLine(self):
        import Draft

        selection = FreeCADGui.Selection.getSelection()

        if len(selection) == 0:
            self.InfoLabel.setText('Select exactly one Wire to continue.')
            return
        
        draftType = Draft.getType(selection[0])

        if draftType != 'Wire':
            self.InfoLabel.setText('Select exactly one Wire to continue. Selected object is of type %s' % (draftType))
            return
        
        self.InfoLabel.setText('')

        self.selectedWire = selection[0]
        self.LineInfo.setText('%s / %smm' %(self.selectedWire.Label, self.selectedWire.Length.Value))
        
        self.LineLengthBox.setEnabled(True)
        self.LineLengthBox.setValue(self.selectedWire.Length.Value)

        self.LengthBox.setEnabled(False)
        self.WidthBox.setEnabled(False)

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