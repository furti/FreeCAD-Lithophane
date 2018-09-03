import os
from freecad_it.freecad_utils import getObject, recompute, vector
from freecad_it.asserting import assertThat, isNotNone, hasAttributeOfValue, isOfType, hasAttribute, matchesTowdimensionalListOfVectors
import freecad_it.logger as logger

import lithophane_image

v_0_0_09 = vector(0, 0, 0.9)

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

small_points_reduced = buildSmallPointsReduced()

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

def collectTests():
    return [isLoadedWithRightName, pointcloudIsCalculatedForDefaultProperties]