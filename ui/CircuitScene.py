from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtWidgets import QGraphicsScene

from ui.GraphicalComponents import CircuitWire
from ui.UberPath import UberPath
from ui.utils import snap_point, defaultPen


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
