'''Creates the wires and part objects'''

import math

import FreeCAD
import Mesh

import lithophane_utils
from utils.resource_utils import iconPath
from create_geometry_base import CreateGeometryBase
from utils import geometry_utils
from boolean_mesh import BooleanMesh
from boolean_mesh import ViewProviderBooleanMesh


class ProcessingParameters(object):
    def __init__(self, image):
        self.image = image
        self.radius = self.calculateRadius()
        self.numberOfPointsPerLine = self.calculateNumberOfPoints()
        self.pointToPointAngle = self.caclulateAngle()

        self.innerTube = None
        self.outerTube = None
        self.bottomCircle = None
        self.topCircle = None
        self.tube = None

    def calculateRadius(self):
        perimeter = self.image.length()

        return perimeter / (2 * math.pi)

    def calculateNumberOfPoints(self):
        firstLine = self.image.lines[0]
        return len(firstLine)

    def caclulateAngle(self):
        pointToPointAngle = 360 / self.numberOfPointsPerLine

        return pointToPointAngle


class CylindricalLithophane(BooleanMesh):
    def __init__(self, obj):
        super().__init__(obj)

    def getDescription(self):
        return 'CreateCylinder'

    def getIcon(self):
        return iconPath('CreateTube.svg')

    def getBaseProcessingSteps(self, obj):
        return [('Inner Tube', self.makeInnerTube),
                ('Outer Tube', self.makeOuterTube),
                ('Bottom Circle', self.makeBottomCircle),
                ('Top Circle', self.makeTopCircle),
                ('Merge Meshes', self.mergeMeshes),
                ('Optimize Mesh', self.optimizeMesh)]

    def extractBaseMesh(self, obj, processingParameters):
        return processingParameters.tube

    def makeInnerTube(self, obj, image):
        processingParameters = ProcessingParameters(image)
        height = processingParameters.image.width()

        facets = []

        for index in range(processingParameters.numberOfPointsPerLine):
            actualAngle = processingParameters.pointToPointAngle * index
            nextAngle = processingParameters.pointToPointAngle * (index + 1)

            actualPointCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius, actualAngle)
            nextPointCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius, nextAngle)

            # The inside of the tube should be visible
            # so we have to draw the faces counterclockwise
            # seen from the inside of the tube
            bottomLeft = FreeCAD.Vector(
                actualPointCoordinates[0], actualPointCoordinates[1], 0)
            topLeft = FreeCAD.Vector(
                actualPointCoordinates[0], actualPointCoordinates[1], height)
            topRight = FreeCAD.Vector(
                nextPointCoordinates[0], nextPointCoordinates[1], height)
            bottomRight = FreeCAD.Vector(
                nextPointCoordinates[0], nextPointCoordinates[1], 0)

            facets.extend([bottomLeft, bottomRight, topRight])
            facets.extend([topRight, topLeft, bottomLeft])

        processingParameters.innerTube = Mesh.Mesh(facets)

        return processingParameters

    def makeOuterTube(self, obj, processingParameters):
        lines = processingParameters.image.lines
        facets = []

        for lineNumber, actualLine in enumerate(lines):
            # No need to perform operations on the last line at all
            if lineNumber == len(lines) - 1:
                break

            # We need to iterate the lines reversed
            # The angle needs to be calculated in clockwise order, for the normals to point in the right direction
            # When we start at the beginning of the line the image would be mirrored
            nextLine = list(reversed(lines[lineNumber + 1]))
            reversedLine = list(reversed(actualLine))
            numberOfRows = len(reversedLine)

            for rowNumber, actualPoint in enumerate(reversedLine):
                # We ignore the x coordinate of the point because the radius defines our x/y coordinates
                # To get the radius we add the z coordinate to the base radius.
                # The higher the z coordinate, the thicker the tube at this point
                # The y coordinate of the image point will be used as the z coordinate in our mesh
                # because the image will stand upright

                actualAngle = processingParameters.pointToPointAngle * rowNumber
                nextAngle = processingParameters.pointToPointAngle * (rowNumber + 1)

                actualPointNextRow = nextLine[rowNumber]

                # last point means the next one is the first point
                if rowNumber == numberOfRows - 1:
                    nextPointSameRow = reversedLine[0]
                    nextPointNextRow = nextLine[0]
                else:
                    nextPointSameRow = reversedLine[rowNumber + 1]
                    nextPointNextRow = nextLine[rowNumber + 1]

                actualPointCoordinates = geometry_utils.pointOnCircle(
                    processingParameters.radius + actualPoint.z, actualAngle)
                actualPointNextRowCoordinates = geometry_utils.pointOnCircle(
                    processingParameters.radius + actualPointNextRow.z, actualAngle)
                nexPointSameRowCoordinates = geometry_utils.pointOnCircle(
                    processingParameters.radius + nextPointSameRow.z, nextAngle)
                nextPointNextRowCoordinates = geometry_utils.pointOnCircle(
                    processingParameters.radius + nextPointNextRow.z, nextAngle)

                bottomLeft = FreeCAD.Vector(
                    nexPointSameRowCoordinates[0], nexPointSameRowCoordinates[1], nextPointSameRow.y)
                bottomRight = FreeCAD.Vector(
                    actualPointCoordinates[0], actualPointCoordinates[1], actualPoint.y)
                topRight = FreeCAD.Vector(
                    actualPointNextRowCoordinates[0], actualPointNextRowCoordinates[1], actualPointNextRow.y)
                topLeft = FreeCAD.Vector(
                    nextPointNextRowCoordinates[0], nextPointNextRowCoordinates[1], nextPointNextRow.y)

                facets.extend([bottomLeft, bottomRight, topRight])
                facets.extend([topRight, topLeft, bottomLeft])

        processingParameters.outerTube = Mesh.Mesh(facets)

        return processingParameters

    def makeBottomCircle(self, obj, processingParameters):
        facets = []
        line = processingParameters.image.lines[0]

        for rowNumber, actualPoint in enumerate(line):
            actualAngle = processingParameters.pointToPointAngle * rowNumber
            nextAngle = processingParameters.pointToPointAngle * \
                (rowNumber + 1)

            if rowNumber == len(line) - 1:
                nextPoint = line[0]
            else:
                nextPoint = line[rowNumber + 1]

            actualPointCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius + actualPoint.z, actualAngle)
            nextPointCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius + nextPoint.z, nextAngle)
            actualPointInnerCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius, actualAngle)
            nextPointInnerCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius, nextAngle)

            leftOuter = FreeCAD.Vector(
                nextPointCoordinates[0], nextPointCoordinates[1], 0)
            rightOuter = FreeCAD.Vector(
                actualPointCoordinates[0], actualPointCoordinates[1], 0)
            rightInner = FreeCAD.Vector(
                actualPointInnerCoordinates[0], actualPointInnerCoordinates[1], 0)
            leftInner = FreeCAD.Vector(
                nextPointInnerCoordinates[0], nextPointInnerCoordinates[1], 0)

            facets.extend([rightOuter, leftOuter, leftInner])
            facets.extend([leftInner, rightInner, rightOuter])

        processingParameters.bottomCircle = Mesh.Mesh(facets)

        return processingParameters

    def makeBottomCircle(self, obj, processingParameters):
        line = processingParameters.image.lines[0]
        processingParameters.bottomCircle = self.makeCircle(
            processingParameters, line)

        return processingParameters

    def makeTopCircle(self, obj, processingParameters):
        line = processingParameters.image.lines[-1]
        processingParameters.topCircle = self.makeCircle(
            processingParameters, line, True)

        return processingParameters

    def mergeMeshes(self, obj, processingParameters):
        processingParameters.tube = Mesh.Mesh()
        processingParameters.tube.addMesh(processingParameters.innerTube)
        processingParameters.tube.addMesh(processingParameters.outerTube)
        processingParameters.tube.addMesh(processingParameters.bottomCircle)
        processingParameters.tube.addMesh(processingParameters.topCircle)

        return processingParameters

    def optimizeMesh(self, obj, processingParameters):
        processingParameters.tube.removeDuplicatedPoints()

        return processingParameters

    def makeCircle(self, processingParameters, line, top=False):
        facets = []

        for rowNumber, actualPoint in enumerate(line):
            actualAngle = processingParameters.pointToPointAngle * rowNumber
            nextAngle = processingParameters.pointToPointAngle * \
                (rowNumber + 1)

            if rowNumber == len(line) - 1:
                nextPoint = line[0]
            else:
                nextPoint = line[rowNumber + 1]

            actualPointCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius + actualPoint.z, actualAngle)
            nextPointCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius + nextPoint.z, nextAngle)
            actualPointInnerCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius, actualAngle)
            nextPointInnerCoordinates = geometry_utils.pointOnCircle(
                processingParameters.radius, nextAngle)

            leftOuter = FreeCAD.Vector(
                nextPointCoordinates[0], nextPointCoordinates[1], actualPoint.y)
            rightOuter = FreeCAD.Vector(
                actualPointCoordinates[0], actualPointCoordinates[1], actualPoint.y)
            rightInner = FreeCAD.Vector(
                actualPointInnerCoordinates[0], actualPointInnerCoordinates[1], actualPoint.y)
            leftInner = FreeCAD.Vector(
                nextPointInnerCoordinates[0], nextPointInnerCoordinates[1], actualPoint.y)

            if top:
                facets.extend([rightOuter, rightInner, leftInner])
                facets.extend([leftInner, leftOuter, rightOuter])
            else:
                facets.extend([rightOuter, leftOuter, leftInner])
                facets.extend([leftInner, rightInner, rightOuter])

        return Mesh.Mesh(facets)


class CreateTubeCommand(CreateGeometryBase):
    toolbarName = 'Image_Tools'
    commandName = 'Create_Tube'

    def GetResources(self):
        return {'MenuText': "Create Tube",
                'ToolTip': "Creates the geometry of the selected Lithophane Image in the shape of a Tube",
                'Pixmap': iconPath('CreateTube.svg')}

    def createGeometryInstance(self, documentObject, imageLabel):
        obj = FreeCAD.ActiveDocument.addObject(
            "App::FeaturePython", imageLabel + '_Mesh')

        CylindricalLithophane(obj)
        ViewProviderBooleanMesh(obj.ViewObject)

        obj.LithophaneImage = documentObject


if __name__ == "__main__":
    command = CreateTubeCommand()

    if command.IsActive():
        command.Activated()
    else:
        import utils.qtutils as qtutils

        qtutils.showInfo("No open Document", "There is no open document")
else:
    import toolbars
    toolbars.toolbarManager.registerCommand(CreateTubeCommand())
