import sys
import traceback

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QMessageBox, QFileDialog, QGraphicsView, QSplitter
from pyqtgraph import PlotWidget

from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import StaticSimulation
from ui import persistence
from ui.CircuitScene import CircuitScene
from ui.GraphicalComponents import GraphicalGround, COMPONENTS, CircuitSymbol, CircuitWire, GraphicalTestPoint
from ui.ResultsView import ResultsView
from ui.SimulationWorker import TransientWorker
from ui.persistence import ProgramSettings
from ui.utils import follow_duplications
from ui.visuals import CircuitView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.next_id = 0

        self.edited = False
        self.currentFile = None

        self.settings = ProgramSettings()

        self.current_simulation = None
        self.splitter = QSplitter(Qt.Vertical, self)
        self.mscene = CircuitScene(self)

        self.mview = CircuitView(self.mscene)
        self.mview.setDragMode(QGraphicsView.RubberBandDrag)
        self.splitter.addWidget(self.mview)
        pg.setConfigOption("foreground", 'k')
        self.resultsView = ResultsView()
        self.splitter.addWidget(self.resultsView)
        self.setResultsVisible(False)

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
                sim = StaticSimulation(circuit, self.settings.get("convergenceLimit"))
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

                    self.runDynamicAction.setDisabled(False)
                    self.runStaticAction.setDisabled(False)
                    return

                self.resultsView.displayStaticData(circuit, components)
                self.setResultsVisible(True)
                self.runDynamicAction.setDisabled(False)
                self.runStaticAction.setDisabled(False)
            else:
                # Dynamic
                maxGraphSteps = self.settings.get("graphTimeRange") // self.settings.get("simulationFidelity")
                (watchedNodes, watchedCurrents) = self.resultsView.prepareTransient(circuit, components, maxGraphSteps)

                self.current_simulation = TransientWorker(circuit, watchedNodes, watchedCurrents, self.settings.get("convergenceLimit"),
                                                          self.settings.get("timeBase"),
                                                          self.settings.get("simulationFidelity"))

                self.current_simulation.onStep.connect(self.resultsView.updateTransientData)
                self.current_simulation.onError.connect(self.onSimulationError)
                self.current_simulation.start()
                self.setResultsVisible(True)
                self.stopDynamicAction.setDisabled(False)

    def onSimulationError(self, e: Exception):
        self.current_simulation.halt()
        self.current_simulation = None
        self.stopDynamicAction.setDisabled(True)
        self.runDynamicAction.setDisabled(False)
        self.runStaticAction.setDisabled(False)
        errorBox = QMessageBox()
        errorBox.setText(f"The simulation failed with error {e.__class__.__name__}")
        errorBox.setInformativeText(f'"{str(e)}"')
        errorBox.setDetailedText(''.join(traceback.format_exception(e.__class__, e, e.__traceback__)))
        errorBox.setWindowTitle("Circuit Failure")
        errorBox.setIcon(QMessageBox.Warning)

        errorBox.exec()

    def checkTransientResults(self, result):
        self.resultsView.updateTransientData(result)

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
            c.populateName(self.mscene.componentNames)
            self.setEdited()

        return addComponent

    def onSwitchStateChange(self, newState: bool, uid: int):
        if self.current_simulation:
            self.current_simulation.notifySwitchStateChanged(newState, uid)

    def setResultsVisible(self, visible: bool = True):
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

        settingsAction = QAction("Settings", menuBar)
        settingsAction.triggered.connect(self.settings.displayDialog)
        fileMenu.addAction(settingsAction)

        fileMenu.addSeparator()

        closeAction = QAction("Quit", menuBar)
        closeAction.triggered.connect(self.close)
        closeAction.setShortcut(QKeySequence("Ctrl+Q"))
        fileMenu.addAction(closeAction)

        editMenu = menuBar.addMenu("Edit")

        rotateRightAction = QAction("Rotate Right", menuBar)
        rotateRightAction.triggered.connect(self.mscene.rotateSelected)
        rotateRightAction.setShortcut(QKeySequence("Ctrl+R"))
        editMenu.addAction(rotateRightAction)

        rotateLeftAction = QAction("Rotate Left", menuBar)
        rotateLeftAction.triggered.connect(lambda: self.mscene.rotateSelected(True))
        rotateLeftAction.setShortcut(QKeySequence("Ctrl+L"))
        editMenu.addAction(rotateLeftAction)

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
            self.mscene.componentNames = set()

            self.setWindowTitle("Circuit Simulator")

            return True

        return False

    def open(self):
        fileName = QFileDialog.getOpenFileName(self, "Open...", None, "Circuit Files (*.cir)",
                                               "Circuit Files (*.cir)")[0]

        if fileName == "" or not self.new():
            return

        with open(fileName, 'r') as fil:
            data = fil.read()

        self.next_id = persistence.load(self.mscene, data)

        self.currentFile = fileName
        self.statusBar().showMessage("File opened successfully.")
        self.setWindowTitle(f"Circuit Simulator ({self.currentFile})")
        self.edited = False

        return True

    def save(self):
        if self.currentFile is None:
            return self.saveAs()

        saveText = persistence.dump(self.mscene)

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
    sys.exit(app.exec_())
