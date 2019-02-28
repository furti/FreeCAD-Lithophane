'''Creates the mesh for a tube lithophane'''

import FreeCAD
# import FreeCADGui
# import Mesh, Part, MeshPart

import lithophane_utils
import utils.qtutils as qtutils
from base_lithophane_processor import BaseLithophaneProcessor


class CreateGeometryBase(BaseLithophaneProcessor):
    def __init__(self, description):
        super(BaseLithophaneProcessor, self).__init__(description)

    def checkExecution(self):
        lithophaneImage, imageLabel = lithophane_utils.findSelectedImage()

        if lithophaneImage is None:
            qtutils.showInfo("No LithophaneImage selected",
                             "Select exactly one LithophaneImage to continue")

            return None

        return (lithophaneImage, imageLabel)

    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None
