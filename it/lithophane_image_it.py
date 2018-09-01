import os
from freecad_it.freecad_utils import getObject, recompute, vector
from freecad_it.asserting import assertThat, isNotNone, hasAttributeOfValue, isOfType, hasAttribute, matchesTowdimensionalListOfVectors
import freecad_it.logger as logger

import lithophane_image

def buildSmallPointsReduced():
    points = []
    distanceBetweenPoints = 0.42 # the default settings end up with this distance between points

    # The small reduced image ends up in 10x10 pixels
    for row in range(0, 10):
        line = []

        for column in range(0, 10):

            # Ninth column is 50% grey. So at height 1.2 millimeters
            if column == 8:
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 1.2))
            elif row == 4 and column < 7:
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 0.8))
            elif row == 8 and column < 6:
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 2))
            elif row == 8 and column == 6:
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 1.7))
            else:
                # everything that is white
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 0.5))

        points.append(line)

    return points

def buildTinyPoints():
    points = []
    distanceBetweenPoints = 1 # 25,4 ppi should be 1mm

    # The tiny image with no optimizations ends up in 10x10 pixels
    for row in range(0, 10):
        line = []

        for column in range(0, 10):

            # Eight column is 50% grey. So at height 1.75 millimeters
            if column == 7:
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 1.75))
            # First 3 pixels of third colum are 25% grey. 1.1mm
            elif row == 2 and column < 3:
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 1.1))
            # First 5 pixels of ninth colum are black. so at full height
            elif row == 8 and column < 5:
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 3))
            else:
                # everything that is white
                line.append(vector(distanceBetweenPoints * column, distanceBetweenPoints * row, 0.5))

        points.append(line)

    return points

small_points_reduced = buildSmallPointsReduced()
tiny_points = buildTinyPoints()

# Utils
def imagePath(fileName):
    imagePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'testimages', fileName)

    return imagePath

def importImage(imageName):
    lithophane_image.createImage(imagePath(imageName + '.png'))

    return getObject(imageName)

# Tests

def isLoadedWithRightName():
    image = importImage('small')

    assertThat(image, isNotNone())
    assertThat(image, isOfType('App::FeaturePython'))
    assertThat(image, hasAttributeOfValue('ppi', 300))
    assertThat(image, hasAttributeOfValue('LayerHeight', 0.1))
    assertThat(image, hasAttributeOfValue('BaseHeight', 0.5))
    assertThat(image, hasAttributeOfValue('MaximumHeight', 3))
    assertThat(image, hasAttributeOfValue('NozzleSize', 0.4))

def pointcloudIsCalculatedForDefaultProperties():
    image = importImage('small').Proxy
    recompute()

    assertThat(image, isNotNone())
    assertThat(image, hasAttribute('lines'))
    assertThat(image.lines, matchesTowdimensionalListOfVectors(small_points_reduced))

def pointCloudIsCalculatedWithoutNozzleSize():
    imageObject = importImage('tini')
    imageObject.NozzleSize = 0
    imageObject.ppi = 25.4 # Should be approximately 1mm per pixel
    image = imageObject.Proxy
    
    recompute()

    assertThat(image, isNotNone())
    assertThat(image, hasAttribute('lines'))
    assertThat(image.lines, matchesTowdimensionalListOfVectors(tiny_points))

def pointCloudIsCalculatedWithoutNozzleSizeForTransparency():
    imageObject = importImage('tiny_transparency')
    imageObject.NozzleSize = 0
    imageObject.ppi = 25.4 # Should be approximately 1mm per pixel
    image = imageObject.Proxy
    
    recompute()

    assertThat(image, isNotNone())
    assertThat(image, hasAttribute('lines'))
    assertThat(image.lines, matchesTowdimensionalListOfVectors(tiny_points))

def collectTests():
    return [isLoadedWithRightName, pointcloudIsCalculatedForDefaultProperties, pointCloudIsCalculatedWithoutNozzleSize, pointCloudIsCalculatedWithoutNozzleSizeForTransparency]