from PyQt5.QtGui import QPainterPath, QPainterPathStroker
from PyQt5.QtWidgets import QGraphicsPathItem


class UberPath(QGraphicsPathItem):
    def __init__(self):
        super().__init__()
        self._points = []
        self.sourcePos = None
        self.targetPos = None

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