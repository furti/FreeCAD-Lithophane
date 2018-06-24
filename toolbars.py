from collections import OrderedDict
import FreeCAD, FreeCADGui

class ToolbarManager:
    Toolbars =  OrderedDict()

    def registerCommand(self, command):
        FreeCADGui.addCommand(command.commandName, command)
        self.Toolbars.setdefault(command.toolbarName, []).append(command)

toolbarManager = ToolbarManager()

import import_image
import create_box