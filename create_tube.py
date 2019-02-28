'''Creates the wires and part objects'''

import math

import FreeCAD
# import FreeCADGui
import Mesh
# import Part
# import MeshPart

import lithophane_utils
# from utils.timer import Timer, computeOverallTime
from utils.resource_utils import iconPath
from create_geometry_base import CreateGeometryBase
from utils import geometry_utils


class ProcessingParameters(object):
    def __init__(self, image, imageLabel):
        self.image = image
        self.imageLabel = imageLabel
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


class CreateTubeCommand(CreateGeometryBase):
    toolbarName = 'Image_Tools'
    commandName = 'Create_Tube'

    def __init__(self):
        super(CreateGeometryBase, self).__init__('CreateTube')

    def GetResources(self):
        return {'MenuText': "Create Tube",
                'ToolTip': "Creates the geometry of the selected Lithophane Image in the shape of a Tube",
                'Pixmap': iconPath('CreateTube.svg')}

    def getProcessingSteps(self, fp):
        return [('Inner Tube', self.makeInnerTube),
                ('Outer Tube', self.makeOuterTube),
                ('Bottom Circle', self.makeBottomCircle),
                ('Top Circle', self.makeTopCircle),
                ('Merge Meshes', self.mergeMeshes),
                ('Optimize Mesh', self.optimizeMesh),
                ('Display Mesh', self.displayMesh)]

    def makeInnerTube(self, imageAndLabel):
        processingParameters = ProcessingParameters(
            imageAndLabel[0], imageAndLabel[1])
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

    def makeOuterTube(self, processingParameters):
        lines = processingParameters.image.lines
        facets = []

        for lineNumber, actualLine in enumerate(lines):
            # No need to perform operations on the last line at all
            if lineNumber == len(lines) - 1:
                break

            nextLine = lines[lineNumber + 1]

            for rowNumber, actualPoint in enumerate(actualLine):
                # We ignore the x coordinate of the point because the radius defines our x/y coordinates
                # To get the radius we add the z coordinate to the base radius.
                # The higher the z coordinate, the thicker the tube at this point
                # The y coordinate of the image point will be used as the z coordinate in our mesh
                # because the image will stand upright

                actualAngle = processingParameters.pointToPointAngle * rowNumber
                nextAngle = processingParameters.pointToPointAngle * \
                    (rowNumber + 1)

                actualPointNextRow = nextLine[rowNumber]

                # last point means the next one is the first point
                if rowNumber == len(actualLine) - 1:
                    nextPointSameRow = actualLine[0]
                    nextPointNextRow = nextLine[0]
                else:
                    nextPointSameRow = actualLine[rowNumber + 1]
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

    def makeBottomCircle(self, processingParameters):
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

    def makeBottomCircle(self, processingParameters):
        line = processingParameters.image.lines[0]
        processingParameters.bottomCircle = self.makeCircle(
            processingParameters, line)

        return processingParameters

    def makeTopCircle(self, processingParameters):
        line = processingParameters.image.lines[-1]
        processingParameters.topCircle = self.makeCircle(
            processingParameters, line, True)

        return processingParameters

    def mergeMeshes(self, processingParameters):
        processingParameters.tube = Mesh.Mesh()
        processingParameters.tube.addMesh(processingParameters.innerTube)
        processingParameters.tube.addMesh(processingParameters.outerTube)
        processingParameters.tube.addMesh(processingParameters.bottomCircle)
        processingParameters.tube.addMesh(processingParameters.topCircle)

        return processingParameters

    def optimizeMesh(self, processingParameters):
        processingParameters.tube.removeDuplicatedPoints()

        return processingParameters

    def displayMesh(self, processingParameters):
        # Mesh.show(processingParameters.innerTube,
        #           processingParameters.imageLabel + '_InnerTube')
        # Mesh.show(processingParameters.outerTube,
        #           processingParameters.imageLabel + '_OuterTube')
        # Mesh.show(processingParameters.bottomCircle,
        #           processingParameters.imageLabel + '_BottomCircle')
        # Mesh.show(processingParameters.topCircle,
        #           processingParameters.imageLabel + '_TopCircle')
        Mesh.show(processingParameters.tube,
                  processingParameters.imageLabel + '_Tube')
        lithophane_utils.recomputeView()

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
