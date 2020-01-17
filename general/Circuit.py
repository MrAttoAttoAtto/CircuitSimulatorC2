# Rough outline
from typing import Union, Tuple

import numpy as np
import scipy.linalg

from general.Environment import Environment
from utils.MutableFloat import MutableFloat


class Circuit:
    def __init__(self, environment: Environment, delta_t: float):
        self.matrix_n = 0
        self.node_mapping = {}
        self.delta_t = delta_t
        environment.delta_t = delta_t
        self.environment = environment

        self.componentNodes = []
        self.components = ()

        self.groundNode = None
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

        self.componentNodes.append((component, nodes))

    def finalise(self, groundNode: int):
        # We remove rows and columns of ground...
        ground_entry = self.node_mapping[groundNode]
        for node in self.node_mapping.keys():
            # Shift down once
            if self.node_mapping[node] > ground_entry:
                self.node_mapping[node] -= 1
        self.matrix_n -= 1
        self.jacobian = np.array([[MutableFloat() for _ in range(self.matrix_n)] for _ in range(self.matrix_n)])
        self.resultVector = np.array([MutableFloat() for _ in range(self.matrix_n)])
        self.inputVector = np.array([MutableFloat(1) for _ in range(self.matrix_n)])
        self.groundNode = groundNode
        for component in self.componentNodes:
            component[0].connect(self, component[1])

        self.components = [component[0] for component in self.componentNodes]

    def getInputReference(self, node: Union[Tuple[int], int]) -> MutableFloat:
        return self.inputVector[self.node_mapping[node]] if node != self.groundNode else MutableFloat()

    def getResultReference(self, node: Union[Tuple[int], int]) -> MutableFloat:
        return self.resultVector[self.node_mapping[node]] if node != self.groundNode else MutableFloat()

    def getJacobianReference(self, nodeA: Union[Tuple[int], int], nodeB: Union[Tuple[int], int]) -> MutableFloat:
        return self.jacobian[self.node_mapping[nodeA], self.node_mapping[nodeB]] if nodeA != self.groundNode and nodeB != self.groundNode else MutableFloat()

    def simulate_step(self):
        # TODO do better guessing!
        clear_vec_one = np.vectorize(lambda x: x.reset(1))
        clear_vec_one(self.inputVector)

        # Limit convergence
        for _ in range(100000):
            updateVec = np.vectorize(lambda x: x.update())
            updateVec(self.inputVector)

            clear_vec = np.vectorize(lambda x: x.reset(0))
            clear_vec(self.resultVector)
            clear_vec(self.jacobian)

            for component in self.components:
                component.stamp(self.environment)

            extract_value = np.vectorize(lambda x: x.live, otypes=[np.float64])
            jac = extract_value(self.jacobian)
            resultVector = -extract_value(self.resultVector)

            # Solve matrices
            delta_in = scipy.linalg.lapack.dgesv(jac+1e-12, resultVector)[2]
            for i, inputValue in enumerate(self.inputVector):
                inputValue += delta_in[i]

            # If the better guess is indistinguishable from the prior guess, we probably have the right value...
            if (abs(delta_in) < 1e-5).all():
                self.environment.time += self.delta_t
                return
