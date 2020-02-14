from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class Switch:
    """
    A standard, on-off switch.
    Could be either momentary or otherwise by just varying when you close and open it.
    """

    isVoltageBased = False

    def __init__(self, closed: bool = True, openG: float = 1e-12, closedG: float = 1e12):
        """
        Creates a switch, setting all the nodes to None before the switch is connected

        :param closed: Does it start open or closed?
        """

        # Basic switch properties
        self.closed = closed
        self.openG = openG
        self.closedG = closedG

        # The objects that will hold the voltage at the front and back nodes of the switch
        # These are the values corresponding to the front and back nodes in the INPUT VECTOR
        self.frontVoltage = None
        self.backVoltage = None

        # The objects that will hold the current at the front and back nodes of the switch
        # These are the values corresponding to the front and back nodes in the RESULT VECTOR
        self.frontCurrent = None
        self.backCurrent = None

        # The objects that will hold the conductances at the front and back nodes in the switch: in essence
        # the derivatives of the currents with respect to the front and back voltages
        # These are the values corresponding to the front and back nodes in the JACOBIAN MATRIX
        self.frontConductanceByFrontVoltage = None
        self.frontConductanceByBackVoltage = None
        self.backConductanceByFrontVoltage = None
        self.backConductanceByBackVoltage = None

    # noinspection PyMethodMayBeStatic
    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns an empty list as cross-node entries are not required for a switch

        :param nodes: The nodes this switch is connected to
        :param identifier: This switch's identifier
        :return: An empty list
        """

        return []

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the switch to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (2) nodes this switch is connected to
        :return: None
        """

        frontNode, backNode = nodes

        self.frontVoltage = circuit.getInputReference(frontNode)
        self.backVoltage = circuit.getInputReference(backNode)

        self.frontCurrent = circuit.getResultReference(frontNode)
        self.backCurrent = circuit.getResultReference(backNode)

        # Coordinate-type system with the jacobian: handled by the Circuit class
        self.frontConductanceByFrontVoltage = circuit.getJacobianReference(frontNode, frontNode)
        self.frontConductanceByBackVoltage = circuit.getJacobianReference(frontNode, backNode)
        self.backConductanceByFrontVoltage = circuit.getJacobianReference(backNode, frontNode)
        self.backConductanceByBackVoltage = circuit.getJacobianReference(backNode, backNode)

    def stamp_static(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the switch would, after infinite time.

        :param environment: The environment of the circuit when this switch is operating
        :return: None
        """

        # +ve means current is flowing _out_ of that node into this component
        conductance = self.closedG if self.closed else self.openG
        current = (self.frontVoltage.value - self.backVoltage.value) * conductance
        self.frontCurrent += current
        self.backCurrent -= current

        self.frontConductanceByFrontVoltage += conductance
        self.frontConductanceByBackVoltage -= conductance
        self.backConductanceByFrontVoltage -= conductance
        self.backConductanceByBackVoltage += conductance

    def stamp_transient(self, environment: Environment, delta_t: int):
        self.stamp_static(environment)

    def close(self):
        self.closed = True

    def open(self):
        self.closed = False


Component.register(Switch)
