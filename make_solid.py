'''Creates the wires and part objects'''

import math
import FreeCAD, FreeCADGui
import Mesh, Part, MeshPart
from PySide import QtGui

import lithophane_utils
from utils.timer import Timer, computeOverallTime
from utils.resource_utils import iconPath

class Neighbours:
    def __init__(self, face):
        self.neighbours = {}

        self.addNeighbours(face)
    
    def addNeighbours(self, face):
        for index in face.NeighbourIndices:
            self.neighbours[index] = True

    def isNeighbour(self, face):
        return face.Index in self.neighbours

class FaceGroup:
    def __init__(self, face):
        self.faces = [face]

        self.Normal = FreeCAD.Vector(face.Normal.x, face.Normal.y, face.Normal.z)
        self.Neighbours = Neighbours(face)
    
    def matches(self, face):
        normalVector = FreeCAD.Vector(face.Normal.x, face.Normal.y, face.Normal.z)

        if not self.Normal.isEqual(face.Normal, 0.00001):
            return False
        
        return self.Neighbours.isNeighbour(face)
    
    def append(self, face):
        self.faces.append(face)
        self.Neighbours.addNeighbours(face)
    
    def toSegment(self):
        return [face.Index for face in self.faces]
    
    def __str__(self):
        return [face.Index for face in self.faces].__str__()

def groupFaces(mesh):
    faceGroups = []

    for face in mesh.Facets:
        matchingFaceGroups = [faceGroup for faceGroup in faceGroups if faceGroup.matches(face)]

        if len(matchingFaceGroups) > 0:
            matchingFaceGroups[0].append(face)
        else:
            faceGroups.append(FaceGroup(face))

    return faceGroups

def wiresFromFaceGroups(mesh, faceGroups):
    wires = []

    for faceGroup in faceGroups:
        wires.append(MeshPart.wireFromSegment(mesh, faceGroup.toSegment()))

    return wires

class MakeSolidCommand:
    toolbarName = 'Part_Tools'
    commandName = 'Make_Solid'

    def GetResources(self):
        return {'MenuText': "Make Solid",
                'ToolTip' : "Creates a Part Object out of the selected Mesh",
                'Pixmap': iconPath('MakeSolid.svg')}

    def Activated(self):
        mesh = lithophane_utils.findSelectedMesh()

        if mesh is None:
          QtGui.QMessageBox.information(QtGui.qApp.activeWindow(), "No mesh selected", "Select exactly one mesh to continue")

          return

        timers = []
        

        timers.append(Timer('Grouping Faces (1/5)'))
        faceGroups = groupFaces(mesh)
        timers[-1].stop()

        timers.append(Timer('Calculating Wires from Groups (2/5)'))
        wires = wiresFromFaceGroups(mesh, faceGroups)
        timers[-1].stop()

        timers.append(Timer('Calculating Faces from Wires (3/5)'))
        faces = [Part.Face(wire) for wire in wires]
        timers[-1].stop()

        timers.append(Timer('Creating Shell from Faces (4/5)'))
        shell = Part.Compound(faces)
        timers[-1].stop()

        timers.append(Timer('Recomputing View (5/5)'))
        Part.show(shell, 'Image Solid')
        lithophane_utils.recomputeView()
        timers[-1].stop()

        FreeCAD.Console.PrintMessage('Creating solid took %.3f s' % (computeOverallTime(timers)))

    
    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None


if __name__ == "__main__":
    command = MakeSolidCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(MakeSolidCommand())
