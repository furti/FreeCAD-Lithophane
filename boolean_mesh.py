'''Base FeaturePython implementation that can handle boolean operations with meshes'''

import FreeCAD
import Mesh

from base_lithophane_processor import BaseLithophaneProcessor
from utils.resource_utils import iconPath
import utils.qtutils as qtutils
from utils import preferences

MODE_MAPPING = {
    'Additive': 'union',
    'Subtractive': 'difference'
}

ICON_MAPPING = {
    'Additive': iconPath('BooleanMeshFeatureAdd.svg'),
    'Subtractive': iconPath('BooleanMeshFeatureSubtract.svg')
}


class BooleanMeshProcessor(BaseLithophaneProcessor):
    def __init__(self, description, checkExecutionFunction, extractMeshFunction, processingStepsFunction):
        super(BooleanMeshProcessor, self).__init__(description)

        self.result = None
        self.checkExecutionFunction = checkExecutionFunction
        self.extractMeshFunction = extractMeshFunction
        self.processingStepsFunction = processingStepsFunction

    def checkExecution(self):
        return self.checkExecutionFunction()

    def processingDone(self, obj, params):
        self.result = self.extractMeshFunction(obj, params)

    def getProcessingSteps(self, obj):
        return self.processingStepsFunction(obj)


class BooleanMeshFeature(object):
    def __init__(self, obj, base, mode):
        obj.Proxy = self

        self.setProperties(obj)

        obj.Base = base
        obj.Mode = mode

        obj.Base.ViewObject.Visibility = False

    def execute(self, obj):
        import MeshPart

        base = obj.Base

        if hasattr(base, 'Mesh') and isinstance(base, Mesh.Mesh):
            self.mesh = base
        elif hasattr(base, 'Shape') and base.Shape:
            self.mesh = MeshPart.meshFromShape(base.Shape.copy(False))
        else:
            self.mesh = MeshPart.meshFromShape(base.copy(False))

    def applyOperationToMesh(self, mesh):
        if not self.Object.Enabled:
            return mesh

        import OpenSCADUtils

        openscadOperation = MODE_MAPPING[self.Object.Mode]

        return OpenSCADUtils.meshoptempfile(openscadOperation, (mesh, self.mesh))

    def setProperties(self, obj):
        self.Object = obj
        pl = obj.PropertiesList

        if not 'Base' in pl:
            obj.addProperty("App::PropertyLink", "Base", "Boolean",
                            "The geometry to apply to the mesh")

        if not 'Mode' in pl:
            obj.addProperty("App::PropertyEnumeration", "Mode", "Boolean",
                            "The type of operation to apply to the mesh")

            obj.Mode = ['Additive', 'Subtractive']

        if not 'Enabled' in pl:
            obj.addProperty("App::PropertyBool", "Enabled", "Boolean",
                            "When False, the operation will not be applied").Enabled = True

    def onDocumentRestored(self, obj):
        self.setProperties(obj)

    def __getstate__(self):
        '''We do not store any data for now'''
        pass

    def __setstate__(self, state):
        '''We do not store any data for now'''
        pass


class ViewProviderBooleanMeshFeature(object):
    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object

        from pivy import coin

        self.coinNode = coin.SoGroup()
        vobj.addDisplayMode(self.coinNode, "Standard")

    def onChanged(self, vp, prop):
        pass

    def claimChildren(self):
        return [self.Object.Base]

    def getIcon(self):
        if not self.Object.Enabled:
            return iconPath('BooleanMeshFeatureDisabled.svg')

        return ICON_MAPPING[self.Object.Mode]

    def getDisplayModes(self, obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def __getstate__(self):
        '''We do not store any data for now'''
        pass

    def __setstate__(self, state):
        '''We do not store any data for now'''
        pass


class BooleanMesh(object):
    def __init__(self, obj):
        obj.Proxy = self

        self.setProperties(obj)

    def getDescription(self):
        raise NotImplementedError

    def getIcon(self):
        return None

    def checkBaseMeshExecution(self):
        if self.Object.LithophaneImage is None:
            qtutils.showInfo('No LithophaneImage linked',
                             'Please link a lithophane Image to the mesh to caculate the geometry')

            return None

        return self.Object.LithophaneImage.Proxy

    def extractBaseMesh(self, obj, params):
        raise NotImplementedError

    def getBaseProcessingSteps(self, obj):
        raise NotImplementedError

    def getResultName(self, obj):
        if not obj.LithophaneImage:
            return "Result"

        return obj.LithophaneImage.Name + '_Result'

    def execute(self, obj):
        if not obj.Result:
            m = FreeCAD.ActiveDocument.addObject(
                "Mesh::Feature", self.getResultName(obj))

            obj.Result = m

        resultMesh = Mesh.Mesh()

        description = self.getDescription()

        baseMeshProcessor = BooleanMeshProcessor(
            description + " (Base)", self.checkBaseMeshExecution, self.extractBaseMesh, self.getBaseProcessingSteps)
        baseMeshProcessor.execute(obj)

        if preferences.useBlenderForBooleanOperations():
            mesh = self.executeBlender(baseMeshProcessor.result, obj)
        else:
            mesh = self.executeOpenSCAD(baseMeshProcessor.result, obj)

        resultMesh.addMesh(mesh)

        obj.Result.Mesh = resultMesh

    def executeOpenSCAD(self, basemesh, obj):
        print('scad')
        if len(obj.Features) == 0:
            return basemesh

        mesh = basemesh

        for meshFeature in obj.Features:
            mesh = meshFeature.Proxy.applyOperationToMesh(mesh)

        return mesh

    def executeBlender(self, basemesh, obj):
        print('blender')
        if len(obj.Features) == 0:
            return basemesh

        from blender import blender_processor

        operations = [(feature.Proxy.mesh, feature.Mode, feature.Name)
                      for feature in obj.Features if feature.Enabled]
        
        # no operations enabled
        if len(operations) == 0:
            return basemesh

        return blender_processor.applyBooleanOperations(basemesh, operations)

    def addAdditiveFeature(self, base):
        createFeature(self.Object, base, 'Additive')

    def addSubtractiveFeature(self, base):
        createFeature(self.Object, base, 'Subtractive')

    def setProperties(self, obj):
        self.Object = obj
        self.isBooleanMesh = True

        pl = obj.PropertiesList

        if not 'LithophaneImage' in pl:
            obj.addProperty("App::PropertyLink", "LithophaneImage", "Image",
                            "The image used to build the geometry")

        if not 'Result' in pl:
            obj.addProperty("App::PropertyLink", "Result", "Mesh",
                            "The mesh that stores the final result")

        if not 'Features' in pl:
            obj.addProperty("App::PropertyLinkList", "Features", "Feature",
                            "The boolean operations to apply to the mesh")

    def onDocumentRestored(self, obj):
        self.setProperties(obj)

    def __getstate__(self):
        '''We do not store any data for now'''
        pass

    def __setstate__(self, state):
        '''We do not store any data for now'''
        pass


class ViewProviderBooleanMesh():
    def __init__(self, vobj):
        vobj.Proxy = self

    def attach(self, vobj):
        self.ViewObject = vobj
        self.Object = vobj.Object
        self.BooleanMesh = self.Object.Proxy

        from pivy import coin

        self.coinNode = coin.SoGroup()
        vobj.addDisplayMode(self.coinNode, "Standard")

    def onChanged(self, vp, prop):
        if prop == 'Visibility':
            self.Object.Result.ViewObject.Visibility = vp.Visibility

    def onDelete(self, vp, subelements):
        if self.Object.Result:
            FreeCAD.ActiveDocument.removeObject(self.Object.Result.Name)

        return True

    def claimChildren(self):
        children = []

        children.extend(self.Object.Features)
        children.append(self.Object.Result)

        return children

    def getDisplayModes(self, obj):
        return ["Standard"]

    def getDefaultDisplayMode(self):
        return "Standard"

    def getIcon(self):
        return self.BooleanMesh.getIcon()

    def __getstate__(self):
        '''We do not store any data for now'''
        pass

    def __setstate__(self, state):
        '''We do not store any data for now'''
        pass


def createFeature(booleanMesh, base, mode):
    feature = FreeCAD.ActiveDocument.addObject(
        "App::FeaturePython", base.Label + "_" + mode)
    BooleanMeshFeature(feature, base, mode)
    ViewProviderBooleanMeshFeature(feature.ViewObject)

    features = booleanMesh.Features
    features.append(feature)
    booleanMesh.Features = features


if __name__ == '__main__':

    class DummyMesh(BooleanMesh):
        def __init__(self, obj):
            super(DummyMesh, self).__init__(obj)

        def getDescription(self):
            return 'Dummy'

        def checkBaseMeshExecution(self):
            return '<ignore>'

        def getBaseProcessingSteps(self, obj):
            return []

        def extractBaseMesh(self, obj, params):
            return Mesh.createBox()

    booleanMesh = FreeCAD.ActiveDocument.addObject(
        "App::FeaturePython", 'DummyMesh')
    DummyMesh(booleanMesh)
    ViewProviderBooleanMesh(booleanMesh.ViewObject)

    additiveBox = App.ActiveDocument.addObject("Part::Box", "AdditiveBox")
    createFeature(booleanMesh, additiveBox, 'Additive')

    subtractiveBox = App.ActiveDocument.addObject(
        "Part::Box", "SubtractiveBox")
    subtractiveBox.Placement = App.Placement(
        App.Vector(-10, -10, -10), App.Rotation(App.Vector(0, 0, 1), 0))
    createFeature(booleanMesh, subtractiveBox, 'Subtractive')
