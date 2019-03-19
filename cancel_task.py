import FreeCAD, FreeCADGui

import base_lithophane_processor
from utils.resource_utils import iconPath

class CancelTaskCommand:
    toolbarName = 'Debugging_Tools'
    commandName = 'Cancel_Task'

    def GetResources(self):
        return {'MenuText': "Cancel Task",
                'ToolTip' : "Cancels the current running Task (e.g. image parsing,...)",
                'Pixmap': iconPath('CancelTask.svg')}

    def Activated(self):
        print('canceling')

        base_lithophane_processor.CANCEL_TASK = True


    def IsActive(self):
        """If there is no active document we can't add a image to it."""
        return not FreeCAD.ActiveDocument is None

if __name__ == "__main__":
    command = CancelTaskCommand();
    
    command.Activated()
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(CancelTaskCommand()) 