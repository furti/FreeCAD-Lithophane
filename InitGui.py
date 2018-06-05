import FreeCAD, FreeCADGui

class LithophaneWorkbench (FreeCADGui.Workbench):
    "Create Lithophanes with FreeCAD"

    # TODO: Add icon Icon = utils.addicon(iconname)
    MenuText = "Lithophane"
    ToolTip = "Create Lithophanes with FreeCAD"

    def Initialize(self):
        # Initialize the module
        import toolbars

        for name,commands in toolbars.toolbarManager.Toolbars.items():
            self.appendToolbar(name,[command.commandName for command in commands])

#    def Activated(self):

#   def Deactivated(self):

FreeCADGui.addWorkbench(LithophaneWorkbench())