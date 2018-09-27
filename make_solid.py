'''Creates the wires and part objects'''

import math
import FreeCAD, FreeCADGui
import Mesh, Part, MeshPart

import lithophane_utils
from utils.timer import Timer, computeOverallTime
from utils.resource_utils import iconPath
import utils.qtutils as qtutils
from base_lithophane_processor import BaseLithophaneProcessor

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

class MakeSolidCommand(BaseLithophaneProcessor):
    toolbarName = 'Part_Tools'
    commandName = 'Make_Solid'

    def __init__(self):
        super(MakeSolidCommand, self).__init__('Make Solid')

    def getProcessingSteps(self, fp):
        return [('Group Faces', self.groupFaces), 
        ('Calculate Wires from Groups', self.calculateWires), 
        ('Calculate Faces from Wires', self.calculateFaces), 
        ('Create Shell from Faces', self.computeShell),
        ('Recompute View', self.recomputeView)]

    def GetResources(self):
        return {'MenuText': "Make Solid",
                'ToolTip' : "Creates a Part Object out of the selected Mesh",
                'Pixmap': iconPath('MakeSolid.svg')}

    def checkExecution(self):
        mesh, meshLabel = lithophane_utils.findSelectedMesh()

        if mesh is None:
          qtutils.showInfo("No mesh selected", "Select exactly one mesh to continue")

          return None
        
        return (mesh, meshLabel)

    def groupFaces(self, meshData):
        return (groupFaces(meshData[0]), meshData)

    def calculateWires(self, groupData):
        faceGroups = groupData[0]
        meshData = groupData[1]

        return (wiresFromFaceGroups(meshData[0], faceGroups), meshData)
    
    def calculateFaces(self, wireData):
        wires = wireData[0]
        meshData = wireData[1]

        return ([Part.Face(wire) for wire in wires], meshData)
    
    def computeShell(self, faceData):
        faces = faceData[0]
        meshData = faceData[1]

        return (Part.Compound(faces), meshData)
    
    def recomputeView(self, shellData):
        shell = shellData[0]
        meshData = shellData[1]

        Part.show(shell, meshData[1] + '_Solid')
        lithophane_utils.recomputeView()

    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None


if __name__ == "__main__":
    command = MakeSolidCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(MakeSolidCommand())
