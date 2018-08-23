import FreeCAD

class LengthUnit:
    def __init__(self, label, factor):
        self.label = label
        self.factor = factor
    
    def fromMm(self, valueInMm):
        return valueInMm * self.factor

LENGTH_UNITS = [LengthUnit('mm', 1), LengthUnit('m', 0.001), LengthUnit('in', 0.0393701), LengthUnit('in', 0.0393701), LengthUnit('cm', 0.1)]

def getIntParam(paramName, valueName):
    parms = FreeCAD.ParamGet(paramName)
    
    return parms.GetInt(valueName, 0)

def getLengthUnit():
    unitValue = getIntParam("User parameter:BaseApp/Preferences/Units", 'UserSchema')

    return LENGTH_UNITS[unitValue]

def getNumberOfDecimals():
    return getIntParam("User parameter:BaseApp/Preferences/Units", 'Decimals')

def formatLength(value):
    lengthUnit = getLengthUnit()
    numberOfDecimals = getNumberOfDecimals()

    formatString = '%.' + str(numberOfDecimals) + 'f %s'

    return formatString % (lengthUnit.fromMm(value), lengthUnit.label)

if __name__ == "__main__":
    FreeCAD.Console.PrintMessage(formatLength(10.123456789) + "\n")