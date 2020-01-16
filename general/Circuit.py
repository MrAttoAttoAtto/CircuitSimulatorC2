# Rough outline
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

        self.component_nodes = []
        self.components = ()

        self.ground_node = None
        self.jacobian = None
        self.resultVector = None
        self.inputVector = None

    def add(self, component, nodes):
        # Nice to know how many nodes there are
        for n in nodes:
            if n not in self.node_mapping.keys():
                self.node_mapping[n] = [self.matrix_n, None]
                self.matrix_n += 1
            if component.isVoltageSource and self.node_mapping[n][1] is None:
                self.node_mapping[n][1] = self.matrix_n
                self.matrix_n += 1

        self.component_nodes.append((component, nodes))

    def finalise(self, ground_node: int):
        self.jacobian = np.array([[MutableFloat() for _ in range(self.matrix_n)] for _ in range(self.matrix_n)])
        self.resultVector = np.array([MutableFloat() for _ in range(self.matrix_n)])
        self.inputVector = np.array([MutableFloat() for _ in range(self.matrix_n)])
        self.ground_node = ground_node
        for component in self.component_nodes:
            component[0].connect(self, component[1])
        self.components = (component[0] for component in self.component_nodes)

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
        clear_vec = np.vectorize(lambda x: x.reset(0))
        clear_vec(self.resultVector)
        clear_vec(self.jacobian)
        for component in self.components:
            component.stamp(self.environment)

        extract_value = np.vectorize(lambda x: x.value)
        jac = extract_value(self.jacobian)
        resultVector = extract_value(self.resultVector)

        # Solve matrices
        delta_in = scipy.linalg.lapack.dgesv(jac, resultVector)[2]
        self.inputVector -= delta_in

        # If the better guess is indistinguishable from the prior guess, we probably have the right value...
        if (abs(delta_in) < 1e-5).all():
            self.environment.time += self.delta_t
