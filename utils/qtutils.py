IS_QT_5 = False

if IS_QT_5:
    from PySide2 import QtGui, QtCore, QtWidgets
    IS_QT_5 = True
else:
    from PySide import QtGui, QtCore
    import PySide.QtGui as QtWidgets

import time

# Common classes
QByteArray = QtCore.QByteArray
QBuffer = QtCore.QBuffer
QIODevice = QtCore.QIODevice
Qt = QtCore.Qt
QImage = QtGui.QImage
QColor = QtGui.QColor
QDialog = QtWidgets.QDialog
QLabel = QtWidgets.QLabel
QVBoxLayout = QtWidgets.QVBoxLayout
QScrollArea = QtWidgets.QScrollArea
QPalette = QtWidgets.QPalette
QSizePolicy = QtWidgets.QSizePolicy
QPixmap = QtWidgets.QPixmap
QThread = QtCore.QThread

# File patterns
IMAGE_FILES = "Image Files (*.png *.jpg *.bmp)"

def qgray(qColor):
    return (qColor.red() * 11 + qColor.green() * 16 + qColor.blue() * 5)/32

def activeWindow():
    return QtWidgets.QApplication.activeWindow()

def userSelectedFile(title, filePattern):
    fileName = QtWidgets.QFileDialog.getOpenFileName(activeWindow(), title, '', filePattern)[0]

    if fileName == '':
        return None

    return fileName

def showInfo(title, message):
    QtWidgets.QMessageBox.information(activeWindow(), title, message)

def readImage(imagePath):
    imageReader = QtGui.QImageReader(imagePath)

    if imageReader.canRead():
        image = imageReader.read() 

        if image.isNull():
            showInfo("Image Read Error", "Can't read image: %s" % imageReader.errorString())

        return image
    else:
        showInfo("Image Read Error", "Can't read image: %s" % imageReader.errorString())

def processEvents():
    QtGui.QApplication.processEvents()
    time.sleep(0.1)

 
# https://github.com/PySide/pyside2/wiki/My_Practice_:_Porting_python_scripts_to_PySide2#qhboxlayout-qvboxlayout
# important info about layout in qt4 and qt5