from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QSplitter, QTableWidgetItem, QLabel
from pyqtgraph import PlotWidget

from general.Circuit import Circuit
from ui.GraphicalComponents import CircuitSymbol, GraphicalTestPoint, GraphicalAmmeter, GraphicalVoltmeter


class ResultsView(QSplitter):
    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        self.dataBox = QLabel("")
        self.dataBox.setFont(font)
        self.dataBox.setContentsMargins(10, 10, 10, 10)
        self.voltageGraph = PlotWidget(background='w')
        self.currentGraph = PlotWidget(background='w')
        self.addWidget(self.dataBox)
        self.addWidget(self.voltageGraph)
        self.addWidget(self.currentGraph)
        self.ammeterMappings = {}
        self.nodeMappings = {}
        self.voltmeterMappings = {}
        self.maxDataLength = 0

    def displayStaticData(self, circuit: Circuit, graphicalComponents: [CircuitSymbol]):
        # Find ammeter stuff
        results = {}
        for gComp in graphicalComponents:
            if isinstance(gComp, GraphicalAmmeter):
                for cComp in circuit.components:
                    if cComp._patched_id == gComp.uid:
                        results[gComp.attributes["name"]] = str(cComp.currentThroughReference.value) + "A"
            elif isinstance(gComp, GraphicalTestPoint):
                results[gComp.attributes["name"]] = str(circuit.getInputReference(gComp.nodes[0].actual_node).value) + "V"
            elif isinstance(gComp, GraphicalVoltmeter):
                voltage = circuit.getInputReference(gComp.nodes[0].actual_node).value - circuit.getInputReference(gComp.nodes[1].actual_node).value
                results[gComp.attributes["name"]] = str(voltage) + "V"
        self.voltageGraph.hide()
        self.currentGraph.hide()
        s = "\n".join([f"{key}: {value:>10}" for key, value in results.items()])
        self.dataBox.setText(s)

    def prepareTransient(self, circuit: Circuit, graphicalComponents: [CircuitSymbol], maxDataLength: int):
        self.maxDataLength = maxDataLength
        # Find ammeter stuff
        ammeterComponents = []
        self.ammeterMappings = {}
        nodeWatches = set()
        self.nodeMappings = {}
        self.voltmeterMappings = {}
        for gComp in graphicalComponents:
            if isinstance(gComp, GraphicalAmmeter):
                for cComp in circuit.components:
                    if cComp._patched_id == gComp.uid:
                        ammeterComponents.append(gComp.uid)
                        self.ammeterMappings[gComp.attributes["name"]] = gComp.uid
            elif isinstance(gComp, GraphicalTestPoint):
                nodeWatches.add(gComp.nodes[0].actual_node)
                self.nodeMappings[gComp.attributes["name"]] = gComp.nodes[0].actual_node
            elif isinstance(gComp, GraphicalVoltmeter):
                nodeWatches.add(gComp.nodes[0].actual_node)
                nodeWatches.add(gComp.nodes[1].actual_node)
                self.voltmeterMappings[gComp.attributes["name"]] = (gComp.nodes[0].actual_node, gComp.nodes[1].actual_node)

        self.voltageGraph.show()
        self.currentGraph.show()
        self.voltageGraph.getPlotItem().clear()
        self.currentGraph.getPlotItem().clear()
        self.currentPlots = {name: (self.currentGraph.getPlotItem().plot(), []) for name in self.ammeterMappings}
        self.voltagePlots = {name: (self.voltageGraph.getPlotItem().plot(), []) for name in self.nodeMappings}
        self.voltagePlots.update({name: (self.voltageGraph.getPlotItem().plot(), []) for name in self.voltmeterMappings})
        self.timeAxis = []
        return nodeWatches, ammeterComponents

    def updateTransientData(self, incoming):
        self.timeAxis.append(incoming[0])
        if len(self.timeAxis) > self.maxDataLength:
            self.timeAxis.pop(0)
        for name, a in self.ammeterMappings.items():
            self.currentPlots[name][1].append(incoming[2][a])

            if len(self.currentPlots[name][1]) > self.maxDataLength:
                self.currentPlots[name][1].pop(0)
            self.currentPlots[name][0].setData(self.timeAxis, self.currentPlots[name][1])
        for name, (vm1, vm2) in self.voltmeterMappings.items():
            voltage = incoming[1][vm1] - incoming[1][vm2]
            self.voltagePlots[name][1].append(voltage)
            if len(self.voltagePlots[name][1]) > self.maxDataLength:
                self.voltagePlots[name][1].pop(0)
            self.voltagePlots[name][0].setData(self.timeAxis, self.voltagePlots[name][1])
        for name, v in self.nodeMappings.items():
            self.voltagePlots[name][1].append(incoming[1][v])
            if len(self.voltagePlots[name][1]) > self.maxDataLength:
                self.voltagePlots[name][1].pop(0)
            self.voltagePlots[name][0].setData(self.timeAxis, self.voltagePlots[name][1])
