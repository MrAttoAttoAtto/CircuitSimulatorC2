from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class Inductor:
    """
    A standard inductor
    """

    def __init__(self, inductance: float):
        """
        Creates an inductor, setting all the nodes to None before the inductor is connected

        :param inductance: The inductance of the inductor in Henrys
        """

        # Basic inductor properties
        self.inductance = inductance

        self.identifier = None

        # Inputs: Current through inductor, voltage at front and back
        self.currentThroughReference = None
        self.frontVoltageReference = None
        self.backVoltageReference = None

        # Outputs: Voltage across inductor, currents at front and back
        self.voltageAcrossReference = None
        self.frontCurrentReference = None
        self.backCurrentReference = None

        # Jacobian stuff for what it changes, using which inputs
        self.frontVoltageJacobianVoltageReference = None
        self.backVoltageJacobianVoltageReference = None
        self.frontNodeJacobianCurrentReference = None
        self.backNodeJacobianCurrentReference = None

    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns the (single) cross-node entry required: the one from front to back

        :param nodes: The nodes this inductor is connected to (front, back)
        :param identifier: This inductor's identifier
        :return: The (single) cross-node entry required in a list: the one from front to back
        """

        self.identifier = identifier

        frontNode, backNode = nodes
        frontBackTuple = (frontNode, backNode, identifier)

        return [frontBackTuple]

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the inductor to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (2) nodes this inductor is connected to
        :return: None
        """

        frontNode, backNode = nodes
        frontBackTuple = (frontNode, backNode)

        self.currentThroughReference = circuit.getInputReference(frontBackTuple)
        self.frontVoltageReference = circuit.getInputReference(frontNode)
        self.backVoltageReference = circuit.getInputReference(backNode)

        self.voltageAcrossReference = circuit.getResultReference(frontBackTuple)
        self.frontCurrentReference = circuit.getResultReference(frontNode)
        self.backCurrentReference = circuit.getResultReference(backNode)

        self.frontVoltageJacobianVoltageReference = circuit.getJacobianReference(frontBackTuple, frontNode)
        self.backVoltageJacobianVoltageReference = circuit.getJacobianReference(frontBackTuple, backNode)
        self.frontNodeJacobianCurrentReference = circuit.getJacobianReference(frontNode, frontBackTuple)
        self.backNodeJacobianCurrentReference = circuit.getJacobianReference(backNode, frontBackTuple)

    def stamp_transient(self, environment: Environment, delta_t: int):
        """
        Amends the values at its nodes to affect the circuit as the inductor would, in the time interval specified.

        :param environment: The environment of the circuit when this inductor is operating
        :param delta_t: The time that has passed
        :return: None
        """

        # "Instantaneous" rate of change of current
        dI_dt = (self.currentThroughReference.value - self.currentThroughReference.old) / delta_t

        # Finds the _difference_ between the voltage across it and what the voltage across it should really be
        # When 0, that's good!
        self.voltageAcrossReference -= (self.inductance * dI_dt
                                        - (self.frontVoltageReference.value - self.backVoltageReference.value))

        # This is the current from the anode to the cathode - possibly not what you would expect
        self.frontCurrentReference += self.currentThroughReference.value
        self.backCurrentReference -= self.currentThroughReference.value

        self.frontVoltageJacobianVoltageReference += 1
        self.backVoltageJacobianVoltageReference -= 1
        self.frontNodeJacobianCurrentReference += 1
        self.backNodeJacobianCurrentReference -= 1


Component.register(Inductor)
