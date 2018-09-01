import FreeCAD

def logLine(message):
    FreeCAD.Console.PrintMessage(message + '\n')

def logError(message):
    FreeCAD.Console.PrintError(message + '\n')