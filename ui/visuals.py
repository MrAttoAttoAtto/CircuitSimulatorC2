# -*- coding: utf-8 -*-
"""
Created on Tue Dec 17 14:30:00 2019

@author: Joseph, and ya boi
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen
from PyQt5.QtWidgets import (QGraphicsView,
                             QGraphicsItem, QGraphicsRectItem)

from ui.utils import defaultPen, selectedPen, snap_point


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
        self.updateHoverState(self.isUnderMouse())
        target.updateHoverState(self.isUnderMouse())

    def disconnect(self, target):
        self.connected.remove(target)
        target.connected.remove(self)
        self.updateHoverState(self.isUnderMouse())
        target.updateHoverState(self.isUnderMouse())

    def disconnect_all(self):
        for n in self.connected.copy():
            self.disconnect(n)

    def updateHoverState(self, hovered:bool):
        p = QPen(defaultPen)
        if hovered:
            # Red
            p.setColor(QColor(255, 0, 0))
        elif self.connected:
            p.setColor(QColor(0, 0, 0, 0))
        else:
            p.setColor(QColor(0, 255, 0))
        self.setPen(p)

    def hoverEnterEvent(self, event):
        self.updateHoverState(True)

    def hoverLeaveEvent(self, event):
        self.updateHoverState(False)

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
        self.setFlag(QGraphicsItem.ItemIsFocusable, True)

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

