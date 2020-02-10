from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen


def round_nearest(n, base):
    return base * round(n / base)


def snap_point(p, base):
    return QPointF(round_nearest(p.x(), base), round_nearest(p.y(), base))


defaultPen = QPen(Qt.black, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
selectedPen = QPen(Qt.blue, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
