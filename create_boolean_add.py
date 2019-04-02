import FreeCAD, FreeCADGui
import Mesh

import lithophane_utils
from utils.resource_utils import iconPath
import utils.qtutils as qtutils

class BooleanAddCommand:
    toolbarName = 'Boolean_Tools'
    commandName = 'Boolean_Add'

    def GetResources(self):
        return {'MenuText': "Additive Mesh",
                'ToolTip' : "Creates a additive boolean feature in the selected Lithophane Mes",
                'Pixmap': iconPath('BooleanMeshFeatureAdd.svg')}

    def Activated(self):
        if not lithophane_utils.checkOpenscadInstalled():
            return
        
        mesh, label = lithophane_utils.findSelectedBooleanMesh()

        if mesh is None:
          qtutils.showInfo("No Lithophane Mesh selected", "Select one Lithophane mesh, and either a FreeCAD Mesh or an object with a Shape")

          return
        
        base = lithophane_utils.findSelectedBaseFeature()
        
        if base is None:
          qtutils.showInfo("No Base Feature selected", "Select one Lithophane mesh, and either a FreeCAD Mesh or an object with a Shape")

          return
        
        mesh.addAdditiveFeature(base)

        FreeCAD.ActiveDocument.recompute()
        
    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = BooleanAddCommand()
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(BooleanAddCommand())