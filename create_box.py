'''Creates the wires and part objects'''

import FreeCAD, FreeCADGui
import Mesh, Part
from PySide import QtGui

import lithophane_utils
from utils.timer import Timer, computeOverallTime

def makeBlockBase(lines):
    facets = []

    # add the bottom rectangle
    bottomLeftCorner = lithophane_utils.vectorAtGround(lines[0][0])
    bottomRightCorner = lithophane_utils.vectorAtGround(lines[0][-1])
    topRightCorner = lithophane_utils.vectorAtGround(lines[-1][-1])
    topLeftCorner = lithophane_utils.vectorAtGround(lines[-1][0])

    facets.extend([bottomLeftCorner, topLeftCorner, bottomRightCorner])
    facets.extend([bottomRightCorner, topLeftCorner, topRightCorner])

    for lineNumber, actualLine in enumerate(lines):
        # Need to process all the points on the first and last line
        if lineNumber == 0 or lineNumber == len(lines) - 1:
            for rowNumber, actualPoint in enumerate(actualLine):
                # No need to perform operations on the last row
                if rowNumber == len(actualLine) - 1:
                  break
                
                nextPoint = actualLine[rowNumber + 1]

                bottomLeft = lithophane_utils.vectorAtGround(actualPoint)
                bottomRight = lithophane_utils.vectorAtGround(nextPoint)
                topRight = nextPoint
                topLeft = actualPoint

                facets.extend([bottomLeft, bottomRight, topLeft])
                facets.extend([bottomRight, topRight, topLeft])
        
        # Only use the first and last point for all other rows
        if lineNumber > 0:
            previousLine = lines[lineNumber - 1]
            
            firstPoint = actualLine[0]
            prevFirstPoint = previousLine[0]
            lastPoint = actualLine[-1]
            prevLastPoint = previousLine[-1]


            bottomLeft1 = lithophane_utils.vectorAtGround(firstPoint)
            bottomRight1 = lithophane_utils.vectorAtGround(prevFirstPoint)
            topRight1 = prevFirstPoint
            topLeft1 = firstPoint

            facets.extend([bottomRight1, topRight1, bottomLeft1])
            facets.extend([topRight1, topLeft1, bottomLeft1])

            bottomLeft2 = lithophane_utils.vectorAtGround(prevLastPoint)
            bottomRight2 = lithophane_utils.vectorAtGround(lastPoint)
            topRight2 = lastPoint
            topLeft2 = prevLastPoint

            facets.extend([bottomLeft2, bottomRight2, topLeft2])
            facets.extend([bottomRight2, topRight2, topLeft2])
    
    return Mesh.Mesh(facets)

def makeImagePlane(lines):
    facets = []

    for lineNumber, actualLine in enumerate(lines):
        # No need to perform operations on the last line at all
        if lineNumber == len(lines) - 1:
            break
        
        nextLine = lines[lineNumber + 1]

        for rowNumber, actualPoint in enumerate(actualLine):
            # No need to perform operations on the last row
            if rowNumber == len(actualLine) - 1:
                break
            
            bottomLeft = actualPoint
            bottomRight = actualLine[rowNumber + 1] # next row same line
            topRight = nextLine[rowNumber + 1] # next row next line
            topLeft = nextLine[rowNumber] # same row next line

            facets.extend([bottomLeft, bottomRight, topLeft])
            facets.extend([bottomRight, topRight, topLeft])

    return Mesh.Mesh(facets)

class CreateGeometryCommand:
    toolbarName = 'Image_Tools'
    commandName = 'Create_Box'

    def GetResources(self):
        # Add pixmap some time 'Pixmap'  : 'My_Command_Icon
        return {'MenuText': "Create Box",
                'ToolTip' : "Creates the geometry of the selected Lithophane Image in the shape of a box"}

    def Activated(self):
        lithophaneImage = lithophane_utils.findSelectedImage()

        if lithophaneImage is None:
          QtGui.QMessageBox.information(QtGui.qApp.activeWindow(), "No LithophaneImage selected", "Select exactly one LithophaneImage to continue")

          return

        # todo: we should really use the mesh for creating geometry. This is way too slow.
        # https://github.com/FreeCAD/FreeCAD/blob/master/src/Mod/Mesh/BuildRegularGeoms.py
        # https://www.freecadweb.org/wiki/Mesh_Scripting
        timers = []
        
        timers.append(Timer('Creating ImagePlane'))
        imagePlane = makeImagePlane(lithophaneImage.lines)
        timers[-1].stop()
        lithophane_utils.processEvents()

        timers.append(Timer('Creating ImageBase'))
        block = makeBlockBase(lithophaneImage.lines)
        timers[-1].stop()
        lithophane_utils.processEvents()
        
        timers.append(Timer('Merge Meshes'))
        imageMesh = Mesh.Mesh()
        imageMesh.addMesh(imagePlane)
        imageMesh.addMesh(block)
        timers[-1].stop()
        lithophane_utils.processEvents()

        timers.append(Timer('Recalculating Normals'))
        imageMesh.harmonizeNormals()
        timers[-1].stop()
        lithophane_utils.processEvents()

        # timers.append(Timer('Creating Solid From Mesh'))
        # shape = Part.Shape()
        # shape.makeShapeFromMesh(imageMesh.Topology, 0.05)
        # imageSolid = Part.makeSolid(shape)
        # timers[-1].stop()

        timers.append(Timer('Recomputing View'))
        # Part.show(imageSolid, 'Image')
        Mesh.show(imageMesh, 'Image')
        lithophane_utils.recomputeView()
        timers[-1].stop()

        FreeCAD.Console.PrintMessage('Creating Boxy image took %.3f s' % (computeOverallTime(timers)))

    
    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None


if __name__ == "__main__":
    #bop = __import__("BOPTools")
    #bop.importAll()
    #bop.addCommands()

    command = CreateGeometryCommand();
    
    if command.IsActive():
        command.Activated()
    else:
        QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "No open Document", "There is no open document")
else:
   toolbars.toolbarManager.registerCommand(CreateGeometryCommand())
