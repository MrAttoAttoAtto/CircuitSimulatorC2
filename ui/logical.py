from ui.visuals import GraphicalGround
from ui.visuals import GraphicalResistor, GraphicalVoltageSource, GraphicalDiode

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
    # Type then display name then unit then unit tooltip
    ATTRIBUTES = {'resistance': [float, "Resistance", "Ω", "Ohms"]}
    DEFAULT_ATTRIBUTES = {'resistance': 1.0}

    def __init__(self):
        self.attributes = Resistor.DEFAULT_ATTRIBUTES.copy()
        self.graphic = None


class VoltageSource:
    NAME = "Voltage Source"
    DISPLAY = GraphicalVoltageSource
    # Type then display name
    ATTRIBUTES = {'voltage': [float, "Voltage", "V", "Volts"]}
    DEFAULT_ATTRIBUTES = {'voltage': 9.0}

    def __init__(self):
        self.attributes = VoltageSource.DEFAULT_ATTRIBUTES.copy()
        self.graphic = None


class Diode:
    NAME = "Diode"
    DISPLAY = GraphicalDiode
    # Type then display name
    ATTRIBUTES = {'breakdownVoltage': [float, "Breakdown Voltage", "V", "Volts"],
                  'saturationCurrent': [float, "Saturation Current", "A", "Amps"],
                  'ideality': [float, "Ideality", " ", "Dimensionless"]}
    DEFAULT_ATTRIBUTES = {'breakdownVoltage': 40.0,
                          'saturationCurrent': 1e-12,
                          'ideality': 1.0}

    def __init__(self):
        self.attributes = Diode.DEFAULT_ATTRIBUTES.copy()
        self.graphic = None


COMPONENTS = [Resistor, ReferenceNode, VoltageSource, Diode]
