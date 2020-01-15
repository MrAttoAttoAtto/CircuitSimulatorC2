from typing import List

from general.Circuit import Circuit

from components.Component import Component
from general.Environment import Environment


class Resistor:
    """
    A standard Ohm's law-obeying resistor
    """

    def __init__(self, resistance: float):
        """
        Creates a resistor, setting all the nodes to None before the resistor is connected

        :param resistance: The resistance of the resistor in Ohms
        """

        # Basic resistor properties
        self.resistance = resistance
        self.conductance = 1 / self.resistance

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

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the resistor to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (2) nodes this resistor is connected to
        :return: None
        """

        # TODO

        frontNode, backNode = nodes

        # As opposed to getInputCurrentReference for voltage sources etc.
        # frontVoltageIndicator should be something usable to relate this value to a position in the Jacobian
        frontVoltageIndicator, self.frontVoltage = circuit.getInputVoltageReference(frontNode)
        backVoltageIndicator, self.backVoltage = circuit.getInputVoltageReference(backNode)

        self.frontCurrent = circuit.getResultReference(frontNode)
        self.backCurrent = circuit.getResultReference(backNode)

        # Coordinate-type system with the jacobian: handled by the Circuit class
        self.frontConductanceByFrontVoltage = circuit.getJacobianReference(frontNode, frontVoltageIndicator)
        self.frontConductanceByBackVoltage = circuit.getJacobianReference(frontNode, backVoltageIndicator)
        self.backConductanceByFrontVoltage = circuit.getJacobianReference(backNode, frontVoltageIndicator)
        self.backConductanceByBackVoltage = circuit.getJacobianReference(backNode, backVoltageIndicator)

    def stamp(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the resistor would

        :param environment: The environment of the circuit at the given moment (in this case, not important)
        :return: None
        """

        # +ve means current is flowing _out_ of that node into this component
        self.frontCurrent += (self.frontVoltage - self.backVoltage) / self.resistance
        self.backCurrent -= (self.frontVoltage - self.backVoltage) / self.resistance

        self.frontConductanceByFrontVoltage += self.conductance
        self.frontConductanceByBackVoltage -= self.conductance
        self.backConductanceByFrontVoltage -= self.conductance
        self.backConductanceByBackVoltage += self.conductance


Component.register(Resistor)