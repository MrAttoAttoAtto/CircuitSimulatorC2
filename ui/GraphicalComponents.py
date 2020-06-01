from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QPolygonF, QPainterPathStroker, QPainterPath, QFont, QColor, QBrush
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox, QGraphicsItem, \
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsPathItem, \
    QGraphicsSimpleTextItem
from pyqtgraph import mkColor

from components.ACVoltageSource import ACVoltageSource
from components.Capacitor import Capacitor
from components.Diode import Diode
from components.Inductor import Inductor
from components.MOSFET import MOSFET
from components.Resistor import Resistor
from components.SweepVoltageSource import SweepVoltageSource
from components.Switch import Switch
from components.VoltageControlledVoltageSource import VCVS
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from ui.utils import defaultPen
from ui.visuals import CircuitItem, CircuitNode, ColourSelectButton


class CircuitSymbol(CircuitItem):
    PREFIX = ""
    NAME = ""
    ATTRIBUTES = {"name": [str, "Component Name", "", ""]}
    DEFAULT_ATTRIBUTES = {"name": ""}

    def __init__(self, uid, x=0, y=0):
        super().__init__()
        self.uid = uid
        self.attributes = self.DEFAULT_ATTRIBUTES.copy()
        # An non-unique guaranteed, 'id' corresponding to the type of the component.
        self._temp_id = 0
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

    def populateName(self, componentNames: set):
        """Generates the name of the component if necessary, and adds it to the componentNames set."""
        if self.attributes["name"] == "":
            i = 1
            while f"{self.PREFIX}{i}" in componentNames:
                i += 1
            self._temp_id = i
            self.attributes["name"] = f"{self.PREFIX}{i}"
        if self.attributes["name"] in componentNames:
            raise ValueError("Component Name {} already exists.".format(self.attributes["name"]))
        else:
            componentNames.add(self.attributes["name"])

    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
        if len(self.attributes) == 0:
            return

        dialog = QDialog()
        dialog.setWindowTitle(f"{self.NAME} Configuration")

        gridLayout = QGridLayout()
        attributeMap = {}
        for i, (name, (typ, displayName, unit, unitTooltip)) in enumerate(self.ATTRIBUTES.items()):
            label = QLabel(f"{displayName}:")
            if typ is QColor:
                entry = ColourSelectButton(self.attributes[name], None)
            else:
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
                self.onAttributesUpdated()
                self.scene().parent().setEdited()
            dialog.close()

        buttonBox.accepted.connect(recordValues)
        buttonBox.rejected.connect(dialog.close)

        gridLayout.addWidget(buttonBox, i + 1, 1)
        dialog.setLayout(gridLayout)

        dialog.exec()

    def onAttributesUpdated(self):
        pass

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


def QColorFactory(rgbString: str) -> QColor:
    return QColor(int(rgbString))


def CircuitComponent(cls):
    cls.ATTRIBUTES.update(cls.__mro__[1].ATTRIBUTES)
    cls.DEFAULT_ATTRIBUTES.update(cls.__mro__[1].DEFAULT_ATTRIBUTES)
    return cls


@CircuitComponent
class CircuitWire(CircuitSymbol):
    PREFIX = "W"
    NAME = "Wire"
    ATTRIBUTES = {}
    DEFAULT_ATTRIBUTES = {}

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


@CircuitComponent
class GraphicalResistor(CircuitSymbol):
    PREFIX = "R"
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
        res = Resistor(resistance=self.attributes["resistance"])
        res._patched_id = self.uid
        circuit.add(res, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalCapacitor(CircuitSymbol):
    PREFIX = "C"
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
        cap = Capacitor(capacitance=self.attributes["capacitance"])
        cap._patched_id = self.uid
        circuit.add(cap, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalInductor(CircuitSymbol):
    PREFIX = "L"
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
        ind = Inductor(inductance=self.attributes["inductance"])
        ind._patched_id = self.uid
        circuit.add(ind, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalVoltageSource(CircuitSymbol):
    PREFIX = "VS"
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
        pwr = VoltageSource(self.attributes["voltage"])
        pwr._patched_id = self.uid
        circuit.add(pwr, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalACVoltageSource(CircuitSymbol):
    PREFIX = "VS"
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
        pwr = ACVoltageSource(self.attributes["peakVoltage"], self.attributes["frequency"])
        pwr._patched_id = self.uid
        circuit.add(pwr, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalSweepVoltageSource(CircuitSymbol):
    PREFIX = "VS"
    NAME = "Sweeping Voltage Source"
    # Type then display name then unit then unit tooltip
    ATTRIBUTES = {'startVoltage': [float, "Starting Voltage", "V", "Volts"],
                  'rate': [float, "Rate of increase", "V/s", "Volts per second"]}
    DEFAULT_ATTRIBUTES = {'startVoltage': 0.0, 'rate': 1.0}

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 70)]

    def createDecor(self):
        arrowhead = QPolygonF([QPointF(17.5, 27.5), QPointF(17.5, 32.5), QPointF(12.5, 27.5)])
        return [QGraphicsEllipseItem(-5, 20, 30, 30),
                QGraphicsLineItem(2.5, 42.5, 17.5, 27.5),
                QGraphicsPolygonItem(arrowhead),
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 50, 10, 70)]

    def boundingRect(self):
        return QRectF(-5, 0, 35, 70)

    def addToCircuit(self, circuit: Circuit):
        pwr = SweepVoltageSource(self.attributes["startVoltage"], self.attributes["rate"])
        pwr._patched_id = self.uid
        circuit.add(pwr, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalDiode(CircuitSymbol):
    PREFIX = "D"
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
        diode = Diode(self.attributes["breakdownVoltage"], self.attributes["saturationCurrent"],
                      self.attributes["ideality"])
        diode._patched_id = self.uid
        circuit.add(diode, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalGround(CircuitSymbol):
    PREFIX = "G"
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
        return QRectF(-10, 0, 30, 30)

    def addToCircuit(self, circuit: Circuit):
        pass


@CircuitComponent
class GraphicalTestPoint(CircuitSymbol):
    PREFIX = "V"
    NAME = "Test Point"
    ATTRIBUTES = {"colour": [QColorFactory, "Colour", "", ""]}
    DEFAULT_ATTRIBUTES = {"colour": Qt.black}

    def populateName(self, componentNames: set):
        super().populateName(componentNames)
        self.attributes["colour"] = mkColor((self._temp_id % 16, 16))
        self.onAttributesUpdated()

    def onAttributesUpdated(self):
        self.decor[1].setBrush(QBrush(self.attributes["colour"]))

    def createNodes(self):
        return [CircuitNode(0, 30)]

    def createDecor(self):
        polygon = QPolygonF([QPointF(10, 10), QPointF(20, 20), QPointF(30, 0), QPointF(10, 10)])

        return [QGraphicsLineItem(0, 30, 15, 15),
                QGraphicsPolygonItem(polygon)]

    def boundingRect(self):
        return QRectF(0, 0, 30, 30)

    def addToCircuit(self, circuit: Circuit):
        pass


@CircuitComponent
class GraphicalSwitch(CircuitSymbol):
    PREFIX = "S"
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


@CircuitComponent
class GraphicalMOSFET(CircuitSymbol):
    PREFIX = "Q"
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
        mosfet = MOSFET(self.attributes["thresholdVoltage"], self.attributes["width"], self.attributes["length"],
                        self.attributes["specificCapacitance"], self.attributes["electronMobility"])
        mosfet._patched_id = self.uid
        circuit.add(mosfet, (self.nodes[0].actual_node, self.nodes[1].actual_node, self.nodes[2].actual_node))


@CircuitComponent
class GraphicalVCVS(CircuitSymbol):
    PREFIX = "VCVS"
    NAME = "VCVS"
    ATTRIBUTES = {'mu': [float, "Gain", " ", "Dimensionless"]}
    DEFAULT_ATTRIBUTES = {'mu': 1.0}

    def createNodes(self):
        # anode, cathode, control anode, control cathode
        return [CircuitNode(10, 0), CircuitNode(10, 60), CircuitNode(-20, 10), CircuitNode(-20, 50)]

    def createDecor(self):
        diamond = QPolygonF([QPointF(10, 20), QPointF(20, 30), QPointF(10, 40), QPointF(0, 30)])
        return [QGraphicsLineItem(-20, 10, -10, 10),
                QGraphicsLineItem(-20, 50, -10, 50),
                QGraphicsEllipseItem(-10, 8.5, 3, 3),
                QGraphicsEllipseItem(-10, 48.5, 3, 3),
                QGraphicsLineItem(-11, 14, -11, 19),
                QGraphicsLineItem(-13.5, 16.5, -8.5, 16.5),
                QGraphicsLineItem(-13.5, 43.5, -8.5, 43.5),
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 60, 10, 40),
                QGraphicsPolygonItem(diamond),
                QGraphicsLineItem(10, 23, 10, 28),
                QGraphicsLineItem(7.5, 25.5, 12.5, 25.5),
                QGraphicsLineItem(7.5, 34.5, 12.5, 34.5)]

    def boundingRect(self):
        return QRectF(-20, 0, 40, 60)

    def addToCircuit(self, circuit: Circuit):
        vcvs = VCVS(self.attributes["mu"])
        vcvs._patched_id = self.uid
        circuit.add(vcvs, (
            self.nodes[0].actual_node, self.nodes[1].actual_node, self.nodes[2].actual_node, self.nodes[3].actual_node))


@CircuitComponent
class GraphicalAmmeter(CircuitSymbol):
    PREFIX = "I"
    NAME = "Ammeter"
    ATTRIBUTES = {"colour": [QColorFactory, "Colour", "", ""]}
    DEFAULT_ATTRIBUTES = {"colour": Qt.black}

    def populateName(self, componentNames: set):
        super().populateName(componentNames)
        self.attributes["colour"] = mkColor((self._temp_id % 16, 16))
        self.onAttributesUpdated()

    def onAttributesUpdated(self):
        self.decor[0].setBrush(QBrush(self.attributes["colour"]))

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 70)]

    def createDecor(self):
        font = QFont("Helvetica", 8, QFont.Thin)
        text = QGraphicsSimpleTextItem("A")
        text.setFont(font)
        text.setPos(10 - text.boundingRect().width() / 2, 34.5 - text.boundingRect().height() / 2)

        return [QGraphicsEllipseItem(-5, 20, 30, 30),
                text,
                QGraphicsLineItem(10, 50, 10, 70),
                QGraphicsLineItem(10, 0, 10, 20)]

    def boundingRect(self):
        return QRectF(-5, 0, 30, 70)

    def addToCircuit(self, circuit: Circuit):
        meter = VoltageSource(0)
        meter._patched_id = self.uid
        circuit.add(meter, (self.nodes[0].actual_node, self.nodes[1].actual_node))


@CircuitComponent
class GraphicalVoltmeter(CircuitSymbol):
    PREFIX = "V"
    NAME = "Voltmeter"
    ATTRIBUTES = {"colour": [QColorFactory, "Colour", "", ""]}
    DEFAULT_ATTRIBUTES = {"colour": Qt.black}

    def populateName(self, componentNames: set):
        super().populateName(componentNames)
        self.attributes["colour"] = mkColor((self._temp_id % 16, 16))
        self.onAttributesUpdated()

    def onAttributesUpdated(self):
        self.decor[0].setBrush(QBrush(self.attributes["colour"]))

    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 70)]

    def createDecor(self):
        font = QFont("Helvetica", 8, QFont.Thin)
        text = QGraphicsSimpleTextItem("V")
        text.setFont(font)
        text.setPos(10 - text.boundingRect().width() / 2, 34.5 - text.boundingRect().height() / 2)

        return [QGraphicsEllipseItem(-5, 20, 30, 30),
                text,
                QGraphicsLineItem(10, 50, 10, 70),
                QGraphicsLineItem(10, 0, 10, 20)]

    def boundingRect(self):
        return QRectF(0, 0, 20, 70)

    def addToCircuit(self, circuit: Circuit):
        pass


COMPONENTS = {"Resistor": GraphicalResistor,
              "Capacitor": GraphicalCapacitor,
              "Inductor": GraphicalInductor,
              "Ground": GraphicalGround,
              "Voltage Source": GraphicalVoltageSource,
              "AC Voltage Source": GraphicalACVoltageSource,
              "Sweeping Voltage Source": GraphicalSweepVoltageSource,
              "Diode": GraphicalDiode,
              "MOSFET": GraphicalMOSFET,
              "VCVS": GraphicalVCVS,
              "Switch": GraphicalSwitch,
              "Test Point": GraphicalTestPoint,
              "Ammeter": GraphicalAmmeter,
              "Voltmeter": GraphicalVoltmeter}
