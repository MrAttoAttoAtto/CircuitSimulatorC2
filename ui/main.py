from PyQt5.QtWidgets import QMainWindow, QApplication, QAction

from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import StaticSimulation
from ui.CircuitScene import CircuitScene
from ui.GraphicalComponents import GraphicalGround, COMPONENTS, CircuitSymbol, CircuitWire, \
    GraphicalTestPoint
from ui.SimulationWorker import TransientWorker
from ui.utils import follow_duplications
from ui.visuals import CircuitView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.nodes_valid_state = False
        self.current_simulation = None
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

    def run(self, static: bool):
        if self.current_simulation is not None:
            raise Exception("Shouldn't Happen")
        components = list(filter(lambda item: isinstance(item, CircuitSymbol), self.mscene.items()))
        # Reset node assignments
        for c in components:
            for n in c.nodes:
                n.actual_node = -1
        # Locate ground nodes
        gnd_components = list(filter(lambda x: isinstance(x, GraphicalGround), components))
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
                n1, n2 = follow_duplications(node_duplications, n1), follow_duplications(node_duplications, n2)
                if n1 != n2:
                    # Map base nodes to each other
                    node_duplications[n1] = n2
        for c in components:
            for n in c.nodes:
                n.actual_node = follow_duplications(node_duplications, n.actual_node)
            # Add to circuit
            c.addToCircuit(circuit)
        if len(components):
            circuit.finalise(gnd_components[0].nodes[0].actual_node)
            self.runStaticAction.setDisabled(True)
            self.runDynamicAction.setDisabled(True)
            if static:
                sim = StaticSimulation(circuit, 10000)
                sim.simulate()
                self.nodes_valid_state = True
                for p in filter(lambda c: isinstance(c, GraphicalTestPoint), self.mscene.items()):
                    print(p.nodes[0].actual_node, circuit.getInputReference(p.nodes[0].actual_node))
                self.runDynamicAction.setDisabled(False)
                self.runStaticAction.setDisabled(False)
            else:
                # Dynamic
                watchedNodes = [p.nodes[0].actual_node for p in
                                filter(lambda c: isinstance(c, GraphicalTestPoint), self.mscene.items())]
                self.current_simulation = TransientWorker(circuit, watchedNodes)
                self.current_simulation.onStep.connect(self.checkTransientResults)
                self.current_simulation.start()
                self.nodes_valid_state = False
                self.stopDynamicAction.setDisabled(False)

    def checkTransientResults(self, result):
        self.nodes_valid_state = True
        print(result)

    def stopTransientSimulation(self):
        self.current_simulation.halt()
        self.stopDynamicAction.setDisabled(True)
        self.runDynamicAction.setDisabled(False)
        self.runStaticAction.setDisabled(False)

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
        self.runStaticAction = QAction("Run Static", toolbar)
        self.runStaticAction.triggered.connect(lambda: self.run(True))
        self.runDynamicAction = QAction("Run Dynamic", toolbar)
        self.runDynamicAction.triggered.connect(lambda: self.run(False))
        self.stopDynamicAction = QAction("Stop", toolbar)
        self.stopDynamicAction.triggered.connect(self.stopTransientSimulation)
        self.stopDynamicAction.setDisabled(True)
        toolbar.addAction(self.runStaticAction)
        toolbar.addAction(self.runDynamicAction)
        toolbar.addAction(self.stopDynamicAction)


def run():
    app = QApplication([])
    wind = MainWindow()
    exit(app.exec_())
