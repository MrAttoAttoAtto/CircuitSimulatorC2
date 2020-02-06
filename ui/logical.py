from ui.visuals import GraphicalResistor, GraphicalGround, GraphicalVoltageSource

class CircuitBuilder:
    def __init__(self):
        self.currentNode = 0

    def allocateNode(self):
        n = self.currentNode
        self.currentNode += 1
        return n

class ReferenceNode:
    NAME = "Ground"
    DISPLAY = GraphicalGround
    ATTRIBUTES = {}
    DEFAULT_ATTRIBUTES = {}

    def __init__(self):
        self.attributes = {}
        self.graphic = None

class Resistor:
    NAME = "Resistor"
    DISPLAY = GraphicalResistor
    # Type then display name
    ATTRIBUTES = {'resistance': [float, "Resistance"]}
    DEFAULT_ATTRIBUTES = {'resistance': 1.0}

    def __init__(self):
        self.attributes = Resistor.DEFAULT_ATTRIBUTES.copy()
        self.graphic = None

class VoltageSource:
    NAME = "Voltage Source"
    DISPLAY = GraphicalVoltageSource
    # Type then display name
    ATTRIBUTES = {'voltage': [float, "Voltage"]}
    DEFAULT_ATTRIBUTES = {'voltage': 9.0}

    def __init__(self):
        self.attributes = VoltageSource.DEFAULT_ATTRIBUTES.copy()
        self.graphic = None

COMPONENTS = [Resistor, ReferenceNode, VoltageSource]

