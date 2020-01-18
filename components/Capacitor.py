from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class Capacitor:

    isVoltageBased = False

    def __init__(self, capacitance: float):
        self.capacitance = capacitance

        # The objects that will hold the voltage at the front and back nodes of the resistor
        # These are the values corresponding to the front and back nodes in the INPUT VECTOR
        self.frontVoltage = None
        self.backVoltage = None

        # The objects that will hold the current at the front and back nodes of the resistor
        # These are the values corresponding to the front and back nodes in the RESULT VECTOR
        self.frontCurrent = None
        self.backCurrent = None

        # The objects that will hold the conductances at the front and back nodes in the resistor: in essence
        # the derivatives of the currents with respect to the front and back voltages
        # These are the values corresponding to the front and back nodes in the JACOBIAN MATRIX
        self.frontConductanceByFrontVoltage = None
        self.frontConductanceByBackVoltage = None
        self.backConductanceByFrontVoltage = None
        self.backConductanceByBackVoltage = None

    # noinspection PyMethodMayBeStatic
    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns an empty list as cross-node entries are not required for a capacitor

        :param nodes: The nodes this capacitor is connected to
        :param identifier: This capacitor's identifier
        :return: An empty list
        """

        return []

    def connect(self, circuit: Circuit, nodes: List[int]):
        frontNode, backNode = nodes
        self.frontVoltage = circuit.getInputReference(frontNode)
        self.backVoltage = circuit.getInputReference(backNode)

        self.frontCurrent = circuit.getResultReference(frontNode)
        self.backCurrent = circuit.getResultReference(backNode)

        self.frontConductanceByFrontVoltage = circuit.getJacobianReference(frontNode, frontNode)
        self.frontConductanceByBackVoltage = circuit.getJacobianReference(frontNode, backNode)
        self.backConductanceByFrontVoltage = circuit.getJacobianReference(backNode, frontNode)
        self.backConductanceByBackVoltage = circuit.getJacobianReference(backNode, backNode)

    def stamp_transient(self, environment: Environment, delta_t: int):
        """
        Amends the values at its nodes to affect the circuit as the capacitor would, in the time interval specified.

        :param environment: The environment of the circuit when this capacitor is operating
        :param delta_t: The time that has passed
        :return: None
        """
        derivative_scale = self.capacitance / delta_t
        delta_v = (self.frontVoltage.value - self.backVoltage.value) - (self.frontVoltage.old - self.backVoltage.old)

        self.frontCurrent += delta_v * derivative_scale
        self.backCurrent -= delta_v * derivative_scale

        self.frontConductanceByFrontVoltage += derivative_scale
        self.frontConductanceByBackVoltage -= derivative_scale
        self.backConductanceByFrontVoltage -= derivative_scale
        self.backConductanceByBackVoltage += derivative_scale


Component.register(Capacitor)
