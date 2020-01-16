from typing import List

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class Inductor:
    """
    A standard inductor
    """

    isVoltageBased = True

    def __init__(self, inductance: float):
        """
        Creates an inductor, setting all the nodes to None before the inductor is connected

        :param inductance: The inductance of the inductor in Henrys
        """

        # Basic inductor properties
        self.inductance = inductance

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

    def stamp(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the inductor would

        :param environment: The environment of the circuit at the given moment (in this case, not important)
        :return: None
        """

        # "Instantaneous" rate of change of current
        dI_dt = (self.currentThroughReference - self.currentThroughReference.old) / environment.delta_t

        # Finds the _difference_ between the voltage across it and what the voltage across it should really be
        # When 0, that's good!
        self.voltageAcrossReference -= (self.inductance * dI_dt
                                        - (self.frontVoltageReference - self.backVoltageReference))

        # This is the current from the anode to the cathode - possibly not what you would expect
        self.frontCurrentReference += self.currentThroughReference
        self.backCurrentReference -= self.currentThroughReference

        self.frontVoltageJacobianVoltageReference += 1
        self.backVoltageJacobianVoltageReference -= 1
        self.frontNodeJacobianCurrentReference += 1
        self.backNodeJacobianCurrentReference -= 1


Component.register(Inductor)
