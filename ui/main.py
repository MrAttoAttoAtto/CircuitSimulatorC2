from PyQt5.QtWidgets import QMainWindow, QApplication, QAction

from ui.CircuitScene import CircuitScene
from ui.GraphicalComponents import GraphicalDiode, GraphicalGround, COMPONENTS, CircuitSymbol
from ui.visuals import CircuitNode, CircuitView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.mscene = CircuitScene()

        self.mview = CircuitView(self.mscene)
        self.setCentralWidget(self.mview)
        self.createActions()
        self.statusBar().showMessage('Ready')
        self.resize(1920, 1080)
        self.activateWindow()
        self.setWindowTitle('Circuit Simulator')
        self.show()
        self.mview.zoomToFit()

    def run(self):
        components = list(filter(lambda item: isinstance(item, CircuitSymbol), self.mscene.items()))
        print(components)
        gnd_components = list(filter(lambda x: isinstance(x, GraphicalGround), components))
        if len(gnd_components) > 0:
            for gnd in gnd_components:
                gnd.nodes[0].actual_node = 0
        else:
            self.statusBar().showMessage("Ground node required.")

    def addComponentFactory(self, component_class):
        def addComponent():
            c = component_class(0, 0)
            self.mscene.addItem(c)

        return addComponent

    def createActions(self):
        toolbar = self.addToolBar("Components")

        for c in COMPONENTS:
            action = QAction(c.NAME, toolbar)
            action.triggered.connect(self.addComponentFactory(c))
            toolbar.addAction(action)

        toolbar.addSeparator()
        runAction = QAction("Run", toolbar)
        runAction.triggered.connect(self.run)
        toolbar.addAction(runAction)


if __name__ == '__main__':
    app = QApplication([])
    wind = MainWindow()
    exit(app.exec_())
