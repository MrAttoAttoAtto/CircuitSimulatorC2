import multiprocessing
import queue
from enum import Enum

from PyQt5.QtCore import QTimer, pyqtSignal, QObject

from general.Circuit import Circuit
from general.Simulation import TransientSimulation


class WorkerMessage(Enum):
    CHANGE_WATCHED = 1
    SWITCH_STATE_CHANGE = 2


def _transient_simulate(circuit: Circuit, watchedNodes: [int], outQueue: multiprocessing.Queue,
                        inQueue: multiprocessing.Queue, resultInterval: float):
    sim = TransientSimulation(circuit, 10000, 1e-5)
    watchedRefs = {n: circuit.getInputReference(n) for n in watchedNodes}
    resultIntervalCount = resultInterval // 1e-5
    i = 0
    while True:
        if i == resultIntervalCount:
            # Check messages from main
            try:
                w = inQueue.get(False)
                if w is None:
                    # Trigger to stop
                    break
                else:
                    if w[0] == WorkerMessage.CHANGE_WATCHED:
                        watchedNodes = w[1]
                        watchedRefs = {n: circuit.getInputReference(n) for n in w}
                    elif w[0] == WorkerMessage.SWITCH_STATE_CHANGE:
                        for c in circuit.components:
                            if c._patched_id == w[1]:
                                c.closed = not w[2]
                                break
                    else:
                        raise Exception("Invalid Message")
            except queue.Empty:
                pass
            # Send updated values
            outQueue.put((circuit.environment.time, {n: ref.value for (n, ref) in watchedRefs.items()}))
            i = 0
        i += 1

        # Simulate a step
        sim.step()


class TransientWorker(QObject):
    onStep = pyqtSignal(object)

    def __init__(self, circuit: Circuit, watchedNodes: [int]):
        super().__init__()
        self.watchedNodes = watchedNodes
        self.resultsQueue = multiprocessing.Queue()
        self.commandQueue = multiprocessing.Queue()

        self.checkTimer = QTimer()
        self.checkTimer.timeout.connect(self._periodicCheck)

        self._process = multiprocessing.Process(target=_transient_simulate,
                                                args=(
                                                    circuit, watchedNodes, self.resultsQueue, self.commandQueue,
                                                    10 / 1000))

    def start(self):
        self._process.start()
        self.checkTimer.start(20)

    def setWatchedNodes(self, watchedNodes: [int]):
        self.commandQueue.put((WorkerMessage.CHANGE_WATCHED, watchedNodes))

    def notifySwitchStateChanged(self, isOpen: bool, uid: int):
        self.commandQueue.put((WorkerMessage.SWITCH_STATE_CHANGE, uid, isOpen))

    def halt(self):
        self.checkTimer.stop()
        self.commandQueue.put(None)
        self._process.join()

    def getResults(self):
        res = []
        while not self.resultsQueue.empty():
            res.append(self.resultsQueue.get())
        return res

    def _periodicCheck(self):
        while True:
            try:
                self.onStep.emit(self.resultsQueue.get(False))
                print("Emitted onStep")
            except queue.Empty:
                break
