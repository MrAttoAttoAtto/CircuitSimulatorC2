import traceback

from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QMessageBox, QFileDialog, QGraphicsView, QSplitter
from pyqtgraph import PlotWidget

from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import StaticSimulation
from ui.CircuitScene import CircuitScene
from ui.GraphicalComponents import GraphicalGround, COMPONENTS, CircuitSymbol, CircuitWire, \
    GraphicalTestPoint
from ui.SimulationWorker import TransientWorker
from ui.UberPath import UberPath
from ui.utils import follow_duplications
from ui.visuals import CircuitView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.next_id = 0

        self.edited = False
        self.currentFile = None

        self.nodes_valid_state = False
        self.current_simulation = None
        self.splitter = QSplitter(Qt.Vertical, self)
        self.mscene = CircuitScene(self)

        self.mview = CircuitView(self.mscene)
        self.mview.setDragMode(QGraphicsView.RubberBandDrag)
        self.splitter.addWidget(self.mview)
        self.graphView = PlotWidget()
        self.splitter.addWidget(self.graphView)
        self.setGraphVisible(False)

        self.setCentralWidget(self.splitter)
        self.createActions()
        self.createMenuBar()
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
            return

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
                try:
                    sim.simulate()
                except Exception as e:
                    errorBox = QMessageBox()
                    errorBox.setText(f"The simulation failed with error {e.__class__.__name__}")
                    errorBox.setInformativeText(f'"{str(e)}"')
                    errorBox.setDetailedText(''.join(traceback.format_exception(e.__class__, e, e.__traceback__)))
                    errorBox.setWindowTitle("Circuit Failure")
                    errorBox.setIcon(QMessageBox.Warning)

                    errorBox.exec()
                    return

                self.nodes_valid_state = True
                for p in filter(lambda c: isinstance(c, GraphicalTestPoint), self.mscene.items()):
                    print(p.nodes[0].actual_node, circuit.getInputReference(p.nodes[0].actual_node))
                self.runDynamicAction.setDisabled(False)
                self.runStaticAction.setDisabled(False)
            else:
                # Dynamic
                watchedNodes = [p.nodes[0].actual_node for p in
                                filter(lambda c: isinstance(c, GraphicalTestPoint), self.mscene.items())]
                plot = self.graphView.getPlotItem()
                plot.clear()
                self.graphedNodes = {n: [plot.plot(pen=(i, len(watchedNodes))), [[], []]] for i, n in
                                     enumerate(watchedNodes)}
                self.current_simulation = TransientWorker(circuit, watchedNodes)
                self.current_simulation.onStep.connect(self.checkTransientResults)
                self.current_simulation.start()
                self.setGraphVisible(True)
                self.nodes_valid_state = False
                self.stopDynamicAction.setDisabled(False)

    def checkTransientResults(self, result):
        self.nodes_valid_state = True
        for node in self.graphedNodes.keys():
            # Update data
            self.graphedNodes[node][1][0].append(result[0])
            self.graphedNodes[node][1][1].append(result[1][node])
            self.graphedNodes[node][0].setData(self.graphedNodes[node][1][0], self.graphedNodes[node][1][1])

    def stopTransientSimulation(self):
        self.current_simulation.halt()
        self.current_simulation = None
        self.stopDynamicAction.setDisabled(True)
        self.runDynamicAction.setDisabled(False)
        self.runStaticAction.setDisabled(False)

    def addComponentFactory(self, component_class):
        def addComponent():
            c = component_class(self.next_id, 0, 0)
            self.next_id += 1
            self.mscene.addItem(c)
            self.setEdited()

        return addComponent

    def onSwitchStateChange(self, newState: bool, uid: int):
        if self.current_simulation:
            self.current_simulation.notifySwitchStateChanged(newState, uid)

    def setGraphVisible(self, visible: bool = True):
        h = self.splitter.geometry().height()
        if visible:
            # Dont adjust if already custom
            if self.splitter.sizes()[1] == 0:
                self.splitter.setSizes([int(h * 0.6), int(h * 0.4)])
        else:
            self.splitter.setSizes([h, 0])

    def createActions(self):
        toolbar = self.addToolBar("Components")

        for c in COMPONENTS.values():
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

    def createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("File")

        newAction = QAction("New", menuBar)
        newAction.triggered.connect(self.new)
        newAction.setShortcut(QKeySequence("Ctrl+N"))
        fileMenu.addAction(newAction)

        openAction = QAction("Open", menuBar)
        openAction.triggered.connect(self.open)
        openAction.setShortcut(QKeySequence("Ctrl+O"))
        fileMenu.addAction(openAction)

        fileMenu.addSeparator()

        saveAction = QAction("Save", menuBar)
        saveAction.triggered.connect(self.save)
        saveAction.setShortcut(QKeySequence("Ctrl+S"))
        fileMenu.addAction(saveAction)

        saveAsAction = QAction("Save As...", menuBar)
        saveAsAction.triggered.connect(self.saveAs)
        saveAsAction.setShortcut(QKeySequence("Shift+Ctrl+S"))
        fileMenu.addAction(saveAsAction)

        fileMenu.addSeparator()

        closeAction = QAction("Quit", menuBar)
        closeAction.triggered.connect(self.close)
        closeAction.setShortcut(QKeySequence("Ctrl+Q"))
        fileMenu.addAction(closeAction)

    def setEdited(self):
        self.edited = True
        if self.currentFile is not None:
            self.setWindowTitle(f"Circuit Simulator ({self.currentFile}*)")

    def new(self):
        if self.saveCheck():
            if self.current_simulation:
                self.stopTransientSimulation()
                self.current_simulation = None

            self.next_id = 0
            self.currentFile = None
            self.edited = False

            self.mscene.clear()

            self.setWindowTitle("Circuit Simulator")

            return True

        return False

    def open(self):
        fileName = QFileDialog.getOpenFileName(self, "Open...", None, "Circuit Files (*.cir)",
                                               "Circuit Files (*.cir)")[0]

        if fileName == "":
            return

        if not self.new():
            return

        with open(fileName, 'r') as fil:
            data = fil.read()

        lines = data.split("\n")
        nodeLine = lines[0]
        componentLines = lines[1:]

        nodeDict = {}
        for componentLine in componentLines:
            name, parameters, nodes, position = componentLine.split(":")

            if name == "Wire":
                newUberPath = UberPath()
                points = [QPointF(float(x), float(y)) for x, y in [pair.split(",") for pair in position.split(";")]]
                sourcePos = points[0]
                targetPos = points[-1]
                leftoverPoints = points[1:-1]

                newUberPath.sourcePos = sourcePos
                newUberPath.targetPos = targetPos

                newUberPath.setPos(sourcePos)
                newUberPath.addPoint(QPointF(0, 0))
                # Position is the sequence of points here
                [newUberPath.addPoint(point) for point in leftoverPoints]

                newUberPath.editPoint(-1, targetPos - sourcePos)

                newComponent = CircuitWire(newUberPath, self.next_id)
            else:
                x, y = position.split(",")
                newComponent = COMPONENTS[name](self.next_id, float(x), float(y))

                # If it has attributes...
                if parameters != "":
                    parameterDict = {parameter: newComponent.ATTRIBUTES[parameter][0](value)
                                     for parameter, value in [pair.split("=") for pair in parameters.split(",")]}
                    newComponent.attributes = parameterDict
            self.next_id += 1

            nodes = [int(node) for node in nodes.split(",")]
            nodeDict.update({nodeIndex: nodeObject for nodeIndex, nodeObject in zip(nodes, newComponent.nodes)})

            self.mscene.addItem(newComponent)

        for nodeConnections in nodeLine.split(":"):
            node, connects = nodeConnections.split("=")

            # This node isn't connected to anything
            if connects == "":
                continue

            nodeObject = nodeDict[int(node)]
            connectObjects = [nodeDict[int(connect)] for connect in connects.split(',')]

            for connectObject in connectObjects:
                nodeObject.connect(connectObject)

        self.currentFile = fileName
        self.statusBar().showMessage("File opened successfully.")
        self.setWindowTitle(f"Circuit Simulator ({self.currentFile})")
        self.edited = False

        return True

    def save(self):
        if self.currentFile is None:
            return self.saveAs()

        components = list(filter(lambda item: isinstance(item, CircuitSymbol), self.mscene.items()))

        nodes = [node for component in components for node in component.nodes]
        acceptedConnections = []
        nodeConnectionDict = {}
        for node in nodes:
            nodeIndex = nodes.index(node)
            connectedNodeIndices = [nodes.index(conn) for conn in node.connected]

            # Makes sure things are only connected once
            acceptedNodeConnections = []
            for connectedNodeIndex in connectedNodeIndices:
                if (nodeConnectionDict.get(nodeIndex) is None or
                        connectedNodeIndex not in nodeConnectionDict[nodeIndex]):
                    acceptedNodeConnections.append(connectedNodeIndex)
                    if nodeConnectionDict.get(connectedNodeIndex) is None:
                        nodeConnectionDict[connectedNodeIndex] = [nodeIndex]
                    else:
                        nodeConnectionDict[connectedNodeIndex].append(nodeIndex)

            acceptedConnections.append((nodeIndex, acceptedNodeConnections))

        nodeString = ':'.join(f"{conn[0]}={','.join(str(cted) for cted in conn[1])}" for conn in acceptedConnections)

        componentEntries = []
        for component in components:

            parameterString = ",".join(f"{parameter}={value}" for parameter, value in component.attributes.items())
            ownedNodes = ",".join(str(nodes.index(node)) for node in component.nodes)

            if component.NAME != "Wire":
                position = component.scenePos()
                positionString = f"{position.x()},{position.y()}"
            else:
                sourceString = f"{component.path.sourcePos.x()},{component.path.sourcePos.y()}"
                targetString = f"{component.path.targetPos.x()},{component.path.targetPos.y()}"
                positionString = sourceString + ';' + \
                                 ";".join(f"{point.x()},{point.y()}" for point in
                                          component.path._points) + ';' + targetString

            componentEntries.append(f"{component.NAME}:{parameterString}:{ownedNodes}:{positionString}")

        saveText = nodeString + "\n"
        saveText += '\n'.join(componentEntries)

        try:
            with open(self.currentFile, 'w+') as fil:
                fil.write(saveText)

            self.statusBar().showMessage("File saved successfully.")
            self.setWindowTitle(f"Circuit Simulator ({self.currentFile})")
            self.edited = False

            return True
        except Exception as e:
            errorBox = QMessageBox()
            errorBox.setText(f"Saving failed with error {e.__class__.__name__}")
            errorBox.setInformativeText(f'"{str(e)}"')
            errorBox.setDetailedText(''.join(traceback.format_exception(e.__class__, e, e.__traceback__)))
            errorBox.setWindowTitle("Save Failure")
            errorBox.setIcon(QMessageBox.Warning)

            errorBox.exec()

            return False

    def saveAs(self):
        fileName = QFileDialog.getSaveFileName(self, "Save As...", "untitled.cir", "Circuit Files (*.cir)",
                                               "Circuit Files (*.cir)")[0]

        if fileName != "":
            self.currentFile = fileName
            return self.save()

        return False

    def saveCheck(self):
        if self.edited:
            saveBox = QMessageBox()
            saveBox.setText(f"You have unsaved changes")
            saveBox.setInformativeText("Are you sure you want to close the current file? Unsaved changes will be lost.")
            saveBox.setWindowTitle("Unsaved Changes")
            saveBox.setIcon(QMessageBox.Question)
            saveBox.addButton(QMessageBox.Discard)
            saveBox.addButton(QMessageBox.Save)
            saveBox.addButton(QMessageBox.Cancel)
            saveBox.setDefaultButton(QMessageBox.Save)

            ret = saveBox.exec()

            if ret == QMessageBox.Cancel:
                return False
            elif ret == QMessageBox.Save:
                return self.save()
            else:
                return True

        return True

    def closeEvent(self, QCloseEvent):
        if self.saveCheck():
            if self.current_simulation is not None:
                self.current_simulation.halt()
            QCloseEvent.accept()
        else:
            QCloseEvent.ignore()


def run():
    app = QApplication([])
    wind = MainWindow()
    exit(app.exec_())
