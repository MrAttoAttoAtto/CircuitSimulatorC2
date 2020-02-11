from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPen, QPolygonF, QPainterPathStroker
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox, QGraphicsItem, \
    QGraphicsRectItem, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsPolygonItem

from components.Diode import Diode
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from ui.utils import defaultPen
from ui.visuals import CircuitItem, CircuitNode


class CircuitSymbol(CircuitItem):
    NAME = ""
    ATTRIBUTES = {}
    DEFAULT_ATTRIBUTES = {}

    def __init__(self, x=0, y=0):
        super().__init__()
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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            # Delete the component
            for n in self.nodes:
                n.disconnect_all()
            self.scene().removeItem(self)
            event.accept()
        else:
            event.ignore()

    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
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

            self.attributes = middlemanMap
            dialog.close()

        buttonBox.accepted.connect(recordValues)
        buttonBox.rejected.connect(dialog.close)

        gridLayout.addWidget(buttonBox, i + 1, 1)
        dialog.setLayout(gridLayout)

        dialog.exec()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
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
    def createNodes(self):
        return [CircuitNode(),
                CircuitNode(self.path.path().currentPosition().x(), self.path.path().currentPosition().y())]

    def createDecor(self):
        return [self.path]

    def __init__(self, m_path):
        self.path = m_path
        old_pos = m_path.pos()
        m_path.setPos(0, 0)
        super().__init__(old_pos.x(), old_pos.y())

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
        return [CircuitNode(10, 0), CircuitNode(10, 100)]

    def createDecor(self):
        return [QGraphicsRectItem(0, 20, 20, 60),
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 80, 10, 100)]

    def boundingRect(self):
        return QRectF(0, 0, 20, 100)

    def addToCircuit(self, circuit: Circuit):
        res = Resistor(**self.attributes)
        circuit.add(res, (self.nodes[0].actual_node, self.nodes[1].actual_node))


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
        return QRectF(0, 0, 20, 70)

    def addToCircuit(self, circuit: Circuit):
        pwr = VoltageSource(**self.attributes)
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
        return [CircuitNode(10, 0), CircuitNode(10, 40)]

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
        circuit.add(diode, (self.nodes[0].actual_node, self.nodes[1].actual_node))


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
        return QRectF(-10, 0, 30, 30)

    def addToCircuit(self, circuit: Circuit):
        pass


COMPONENTS = [GraphicalResistor, GraphicalGround, GraphicalVoltageSource, GraphicalDiode]
