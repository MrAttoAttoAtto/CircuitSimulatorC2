# Rough outline
from typing import Union, Tuple, Callable

import numpy as np
import scipy.linalg

from general.Environment import Environment
from utils.MutableFloat import MutableFloat


class ConvergenceFailure(Exception):
    pass


class Circuit:
    def __init__(self, environment: Environment):
        self.matrix_n = 0
        self.node_mapping = {}
        self.environment = environment

        self.componentNodes = []
        self.components = ()

        self.groundNode = None
        self.jacobian = None
        self.resultVector = None
        self.inputVector = None

    def add(self, component, nodes):
        """
        Adds a component instance to the circuit, connected to the appropriate nodes.

        :param component: An instance of Component to add.
        :param nodes: A iterable of nodes which the component is connected to.
        :return: None
        """
        for n in nodes:
            if n not in self.node_mapping.keys():
                self.node_mapping[n] = self.matrix_n
                self.matrix_n += 1

        # Matrix_n will never be the same for 2 distinct components, so it works as an arbitrary unique identifier
        for n in component.getRequiredCrossNodes(nodes, self.matrix_n):
            if n not in self.node_mapping.keys():
                self.node_mapping[n] = self.matrix_n
                self.matrix_n += 1

        self.componentNodes.append((component, nodes))

    def finalise(self, groundNode: int):
        """
        Constructs the circuit using components that have been added.

        :param groundNode: The node that is treated as the reference; all voltages are relative to this node.
        :return: None
        """
        # We remove rows and columns of ground...
        ground_entry = self.node_mapping[groundNode]
        for node in self.node_mapping.keys():
            # Shift down once
            if self.node_mapping[node] > ground_entry:
                self.node_mapping[node] -= 1
        self.matrix_n -= 1
        self.jacobian = np.array([[MutableFloat() for _ in range(self.matrix_n)] for _ in range(self.matrix_n)])
        self.resultVector = [MutableFloat() for _ in range(self.matrix_n)]
        self.inputVector = [MutableFloat(0) for _ in range(self.matrix_n)]
        self.groundNode = groundNode
        for component in self.componentNodes:
            component[0].connect(self, component[1])

        self.components = [component[0] for component in self.componentNodes]

    def getInputReference(self, node: Union[Tuple[int, int, int], int]) -> MutableFloat:
        return self.inputVector[self.node_mapping[node]] if node != self.groundNode else MutableFloat()

    def getResultReference(self, node: Union[Tuple[int, int, int], int]) -> MutableFloat:
        return self.resultVector[self.node_mapping[node]] if node != self.groundNode else MutableFloat()

    def getJacobianReference(self, nodeA: Union[Tuple[int, int, int], int],
                             nodeB: Union[Tuple[int, int, int], int]) -> MutableFloat:
        return self.jacobian[self.node_mapping[nodeA], self.node_mapping[nodeB]] \
            if nodeA != self.groundNode and nodeB != self.groundNode else MutableFloat()


    def solve(self, convergence_limit: int, stamp_f: Callable[['Component', Environment], None]):
        # TODO do better guessing!
        extract_value = np.vectorize(lambda x: x.value, otypes=[np.float64])

        # Set starting inputs to 1
        for x in self.inputVector:
            x.reset(x.value)

        # Limit convergence
        for _ in range(convergence_limit):

            # Clear result vector
            for x in self.resultVector:
                x.reset(0.0)

            # Clear jacobian (old not necessary?)
            for x in np.nditer(self.jacobian, flags=['refs_ok']):
                x.item().reset_without_old(0.0)

            # Stamp each component's contributions
            for component in self.components:
                stamp_f(component, self.environment)

            jac = extract_value(self.jacobian)
            resultVector = [-x.value for x in self.resultVector]

            # Solve matrices
            delta_in = scipy.linalg.lapack.dgesv(jac+1e-12, resultVector)[2]
            for i, inputValue in enumerate(self.inputVector):
                inputValue += delta_in[i]

            # If the better guess is indistinguishable from the prior guess, we probably have the right value...
            if (abs(delta_in) < 1e-5).all():
                return
        else:
            raise ConvergenceFailure("Failed to converge.")
