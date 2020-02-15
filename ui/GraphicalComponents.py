from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QPolygonF, QPainterPathStroker, QPainterPath
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox, QGraphicsItem, \
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsPathItem

from components.ACVoltageSource import ACVoltageSource
from components.Capacitor import Capacitor
from components.Diode import Diode
from components.Inductor import Inductor
from components.MOSFET import MOSFET
from components.Resistor import Resistor
from components.Switch import Switch
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from ui.utils import defaultPen
from ui.visuals import CircuitItem, CircuitNode


class CircuitSymbol(CircuitItem):
    NAME = ""
    ATTRIBUTES = {}
    DEFAULT_ATTRIBUTES = {}

    def __init__(self, uid, x=0, y=0):
        super().__init__()
        self.uid = uid
        self.attributes = self.DEFAULT_ATTRIBUTES.copy()
        self.nodes = self.createNodes()
        self.decor = self.createDecor()

        for c in self.nodes:
            c.setParentItem(self)
        for c in self.decor:
            c.setParentItem(self)
            pen = QPen(defaultPen)
            c.setPen(pen)

        self.setPos(x, y)
        self.setAcceptHoverEvents(True)

    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
        if len(self.attributes) == 0:
            return

        dialog = QDialog()
        dialog.setWindowTitle(f"{self.NAME} Configuration")

        gridLayout = QGridLayout()
        attributeMap = {}
        for i, (name, (typ, displayName, unit, unitTooltip)) in enumerate(self.ATTRIBUTES.items()):
            label = QLabel(f"{displayName}:")
            entry = QLineEdit(f"{self.attributes[name]}")
            unitLabel = QLabel(unit)
            unitLabel.setCursor(Qt.WhatsThisCursor)
            unitLabel.setToolTip(unitTooltip)

            attributeMap[name] = entry

            gridLayout.addWidget(label, i, 0)
            gridLayout.addWidget(entry, i, 1)
            gridLayout.addWidget(unitLabel, i, 2)

        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        def recordValues():
            middlemanMap = {}
            for name, entry in attributeMap.items():
                try:
                    middlemanMap[name] = self.ATTRIBUTES[name][0](entry.text())
                except ValueError as e:
                    messageBox = QMessageBox()
                    messageBox.setText(f"An invalid parameter was specified for {self.ATTRIBUTES[name][1]}")
                    messageBox.setInformativeText("Please enter another value")
                    messageBox.setDetailedText(f"{type(e).__name__}: {str(e)}")
                    messageBox.setWindowTitle("Invalid parameter")
                    messageBox.setIcon(QMessageBox.Warning)

                    messageBox.exec()
                    return

            if self.attributes != middlemanMap:
                self.attributes = middlemanMap
                self.scene().parent().setEdited()
            dialog.close()

        buttonBox.accepted.connect(recordValues)
        buttonBox.rejected.connect(dialog.close)

        gridLayout.addWidget(buttonBox, i + 1, 1)
        dialog.setLayout(gridLayout)

        dialog.exec()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            scene = self.scene()
            if scene is not None:
                scene.parent().setEdited()
            for n in self.nodes:
                n.disconnect_all()
        return super().itemChange(change, value)

    def createNodes(self):
        raise NotImplementedError()

    def createDecor(self):
        raise NotImplementedError()

    def addToCircuit(self, circuit: Circuit):
        pass


class CircuitWire(CircuitSymbol):
    NAME = "Wire"
    ATTRIBUTES = {"caption": (str, "Caption", "", "")}
    DEFAULT_ATTRIBUTES = {"caption": ""}

    def createNodes(self):
        return [CircuitNode(),
                CircuitNode(self.path.path().currentPosition().x(), self.path.path().currentPosition().y())]

    def createDecor(self):
        return [self.path]

    def __init__(self, m_path, uid):
        self.path = m_path
        old_pos = m_path.pos()
        m_path.setPos(0, 0)
        super().__init__(uid, old_pos.x(), old_pos.y())

    def boundingRect(self):
        return self.path.boundingRect()

    def shape(self):
        s = QPainterPathStroker()
        s.setWidth(3)
        return s.createStroke(self.path.path())


class GraphicalResistor(CircuitSymbol):
    NAME = "Resistor"
    # Type then display name then unit then unit tooltip
    ATTRIBUTES = {'resistance': [float, "Resistance", "Ω", "Ohms"]}
    DEFAULT_ATTRIBUTES = {'resistance': 1.0}

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 80)]

    def createDecor(self):
        return [QGraphicsRectItem(5, 20, 10, 40),
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 60, 10, 80)]

    def boundingRect(self):
        return QRectF(5, 0, 10, 80)

    def addToCircuit(self, circuit: Circuit):
        res = Resistor(**self.attributes)
        res._patched_id = self.uid
        circuit.add(res, (self.nodes[0].actual_node, self.nodes[1].actual_node))


class GraphicalCapacitor(CircuitSymbol):
    NAME = "Capacitor"
    # Type then display name then unit then unit tooltip
    ATTRIBUTES = {'capacitance': [float, "Capacitance", "F", "Farads"]}
    DEFAULT_ATTRIBUTES = {'capacitance': 1.0}

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 50)]

    def createDecor(self):
        return [QGraphicsLineItem(0, 20, 20, 20),
                QGraphicsLineItem(0, 30, 20, 30),
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 30, 10, 50)]

    def boundingRect(self):
        return QRectF(0, 0, 20, 50)

    def addToCircuit(self, circuit: Circuit):
        cap = Capacitor(**self.attributes)
        cap._patched_id = self.uid
        circuit.add(cap, (self.nodes[0].actual_node, self.nodes[1].actual_node))


class GraphicalInductor(CircuitSymbol):
    NAME = "Inductor"
    # Type then display name then unit then unit tooltip
    ATTRIBUTES = {'inductance': [float, "Inductance", "H", "Henrys"]}
    DEFAULT_ATTRIBUTES = {'inductance': 1.0}

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 60)]

    def createDecor(self):
        curve = QPainterPath()
        curve.moveTo(10, 10)
        curve.arcTo(QRectF(5, 10, 10, 10), 90, -180)
        curve.arcTo(QRectF(5, 20, 10, 10), 90, -180)
        curve.arcTo(QRectF(5, 30, 10, 10), 90, -180)
        curve.arcTo(QRectF(5, 40, 10, 10), 90, -180)
        bumps = QGraphicsPathItem()
        bumps.setPath(curve)
        return [bumps,
                QGraphicsLineItem(10, 0, 10, 10),
                QGraphicsLineItem(10, 50, 10, 60)]

    def boundingRect(self):
        return QRectF(5, 0, 20, 60)

    def addToCircuit(self, circuit: Circuit):
        ind = Inductor(**self.attributes)
        ind._patched_id = self.uid
        circuit.add(ind, (self.nodes[0].actual_node, self.nodes[1].actual_node))


class GraphicalVoltageSource(CircuitSymbol):
    NAME = "Voltage Source"
    # Type then display name then unit then unit tooltip
    ATTRIBUTES = {'voltage': [float, "Voltage", "V", "Volts"]}
    DEFAULT_ATTRIBUTES = {'voltage': 9.0}

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 70)]

    def createDecor(self):
        return [QGraphicsEllipseItem(-5, 20, 30, 30),
                QGraphicsLineItem(10, 25, 10, 30),
                QGraphicsLineItem(7.5, 27.5, 12.5, 27.5),
                QGraphicsLineItem(7.5, 42.5, 12.5, 42.5),
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 50, 10, 70)]

    def boundingRect(self):
        return QRectF(-5, 0, 35, 70)

    def addToCircuit(self, circuit: Circuit):
        pwr = VoltageSource(**self.attributes)
        pwr._patched_id = self.uid
        circuit.add(pwr, (self.nodes[0].actual_node, self.nodes[1].actual_node))


class GraphicalACVoltageSource(CircuitSymbol):
    NAME = "AC Voltage Source"
    # Type then display name then unit then unit tooltip
    ATTRIBUTES = {'peakVoltage': [float, "Peak Voltage", "V", "Volts"],
                  'frequency': [float, "Frequency", "Hz", "Hertz"]}
    DEFAULT_ATTRIBUTES = {'peakVoltage': 9.0, 'frequency': 1.0}

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 70)]

    def createDecor(self):
        curve = QPainterPath()
        curve.moveTo(0, 35)
        curve.arcTo(QRectF(0, 30, 10, 10), 180, -180)
        curve.arcTo(QRectF(10, 30, 10, 10), 180, 180)
        sine = QGraphicsPathItem()
        sine.setPath(curve)
        return [QGraphicsEllipseItem(-5, 20, 30, 30),
                sine,
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 50, 10, 70)]

    def boundingRect(self):
        return QRectF(-5, 0, 35, 70)

    def addToCircuit(self, circuit: Circuit):
        pwr = ACVoltageSource(**self.attributes)
        pwr._patched_id = self.uid
        circuit.add(pwr, (self.nodes[0].actual_node, self.nodes[1].actual_node))


class GraphicalDiode(CircuitSymbol):
    NAME = "Diode"
    ATTRIBUTES = {'breakdownVoltage': [float, "Breakdown Voltage", "V", "Volts"],
                  'saturationCurrent': [float, "Saturation Current", "A", "Amps"],
                  'ideality': [float, "Ideality", " ", "Dimensionless"]}
    DEFAULT_ATTRIBUTES = {'breakdownVoltage': 40.0,
                          'saturationCurrent': 1e-12,
                          'ideality': 1.0}

    def createNodes(self):
        return [CircuitNode(10, 40), CircuitNode(10, 0)]

    def createDecor(self):
        triangle = QPolygonF([QPointF(0, 10 + 17.32), QPointF(20, 10 + 17.32), QPointF(10, 10)])
        return [QGraphicsLineItem(10, 0, 10, 10),
                QGraphicsLineItem(10, 10 + 17.32, 10, 40),
                QGraphicsPolygonItem(triangle),
                QGraphicsLineItem(0, 10, 20, 10)]

    def boundingRect(self):
        return QRectF(0, 0, 20, 40)

    def addToCircuit(self, circuit: Circuit):
        diode = Diode(**self.attributes)
        diode._patched_id = self.uid
        circuit.add(diode, (self.nodes[0].actual_node, self.nodes[1].actual_node))


class GraphicalMOSFET(CircuitSymbol):
    NAME = "MOSFET"
    ATTRIBUTES = {'thresholdVoltage': [float, "Threshold Voltage", "V", "Volts"],
                  'width': [float, "Width", "m", "Metres"],
                  'length': [float, "Length", "m", "Metres"],
                  'specificCapacitance': [float, "Specific Capacitance", "F/m^2", "Farads per metre squared"],
                  'electronMobility': [float, "Electron Mobility", "m^2/(Vs)", "Metres squared per volt-second"]}
    DEFAULT_ATTRIBUTES = {'thresholdVoltage': 3.0,
                          'width': 1e-6,
                          'length': 1e-9,
                          "specificCapacitance": 1e-2,
                          "electronMobility": 500e-4}

    def createNodes(self):
        # Gate, source, drain
        return [CircuitNode(0, 40), CircuitNode(30, 50), CircuitNode(30, 0)]

    def createDecor(self):
        triangle = QPolygonF([QPointF(20, 25), QPointF(27, 25 + 7 / (3 ** 0.5)), QPointF(27, 25 - 7 / (3 ** 0.5))])
        return [QGraphicsLineItem(0, 40, 15, 40),
                QGraphicsLineItem(15, 40, 15, 10),
                QGraphicsLineItem(20, 42, 20, 35 + 1 / 3),
                QGraphicsLineItem(20, 28 + 1 / 3, 20, 21 + 2 / 3),
                QGraphicsLineItem(20, 14 + 2 / 3, 20, 8),
                QGraphicsLineItem(30, 50, 30, 25),
                QGraphicsLineItem(30, 38 + 2 / 3, 20, 38 + 2 / 3),
                QGraphicsLineItem(30, 25, 27, 25),
                QGraphicsLineItem(30, 0, 30, 11 + 1 / 3),
                QGraphicsLineItem(30, 11 + 1 / 3, 20, 11 + 1 / 3),
                QGraphicsPolygonItem(triangle)]

    def boundingRect(self):
        return QRectF(0, 0, 30, 50)

    def addToCircuit(self, circuit: Circuit):
        mosfet = MOSFET(**self.attributes)
        mosfet._patched_id = self.uid
        circuit.add(mosfet, (self.nodes[0].actual_node, self.nodes[1].actual_node, self.nodes[2].actual_node))


class GraphicalSwitch(CircuitSymbol):
    NAME = "Switch"
    ATTRIBUTES = {}
    DEFAULT_ATTRIBUTES = {}

    def __init__(self, uid, x=0, y=0):
        super().__init__(uid, x, y)
        self.open = True

    def createNodes(self):
        return [CircuitNode(0, 10), CircuitNode(60, 10)]

    def createDecor(self):
        return [QGraphicsLineItem(0, 10, 12, 10), QGraphicsLineItem(60, 10, 48, 10),
                QGraphicsEllipseItem(12, 7, 6, 6), QGraphicsEllipseItem(42, 7, 6, 6),
                QGraphicsLineItem(18, 9, 42, 0)]

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.open:
                self.open = False
                self.decor[-1].setLine(18, 9, 45, 7)
            else:
                self.open = True
                self.decor[-1].setLine(18, 9, 42, 0)
            self.scene().parent().onSwitchStateChange(self.open, self.uid)
            event.accept()
        return super().mouseReleaseEvent(event)

    def boundingRect(self):
        return QRectF(0, 0, 60, 15)

    def addToCircuit(self, circuit: Circuit):
        switch = Switch(closed=not self.open)
        switch._patched_id = self.uid
        circuit.add(switch, (self.nodes[0].actual_node, self.nodes[1].actual_node))


class GraphicalGround(CircuitSymbol):
    NAME = "Ground"
    ATTRIBUTES = {}
    DEFAULT_ATTRIBUTES = {}

    def createNodes(self):
        return [CircuitNode(10, 0)]

    def createDecor(self):
        return [QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(-10, 20, 30, 20),
                QGraphicsLineItem(-3, 25, 23, 25),
                QGraphicsLineItem(4, 30, 16, 30)]

    def boundingRect(self):
        return QRectF(-10, 0, 40, 30)

    def addToCircuit(self, circuit: Circuit):
        pass


class GraphicalTestPoint(CircuitSymbol):
    NAME = "Test Point"
    ATTRIBUTES = {}
    DEFAULT_ATTRIBUTES = {}

    def createNodes(self):
        return [CircuitNode(0, 30)]

    def createDecor(self):
        return [QGraphicsLineItem(0, 30, 15, 15),
                QGraphicsLineItem(10, 10, 20, 20),
                QGraphicsLineItem(10, 10, 30, 0),
                QGraphicsLineItem(20, 20, 30, 0)]

    def boundingRect(self):
        return QRectF(0, 0, 30, 30)

    def addToCircuit(self, circuit: Circuit):
        pass


COMPONENTS = {"Resistor": GraphicalResistor,
              "Capacitor": GraphicalCapacitor,
              "Inductor": GraphicalInductor,
              "Ground": GraphicalGround,
              "Voltage Source": GraphicalVoltageSource,
              "AC Voltage Source": GraphicalACVoltageSource,
              "Diode": GraphicalDiode,
              "MOSFET": GraphicalMOSFET,
              "Switch": GraphicalSwitch,
              "Test Point": GraphicalTestPoint}
