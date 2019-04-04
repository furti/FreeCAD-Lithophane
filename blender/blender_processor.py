import os
import tempfile
import json
import subprocess

import Mesh
from utils import preferences

actualPath = os.path.dirname(os.path.realpath(__file__))
blenderBooleanPath = os.path.join(actualPath, 'blender_boolean.py')

MODE_MAPPING = {
    'Additive': 'UNION',
    'Subtractive': 'DIFFERENCE'
}


class BooleanConfig(object):

    def __init__(self):
        self.config = []
        # [
        #     {
        #         "mode": "union",
        #         "left": {
        #             "type": "file",
        #             "file": "base.stl"
        #         },
        #         "right": {
        #             "type": "file",
        #             "file": "add.stl"
        #         }
        #     },
        #     {
        #         "mode": "union",
        #         "left": {
        #             "type": "outcome"
        #         },
        #         "right": {
        #             "type": "file",
        #             "file": "subtract.stl"
        #         }
        #     }
        # ]

    def addFiles(self, leftFile, rightFile, mode):
        self.config.append({
            "mode": MODE_MAPPING[mode],
            "left": {
                "type": "file",
                "file": leftFile
            },
            "right": {
                "type": "file",
                "file": rightFile
            }
        })

    def addOutcome(self, rightFile, mode):
        self.config.append({
            "mode": MODE_MAPPING[mode],
            "left": {
                "type": "outcome"
            },
            "right": {
                "type": "file",
                "file": rightFile
            }
        })

    def write(self, dir):
        fileName = os.path.join(dir, 'config.json')

        f = open(fileName, 'w')

        try:
            json.dump(self.config, f, sort_keys=True,
                      indent=4, ensure_ascii=False)
        finally:
            f.close()

        return fileName


def writeMesh(mesh, dir, file):
    fileName = os.path.join(dir, file)
    fileName += '.stl'

    mesh.write(Filename=fileName)

    return fileName


def executeBlender(executablePath, configPath, resultPath):
    executable = os.path.basename(executablePath)

    args = [executable, '-b', '-P', blenderBooleanPath,
            '--', configPath, resultPath]

    result = subprocess.run(args, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=True, executable=executablePath)


def applyBooleanOperations(base, operations):
    '''
    base the base mesh
    operations [(mesh, mode, name)]'''
    blenderExecutable = preferences.getBlenderExecutable()

    if blenderExecutable is None or blenderExecutable.strip() == '':
        from utils import qtutils

        qtutils.showInfo('Blender Executable not set',
                         'Go to "Tools > Edit Parameters" and set "Plugins > Furti > Lithophane > BlenderExecutable" to the blender executable path')

        return

    with tempfile.TemporaryDirectory() as tmpdirname:
        config = BooleanConfig()

        firstOperation = operations[0]
        baseFile = writeMesh(base, tmpdirname, 'base')
        featureFile = writeMesh(
            firstOperation[0], tmpdirname, firstOperation[2])

        config.addFiles(baseFile, featureFile, firstOperation[1])

        if len(operations) > 1:
            for mesh, mode, name in operations[1:]:
                featureFile = writeMesh(mesh, tmpdirname, name)

                config.addOutcome(featureFile, mode)

        configPath = config.write(tmpdirname)
        resultPath = os.path.join(tmpdirname, 'boolean_result.stl')

        executeBlender(blenderExecutable, configPath, resultPath)

        resultMesh = Mesh.Mesh()
        resultMesh.read(Filename=resultPath)

        return resultMesh


if __name__ == "__main__":
    base = Mesh.createBox()
    Mesh.show(base, 'Base')

    additiveBox = Mesh.createBox()
    additiveBox.Placement = App.Placement(
        App.Vector(5, 5, 5), App.Rotation(App.Vector(0, 0, 1), 0))
    Mesh.show(additiveBox, 'additiveBox')

    subtractiveBox = Mesh.createBox()
    subtractiveBox.Placement = App.Placement(
        App.Vector(-5, -5, -5), App.Rotation(App.Vector(0, 0, 1), 0))
    Mesh.show(subtractiveBox, 'subtractiveBox')

    operations = [(additiveBox, 'Additive', 'AdditiveBox'),
                  (subtractiveBox, 'Subtractive', 'SubtractiveBox')]

    applyBooleanOperations(base, operations)
