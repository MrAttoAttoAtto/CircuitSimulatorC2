# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 14:30:00 2019

@author: Joseph
"""
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QColor, QPen, QPainterPath, QPainterPathStroker
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView,
                             QGraphicsLineItem, QGraphicsItem, QGraphicsScene,
                             QGraphicsRectItem, QGraphicsPathItem)

defaultPen = QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
selectedPen = QPen(Qt.blue, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)


def round_nearest(n, base):
    return base * round(n / base)


def snap_point(p, base):
    return QPointF(round_nearest(p.x(), base), round_nearest(p.y(), base))


class CircuitNode(QGraphicsRectItem):
    def __init__(self, x=0, y=0):
        super().__init__(-5, -5, 10, 10)
        self.setPen(QColor(0, 255, 0))
        self.setAcceptHoverEvents(True)
        self.setPos(x, y)
        self._wire_spawn = None
        self.actual_node = -1
        self.connected = set()

    def connect(self, target):
        self.connected.add(target)
        target.connected.add(self)
        p = QPen(defaultPen)
        p.setColor(QColor(0, 255, 0, 0))
        self.setPen(p)
        target.setPen(p)

    def disconnect(self, target):
        self.connected.remove(target)
        target.connected.remove(self)

    def disconnect_all(self):
        for n in self.connected.copy():
            self.disconnect(n)


    def hoverEnterEvent(self, event):
        p = QPen(defaultPen)
        p.setColor(QColor(255, 0, 0))
        self.setPen(p)

    def hoverLeaveEvent(self, event):
        p = QPen(defaultPen)
        p.setColor(QColor(0, 255, 0, 0 if len(self.connected) else 255))
        self.setPen(p)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        event.accept()
        self.scene().wireCreationEvent(self)


class CircuitItem(QGraphicsItem):

    def __init__(self):
        super().__init__()
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if (change == QGraphicsItem.ItemSelectedChange):
            if value == True:
                pen = selectedPen
            else:
                pen = defaultPen
            for c in self.decor:
                c.setPen(pen)
        elif change == QGraphicsItem.ItemPositionChange and self.scene() is not None:
            grid_size = self.scene().grid_resolution
            return snap_point(value, grid_size)
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        pass


class CircuitSymbol(CircuitItem):

    def __init__(self, x=0, y=0, logical=None):
        super().__init__()
        self.logical = logical
        self.nodes = self.createNodes()
        self.decor = self.createDecor()

        for c in self.nodes:
            c.setParentItem(self)
        for c in self.decor:
            c.setParentItem(self)
            pen = QPen(defaultPen)
            pen.setColor(Qt.red)
            c.setPen(pen)

        self.setPos(x, y)
        self.setAcceptHoverEvents(True)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            for n in self.nodes:
                n.disconnect_all()
        return super().itemChange(change, value)

    def createNodes(self):
        raise NotImplementedError()

    def createDecor(self):
        raise NotImplementedError()


class GraphicalResistor(CircuitSymbol):
    def createNodes(self):
        return [CircuitNode(10, 0), CircuitNode(10, 100)]

    def createDecor(self):
        return [QGraphicsRectItem(0, 20, 20, 60),
                QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(10, 80, 10, 100)]

    def boundingRect(self):
        return QRectF(0, 0, 20, 100)


class GraphicalGround(CircuitSymbol):
    def createNodes(self):
        return [CircuitNode(10, 0)]
    def createDecor(self):
        return [QGraphicsLineItem(10, 0, 10, 20),
                QGraphicsLineItem(-10, 20, 30, 20),
                QGraphicsLineItem(-3, 25, 23, 25),
                QGraphicsLineItem(4, 30, 16, 30)]
    def boundingRect(self):
        return QRectF(-10, 0, 30, 30)

class UberPath(QGraphicsPathItem):
    def __init__(self):
        super().__init__()
        self._points = []

    def addPoint(self, point):
        self._points.append(point)
        self.regenPath()

    def editPoint(self, index, new_point):
        self._points[index] = new_point
        self.regenPath()

    def regenPath(self):
        n_path = QPainterPath()
        prev_y = 0
        for p in self._points:
            n_path.lineTo(p.x(), prev_y)
            prev_y = p.y()
            n_path.lineTo(p.x(), p.y())
        x = QPainterPathStroker()
        self.setPath(n_path)

    def shape(self):
        x = QPainterPathStroker()
        return x.createStroke(self.path())

    @property
    def startPoint(self):
        return self.scenePos()

    @property
    def endPoint(self):
        return self.path().currentPosition() + self.startPoint

    @property
    def pointCount(self):
        return len(self._points)


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


class CircuitView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self._panX = 0
        self._panY = 0
        self._panning = False

    def zoomToFit(self):
        self.fitInView(self.scene().sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        if (event.angleDelta().y() > 0):
            self.scale(1.25, 1.25)
        else:
            self.scale(0.8, 0.8)

    def mousePressEvent(self, event):
        if (event.button() == Qt.MiddleButton):
            self._panX, self._panY = event.x(), event.y()
            self._panning = True
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        elif event.button() == Qt.RightButton:
            self.zoomToFit()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._panning:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - (event.x() - self._panX))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - (event.y() - self._panY))
            self._panX, self._panY = event.x(), event.y()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.setCursor(Qt.ArrowCursor)
            self._panning = False
            event.accept()
            return
        super().mouseReleaseEvent(event)


class CircuitScene(QGraphicsScene):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wire_spawn = None
        self._wire_spawn_source = None
        self.grid_resolution = 10

    def wireCreationEvent(self, source):
        if self._wire_spawn is None:
            self.startWireCreation(source)
        else:
            self.endWireCreation(source)

    def mouseMoveEvent(self, event):
        if self._wire_spawn is not None:
            p = snap_point(event.scenePos() - self._wire_spawn_source.scenePos(), self.grid_resolution)
            self._wire_spawn.editPoint(-1, p)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not event.isAccepted() and event.button() == Qt.LeftButton and self._wire_spawn is not None:
            print("Extend wire")
            self._wire_spawn.addPoint(
                snap_point(event.scenePos() - self._wire_spawn_source.scenePos(), self.grid_resolution))
        if not event.isAccepted() and event.button() == Qt.RightButton and self._wire_spawn is not None:
            print("Cancel Wire")
            self.removeItem(self._wire_spawn)
            self._wire_spawn = None
            self._wire_spawn_source = None

    def startWireCreation(self, source):
        self._wire_spawn = UberPath()
        self.addItem(self._wire_spawn)
        self._wire_spawn.setPen(defaultPen)
        self._wire_spawn.setPos(source.scenePos())
        self._wire_spawn.addPoint(QPointF(0, 0))
        self._wire_spawn_source = source

    def endWireCreation(self, target):
        if target != self._wire_spawn_source:
            self._wire_spawn.editPoint(-1, target.scenePos() - self._wire_spawn_source.scenePos())
            self.removeItem(self._wire_spawn)
            new_wire = CircuitWire(self._wire_spawn)
            self.addItem(new_wire)
            new_wire.nodes[0].connect(self._wire_spawn_source)
            new_wire.nodes[1].connect(target)
            self._wire_spawn = None
            self._wire_spawn_source = None

    def addComponent(self, x, y, logical):
        visual_component = logical.DISPLAY(x, y, logical)
        self.addItem(visual_component)
        logical.graphic = visual_component

