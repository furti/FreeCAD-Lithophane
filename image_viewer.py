from PySide import QtGui, QtCore

class ImageViewer(QtGui.QDialog):
    def __init__(self, image):
        super(ImageViewer, self).__init__(QtGui.qApp.activeWindow())

        self.imageLabel = QtGui.QLabel()
        self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        self.imageLabel.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Ignored)
        self.imageLabel.setScaledContents(True)
        self.imageLabel.setPixmap(QtGui.QPixmap.fromImage(image))

        layout = QtGui.QVBoxLayout()

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        self.scrollArea.setWidget(self.imageLabel)

        layout.addWidget(self.scrollArea)

        self.setLayout(layout)

        self.setWindowFlags(self.windowFlags()|QtCore.Qt.WindowMinMaxButtonsHint)
        self.setWindowTitle("Image Viewer")
        self.resize(500, 400)

        self.show()

if __name__ == "__main__":
    import os
    import FreeCAD
    imageFile = os.path.join(os.path.dirname(os.path.abspath(__file__)), './testimages/simple.png')
    FreeCAD.Console.PrintMessage(imageFile)

    imageReader = QtGui.QImageReader(imageFile)
    image = imageReader.read()

    if image.isNull():
         FreeCAD.Console.PrintMessage(imageReader.errorString())
    else:
        ImageViewer(image)