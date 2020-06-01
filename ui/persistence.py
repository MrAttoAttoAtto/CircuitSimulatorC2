from PyQt5.QtCore import QPointF, QSettings, Qt
from PyQt5.QtWidgets import QDialog, QLineEdit, QDialogButtonBox, QVBoxLayout, QMessageBox, QGridLayout, \
    QLabel

from ui.CircuitScene import CircuitScene
from ui.GraphicalComponents import CircuitWire, COMPONENTS, CircuitSymbol
from ui.UberPath import UberPath


class ProgramSettings:
    """Maintains program-wide user adjustable settings, and logic for the settings dialog."""

    # key: (human-readable name, unit, type, default)
    SETTINGS = {
        "convergenceLimit": ("Convergence Limit", " ", int, 10000),
        "timeBase": ("Time Base", "s", float, 1e-5),
        "simulationFidelity": ("Simulation Update Interval", "s", float, 1e-2),
        "graphTimeRange": ("Graph Time Range", "s", float, 5.0)
    }

    def __init__(self):
        self._settings = QSettings("bekos", "CircuitSimulatorC2")
        # Load with defaults
        self.settings = {key: self._settings.value(key, self.SETTINGS[key][3], self.SETTINGS[key][2]) for key in
                         self.SETTINGS.keys()}

    def get(self, key):
        return self.settings[key]

    def set(self, key, value):
        val = self.SETTINGS[key][2](value)
        self.settings[key] = val
        self._settings.setValue(key, val)

    def displayDialog(self):
        dialog = QDialog()
        dialog.setWindowTitle("Settings")

        gridLayout = QGridLayout()
        entryComponents = {}
        for i, key in enumerate(self.SETTINGS.keys()):
            entryWidget = QLineEdit()
            entryWidget.setText(str(self.get(key)))
            label = QLabel(f"{self.SETTINGS[key][0]}:")
            unitLabel = QLabel(self.SETTINGS[key][1])

            entryComponents[key] = entryWidget

            gridLayout.addWidget(label, i, 0)
            gridLayout.addWidget(entryWidget, i, 1)
            gridLayout.addWidget(unitLabel, i, 2)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        def saveSettings():
            tempMap = {}
            for key, component in entryComponents.items():
                try:
                    tempMap[key] = self.SETTINGS[key][2](component.text())
                except ValueError as e:
                    messageBox = QMessageBox()
                    messageBox.setText(f"An invalid parameter was specified for {self.SETTINGS[key][0]}")
                    messageBox.setInformativeText("Please enter another value")
                    messageBox.setDetailedText(f"{type(e).__name__}: {str(e)}")
                    messageBox.setWindowTitle("Invalid parameter")
                    messageBox.setIcon(QMessageBox.Warning)
                    messageBox.exec()
                    return
            for key, value in tempMap.items():
                if value != self.get(key):
                    self.set(key, value)
            dialog.close()

        buttonBox.rejected.connect(dialog.close)
        buttonBox.accepted.connect(saveSettings)

        vlayout = QVBoxLayout()
        vlayout.addLayout(gridLayout)
        vlayout.addWidget(buttonBox)
        dialog.setLayout(vlayout)
        dialog.exec_()


def load(scene: CircuitScene, data: str):
    next_id = 0
    lines = data.split("\n")
    nodeLine = lines[0]
    componentLines = lines[1:]

    nodeDict = {}
    for componentLine in componentLines:
        name, parameters, nodes, position = componentLine.split(":")

        # Patch 2 for old files
        if parameters == "":
            parameters = "rotation=0"
        # End patch 2

        parameterStringDict = {parameter: value
                               for parameter, value in [pair.split("=") for pair in parameters.split(",")]}

        # Also a patch
        if parameterStringDict.get("rotation") is not None:
            rotation = float(parameterStringDict["rotation"])
            del parameterStringDict["rotation"]
        else:
            rotation = 0
        # End also patch

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

            newComponent = CircuitWire(newUberPath, next_id)
        else:
            x, y = position.split(",")
            newComponent = COMPONENTS[name](next_id, float(x), float(y))

            parameterDict = {parameter: newComponent.ATTRIBUTES[parameter][0](value)
                             for parameter, value in parameterStringDict.items()}

            newComponent.attributes = parameterDict

        newComponent.setRotation(rotation)

        next_id += 1
        nodes = [int(node) for node in nodes.split(",")]
        nodeDict.update({nodeIndex: nodeObject for nodeIndex, nodeObject in zip(nodes, newComponent.nodes)})
        # Begin Patch 1
        if "name" not in newComponent.attributes:
            newComponent.attributes["name"] = ""
        # End Patch 1
        # Begin Patch 2
        if "colour" not in newComponent.attributes and "colour" in newComponent.ATTRIBUTES:
            newComponent.attributes["colour"] = Qt.black
        # End Patch 2
        newComponent.populateName(scene.componentNames)
        scene.addItem(newComponent)

    for nodeConnections in nodeLine.split(":"):
        node, connects = nodeConnections.split("=")

        # This node isn't connected to anything
        if connects == "":
            continue

        nodeObject = nodeDict[int(node)]
        connectObjects = [nodeDict[int(connect)] for connect in connects.split(',')]

        for connectObject in connectObjects:
            nodeObject.connect(connectObject)

    return next_id


def dump(scene: CircuitScene):
    components = list(filter(lambda item: isinstance(item, CircuitSymbol), scene.items()))

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
        if component.attributes.get("rotation") is None:
            component.attributes["rotation"] = component.rotation()

        parameterString = ""
        for parameter, value in component.attributes.items():
            if len(parameterString) > 0:
                parameterString += ","

            if parameter == "colour":
                parameterString += f"{parameter}={value.rgb()}"
            else:
                parameterString += f"{parameter}={value}"

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

    return saveText
