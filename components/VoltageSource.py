from typing import List

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class VoltageSource:
    """
    A standard DC voltage source
    """

    isVoltageSource = True

    def __init__(self, voltage: float):
        """
        Creates a voltage source, setting all the nodes to None before the voltage source is connected

        :param voltage: The voltage of this source
        """

        # Basic voltage source properties
        self.voltage = voltage

        # e.g. iv
        self.anodeInputCurrent = None
        self.cathodeInputCurrent = None

        # e.g. result_vector[0]
        self.anodeResultCurrent = None
        self.cathodeResultCurrent = None

        # e.g. result_vector[2]
        self.anodeResultVoltage = None
        self.cathodeResultVoltage = None

        self.anodeJacobianCurrentReference = None
        self.cathodeJacobianCurrentReference = None
        self.anodeJacobianCurrentReferenceInv = None
        self.cathodeJacobianCurrentReferenceInv = None

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the voltage source to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (2) nodes this voltage source is connected to, anode first, then cathode
        :return: None
        """

        anode, cathode = nodes

        self.anodeInputCurrent = circuit.getInputCurrentReference(anode)
        self.cathodeInputCurrent = circuit.getInputCurrentReference(cathode)

        self.anodeResultCurrent = circuit.getResultCurrentReference(anode)
        self.cathodeResultCurrent = circuit.getResultCurrentReference(cathode)

        self.anodeResultVoltage = circuit.getResultVoltageReference(anode)
        self.cathodeResultVoltage = circuit.getResultVoltageReference(cathode)

        self.anodeJacobianCurrentReference = circuit.getJacobianCurrentReference(anode, False)
        self.cathodeJacobianCurrentReference = circuit.getJacobianCurrentReference(cathode, False)
        self.anodeJacobianCurrentReferenceInv = circuit.getJacobianCurrentReference(anode, True)
        self.cathodeJacobianCurrentReferenceInv = circuit.getJacobianCurrentReference(cathode, True)

    def stamp(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the resistor would

        :param environment: The environment of the circuit at the given moment (in this case, not important)
        :return: None
        """

        self.anodeResultCurrent -= self.anodeInputCurrent
        self.cathodeInputCurrent += self.cathodeInputCurrent

        # At the end, CIRCUIT MUST ADD ANODE/CATHODE INPUT VOLTAGE!!!!!!!!
        self.anodeResultVoltage -= self.voltage
        self.cathodeResultVoltage += self.voltage

        self.anodeJacobianCurrentReference += 1
        self.cathodeJacobianCurrentReference -= 1
        self.anodeJacobianCurrentReferenceInv += 1
        self.cathodeJacobianCurrentReferenceInv -= 1


Component.register(VoltageSource)
