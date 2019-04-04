import FreeCAD

params = FreeCAD.ParamGet('User parameter:Plugins/Furti/Lithophane')


def useBlenderForBooleanOperations():
    return params.GetBool('UseBlenderForBooleanOperations')


def getBlenderExecutable():
    return params.GetString('BlenderExecutable')


def setupParameters():
    paramVersion = params.GetInt('ParamVersion')

    if paramVersion < 1:
        params.SetInt('ParamVersion', 1)
        params.SetBool('UseBlenderForBooleanOperations', False)
        params.SetString('BlenderExecutable', ' ')


if __name__ == '__main__':
    setupParameters()
