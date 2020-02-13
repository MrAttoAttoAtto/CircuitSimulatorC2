from PyQt5.QtWidgets import QMainWindow, QApplication, QAction

from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import StaticSimulation
from ui.CircuitScene import CircuitScene
from ui.GraphicalComponents import GraphicalDiode, GraphicalGround, COMPONENTS, CircuitSymbol, CircuitWire, \
    GraphicalTestPoint
from ui.utils import follow_duplications
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
        # Reset node assignments
        for c in components:
            for n in c.nodes:
                n.actual_node = -1
        print(components)
        # Locate ground nodes
        gnd_components = list(filter(lambda x: isinstance(x, GraphicalGround), components))
        print(gnd_components)
        if len(gnd_components) > 0:
            for gnd in gnd_components:
                gnd.nodes[0].assignActualNode(0)
        else:
            self.statusBar().showMessage("Ground node required.")

        env = Environment()
        circuit = Circuit(env)

        # Now we blindly assign nodes to all nodes
        node_count = 1
        # Nodes that actually are the same are stored here
        node_duplications = {}
        for c in components:
            for n in c.nodes:
                if n.actual_node == -1:
                    n.assignActualNode(node_count)
                    node_count += 1
            # Now wires need to 'elide' nodes - equal the numbers across them
            if isinstance(c, CircuitWire):
                n1, n2 = c.nodes[0].actual_node, c.nodes[1].actual_node
                print(n1, n2)
                n1, n2 = follow_duplications(node_duplications, n1), follow_duplications(node_duplications, n2)
                print(n1, n2)
                if n1 != n2:
                    # Map base nodes to each other
                    node_duplications[n1] = n2
        print("----")
        for c in components:
            print(c.NAME)
            for n in c.nodes:
                print(n.actual_node, "->", follow_duplications(node_duplications, n.actual_node))
                n.actual_node = follow_duplications(node_duplications, n.actual_node)
            if isinstance(c, CircuitWire):
                print(c.nodes[0].actual_node, c.nodes[1].actual_node)
            # Add to circuit
            c.addToCircuit(circuit)
        print(node_duplications)
        if len(components):
            for c in components:
                print(c.NAME)
                for n in c.nodes:
                    print(n.actual_node)
            circuit.finalise(gnd_components[0].nodes[0].actual_node)
            sim = StaticSimulation(circuit, 10000)
            sim.simulate()
            for p in filter(lambda c: isinstance(c, GraphicalTestPoint), components):
                print(p.nodes[0].actual_node, circuit.getInputReference(p.nodes[0].actual_node))



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


def run():
    app = QApplication([])
    wind = MainWindow()
    exit(app.exec_())
