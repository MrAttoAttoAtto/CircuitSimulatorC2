# Rough outline
from typing import Union, Tuple

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
                self.node_mapping[n] = self.matrix_n
                self.matrix_n += 1

        if component.isVoltageBased and self.node_mapping.get((nodes[0], nodes[1])) is None:
            assert len(nodes) == 2
            self.node_mapping[(nodes[0], nodes[1])] = self.matrix_n
            self.matrix_n += 1

        self.components.append((component, nodes))

    def finalise(self, groundNode: int):
        self.jacobian = np.array([[MutableFloat() for _ in range(self.matrix_n)] for _ in range(self.matrix_n)])
        self.resultVector = np.array([MutableFloat() for _ in range(self.matrix_n)])
        self.inputVector = np.array([MutableFloat() for _ in range(self.matrix_n)])

        for component in self.components:
            component[0].connect(self, component[1])

    def getInputReference(self, node: Union[Tuple[int], int]) -> MutableFloat:
        return self.inputVector[self.node_mapping[node]]

    def getResultReference(self, node: Union[Tuple[int], int]) -> MutableFloat:
        return self.resultVector[self.node_mapping[node]]

    def getJacobianReference(self, nodeA: Union[Tuple[int], int], nodeB: Union[Tuple[int], int]) -> MutableFloat:
        return self.jacobian[self.node_mapping[nodeA], self.node_mapping[nodeB]]

    def simulate_step(self):
        pass
