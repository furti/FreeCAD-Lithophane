import traceback, time
import FreeCAD
from PySide import QtGui

import logger

def processEvents():
  time.sleep(0.001)
  QtGui.QApplication.processEvents()

class TestCase():
    def __init__(self, func):
        self.func = func
        self.success = False
        self.error = None
        self.handleDocument = True
        self.Document = None
    
    def run(self):
        try:
            self.setupTest()

            self.func()

            self.success = True
        except AssertionError as e:
            self.success = False
            self.error = traceback.format_exc()
        except AttributeError as e:
            self.success = False
            self.error = traceback.format_exc()
        
        self.tearDownTest()

    def setupTest(self):
        if self.handleDocument:
            self.Document = FreeCAD.newDocument(self.func.__name__)
    
    def tearDownTest(self):
        if self.handleDocument:
            FreeCAD.closeDocument(self.Document.Name)
            self.Document = None

    def describe(self):
        return self.func.__name__

class TestRunner():
    def __init__(self):
        self.numberOfTests = 0
        self.testCasesByModule = {}
    
    def addTests(self, module):
        for testMethod in module.collectTests():
            self.numberOfTests +=1

            moduleName = extractModuleName(module)

            if not moduleName in self.testCasesByModule:
                self.testCasesByModule[moduleName] = []
            
            self.testCasesByModule[moduleName].append(TestCase(testMethod))
    
    def outputTestsToRun(self):
        logger.logLine('Got %s Tests to run' % (self.numberOfTests))

        for module, testCases in self.testCasesByModule.items():
            logger.logLine(module)

            for testCase in testCases:
                logger.logLine('    %s' % (testCase.describe()))
        
        processEvents()

    def runTests(self):
        logger.logLine('')
        logger.logLine('Starting tests...')
        
        for module, testCases in self.testCasesByModule.items():
            logger.logLine(module)

            for testCase in testCases:
                logger.logLine('    %s' % (testCase.describe()))

                testCase.run()

                processEvents()
    
    def printTestResults(self):
        logger.logLine('')
        logger.logLine('Test Results')

        for module, testCases in self.testCasesByModule.items():
            logger.logLine(module)

            for testCase in testCases:
                logger.logLine('    %s - %s' % (testCase.describe(), testCase.success))

                if not testCase.success:
                    logger.logLine(testCase.error)

    def run(self):
        self.outputTestsToRun()
        self.runTests()
        self.printTestResults()

def extractModuleName(module):
    return module.__name__