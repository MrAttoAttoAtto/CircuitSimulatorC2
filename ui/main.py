from PyQt5.QtWidgets import QMainWindow, QApplication, QAction

from ui.logical import COMPONENTS, ReferenceNode
from ui.logical import Diode
from ui.visuals import CircuitScene, CircuitNode, CircuitView, GraphicalDiode


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.components = []
        self.initUI()

    def initUI(self):
        self.mscene = CircuitScene()

        self.mscene.addText("Hello")
        self.mnoot = CircuitNode()
        self.mnoot2 = CircuitNode(50, 0)
        self.mscene.addItem(self.mnoot)
        self.mscene.addItem(self.mnoot2)

        self.mres = GraphicalDiode(20, 100, Diode())
        self.mscene.addItem(self.mres)

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
        print(self.components)
        gnd_components = list(filter(lambda x: x is ReferenceNode, self.components))
        if len(gnd_components) > 0:
            for gnd in gnd_components:
                gnd.graphic.nodes[0].actual_node = 0
        else:
            self.statusBar().showMessage("need ground node.")
    def addComponent(self, component_class):
        c = component_class()
        self.mscene.addComponent(0, 0, c)
        self.components.append(c)

    def createActions(self):
        toolbar = self.addToolBar("Components")
        for c in COMPONENTS:
            action = QAction(c.NAME, toolbar)
            action.triggered.connect(lambda: self.addComponent(c))
            toolbar.addAction(action)
        toolbar.addSeparator()
        runAction = QAction("Run", toolbar)
        runAction.triggered.connect(self.run)
        toolbar.addAction(runAction)


if __name__ == '__main__':
    app = QApplication([])
    wind = MainWindow()
    exit(app.exec_())
