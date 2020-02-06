from PyQt5.QtWidgets import QMainWindow, QApplication, QAction

from ui.visuals import CircuitScene, CircuitNode, CircuitView, GraphicalResistor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.mscene = CircuitScene()

        self.mscene.addText("Hello")
        self.mnoot = CircuitNode()
        self.mnoot2 = CircuitNode(50, 0)
        self.mscene.addItem(self.mnoot)
        self.mscene.addItem(self.mnoot2)

        self.mres = GraphicalResistor(20, 100)
        self.mscene.addItem(self.mres)

        self.mview = CircuitView(self.mscene)
        self.setCentralWidget(self.mview)
        self.createActions()
        self.statusBar().showMessage('Ready')
        self.resize(1920, 1080)
        self.activateWindow()
        self.setWindowTitle('Statusbar')
        self.show()
        self.mview.zoomToFit()

    def createActions(self):
        toolbar = self.addToolBar("Components")
        toolbar.addAction(QAction("R", toolbar))


if __name__ == '__main__':
    app = QApplication([])
    wind = MainWindow()
    exit(app.exec_())