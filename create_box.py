'''Creates the wires and part objects'''

import FreeCAD
import Mesh

import lithophane_utils
from utils.resource_utils import iconPath
from boolean_mesh import BooleanMesh
from boolean_mesh import ViewProviderBooleanMesh
from create_geometry_base import CreateGeometryBase


class ProcessingParameters(object):
    def __init__(self, image):
        self.image = image

        self.box = None
        self.imagePlane = None
        self.blockBase = None
        self.bottomRectangle = None


class BoxLithophane(BooleanMesh):
    def __init__(self, obj):
        super().__init__(obj)

    def getDescription(self):
        return 'CreateBox'
    
    def getIcon(self):
        return iconPath('CreateBox.svg')

    def getBaseProcessingSteps(self, obj):
        return [('Image Plane', self.makeImagePlane),
                ('Image Base', self.makeBlockBase),
                ('Bottom Plane', self.createBottomRectangle),
                ('Merge Meshes', self.mergeMeshes),
                ('Optimize Mesh', self.optimizeMesh)]

    def extractBaseMesh(self, obj, processingParameters):
        return processingParameters.box

    def makeImagePlane(self, obj, image):
        processingParameters = ProcessingParameters(image)
        lines = processingParameters.image.lines

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
                bottomRight = actualLine[rowNumber + 1]  # next row same line
                topRight = nextLine[rowNumber + 1]  # next row next line
                topLeft = nextLine[rowNumber]  # same row next line

                facets.extend([bottomLeft, bottomRight, topLeft])
                facets.extend([bottomRight, topRight, topLeft])

        processingParameters.imagePlane = Mesh.Mesh(facets)

        return processingParameters

    def makeBlockBase(self, obj, processingParameters):
        lines = processingParameters.image.lines

        facets = []

        # add the bottom rectangle
        # bottomLeftCorner = lithophane_utils.vectorAtGround(lines[0][0])
        # bottomRightCorner = lithophane_utils.vectorAtGround(lines[0][-1])
        # topRightCorner = lithophane_utils.vectorAtGround(lines[-1][-1])
        # topLeftCorner = lithophane_utils.vectorAtGround(lines[-1][0])

        # facets.extend([bottomLeftCorner, topLeftCorner, bottomRightCorner])
        # facets.extend([bottomRightCorner, topLeftCorner, topRightCorner])

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

        processingParameters.blockBase = Mesh.Mesh(facets)

        return processingParameters

    def createBottomRectangle(self, obj, processingParameters):
        lines = processingParameters.image.lines

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

                bottomLeft = lithophane_utils.vectorAtGround(actualPoint)
                bottomRight = lithophane_utils.vectorAtGround(
                    actualLine[rowNumber + 1])  # next row same line
                topRight = lithophane_utils.vectorAtGround(
                    nextLine[rowNumber + 1])  # next row next line
                topLeft = lithophane_utils.vectorAtGround(
                    nextLine[rowNumber])  # same row next line

                facets.extend([bottomLeft, bottomRight, topLeft])
                facets.extend([bottomRight, topRight, topLeft])

        processingParameters.bottomRectangle = Mesh.Mesh(facets)

        return processingParameters

    def mergeMeshes(self, obj, processingParameters):
        processingParameters.box = Mesh.Mesh()
        processingParameters.box.addMesh(processingParameters.imagePlane)
        processingParameters.box.addMesh(processingParameters.blockBase)
        processingParameters.box.addMesh(processingParameters.bottomRectangle)

        return processingParameters

    def optimizeMesh(self, obj, processingParameters):
        processingParameters.box.removeDuplicatedPoints()
        processingParameters.box.harmonizeNormals()

        return processingParameters


class CreateGeometryCommand(CreateGeometryBase):
    toolbarName = 'Image_Tools'
    commandName = 'Create_Box'

    def GetResources(self):
        return {'MenuText': "Create Box",
                'ToolTip': "Creates the geometry of the selected Lithophane Image in the shape of a box",
                'Pixmap': iconPath('CreateBox.svg')}
    
    def createGeometryInstance(self, documentObject, imageLabel):
        obj = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", imageLabel + '_Mesh')

        BoxLithophane(obj)
        ViewProviderBooleanMesh(obj.ViewObject)

        obj.LithophaneImage = documentObject


if __name__ == "__main__":
    command = CreateGeometryCommand()

    if command.IsActive():
        command.Activated()
    else:
        import utils.qtutils as qtutils
        qtutils.showInfo("No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(CreateGeometryCommand())
