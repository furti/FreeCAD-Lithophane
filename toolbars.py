from collections import OrderedDict
import FreeCAD, FreeCADGui

class ToolbarManager:
    Toolbars =  OrderedDict()

    def registerCommand(self, command):
        FreeCADGui.addCommand(command.commandName, command)
        self.Toolbars.setdefault(command.toolbarName, []).append(command)

toolbarManager = ToolbarManager()

# geometry tools
import import_image
import create_box

# solid tools
import make_solid

# debugging tools
import show_pointcloud