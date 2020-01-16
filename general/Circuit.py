# Rough outline
import numpy as np

from general.Environment import Environment
from utils.MutableFloat import MutableFloat


class Circuit:
    def __init__(self, environment: Environment, delta_t: float):
        self.components = []
        self.matrix_n = 0
        self.node_mapping = {}
        self.delta_t = delta_t
        self.environment = environment

        self.jacobian = None
        self.resultVector = None
        self.inputVector = None

    def add(self, component, nodes):
        for n in nodes:
            if n not in self.node_mapping.keys():
                self.node_mapping[n] = [self.matrix_n, None]
                self.matrix_n += 1
            if component.isVoltageSource and self.node_mapping[n][1] is None:
                self.node_mapping[n][1] = self.matrix_n
                self.matrix_n += 1

        self.components.append((component, nodes))

    def finalise(self, groundNode: int):
        self.jacobian = np.array([[MutableFloat() for _ in range(self.matrix_n)] for _ in range(self.matrix_n)])
        self.resultVector = np.array([MutableFloat() for _ in range(self.matrix_n)])
        self.inputVector = np.array([MutableFloat() for _ in range(self.matrix_n)])

        for component in self.components:
            component[0].connect(self, component[1])

    def getInputVoltageReference(self, node: int) -> MutableFloat:
        return self.inputVector[self.node_mapping[node][0]]

    def getInputCurrentReference(self, node: int) -> MutableFloat:
        return self.inputVector[self.node_mapping[node][1]]

    def getResultCurrentReference(self, node: int) -> MutableFloat:
        return self.resultVector[self.node_mapping[node][0]]

    def getResultVoltageReference(self, node: int) -> MutableFloat:
        return self.resultVector[self.node_mapping[node][1]]

    def getJacobianVoltageReference(self, nodeA: int, nodeB: int) -> MutableFloat:
        return self.jacobian[self.node_mapping[nodeA][0], self.node_mapping[nodeB][0]]

    def getJacobianCurrentReference(self, node: int, inverse: bool) -> MutableFloat:
        return self.jacobian[self.node_mapping[node][1 if inverse else 0], self.node_mapping[node][0 if inverse else 1]]

    def simulate_step(self):
        pass
