import FreeCAD
from os import path

utils_path = path.join(path.dirname(path.realpath(__file__)), '../Resources/Icons')

def iconPath(name):
    f = path.join(utils_path, name)

    return f