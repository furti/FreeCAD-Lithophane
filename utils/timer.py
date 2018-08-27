import FreeCAD
import time

import utils.qtutils as qtutils

class Timer:
    def __init__(self, message):
        self.message = message
        self.start()

    def start(self):
        FreeCAD.Console.PrintMessage('Start: %s...\n' % (self.message))
        qtutils.processEvents()

        self.startSeconds = time.time()



    def stop(self):
        endSeconds = time.time()

        self.seconds = endSeconds - self.startSeconds

        FreeCAD.Console.PrintMessage('Finished: %s (%.3f s)\n' % (self.message, self.seconds))
        qtutils.processEvents()

def computeOverallTime(timers):
    return sum(map(lambda timer: timer.seconds, timers))