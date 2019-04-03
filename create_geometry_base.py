'''Creates the mesh for a tube lithophane'''

import FreeCAD
# import FreeCADGui
# import Mesh, Part, MeshPart

import lithophane_utils
import utils.qtutils as qtutils
from base_lithophane_processor import BaseLithophaneProcessor


class CreateGeometryBase(object):
    def Activated(self):
        lithophaneImage, imageLabel, documentObject = lithophane_utils.findSelectedImage(
            True)

        if lithophaneImage is None:
            qtutils.showInfo("No LithophaneImage selected",
                             "Select exactly one LithophaneImage to continue")

            return

        self.createGeometryInstance(documentObject, imageLabel)

        lithophane_utils.recomputeView()

    def createGeometryInstance(self, documentObject, imageLabel):
        raise NotImplementedError

    def IsActive(self):
        """There should be at least an active document."""
        return not FreeCAD.ActiveDocument is None
