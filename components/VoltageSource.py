from typing import List

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class VoltageSource:
    """
    A standard DC voltage source
    """

    isVoltageBased = True

    def __init__(self, voltage: float):
        """
        Creates a voltage source, setting all the nodes to None before the voltage source is connected

        :param voltage: The voltage of this source
        """

        # Basic voltage source properties
        self.voltage = voltage

        self.currentThroughReference = None
        self.anodeVoltageReference = None
        self.cathodeVoltageReference = None

        self.voltageAcrossReference = None
        self.anodeCurrentReference = None
        self.cathodeCurrentReference = None

        # Derivatives of the voltage source's voltage with respect to the anode and cathode voltages (always 1 or -1)
        self.anodeVoltageJacobianVoltageReference = None
        self.cathodeVoltageJacobianVoltageReference = None
        # Derivatives of the anode and cathode internal currents wrt the current through the
        # voltage source (i.e. always 1 or -1)
        self.anodeNodeJacobianCurrentReference = None
        self.cathodeNodeJacobianCurrentReference = None

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the voltage source to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (2) nodes this voltage source is connected to, anode first, then cathode
        :return: None
        """

        anode, cathode = nodes

        anodeCathodeTuple = (anode, cathode)

        self.currentThroughReference = circuit.getInputReference(anodeCathodeTuple)
        self.anodeVoltageReference = circuit.getInputReference(anode)
        self.cathodeVoltageReference = circuit.getInputReference(cathode)

        self.voltageAcrossReference = circuit.getResultReference(anodeCathodeTuple)
        self.anodeCurrentReference = circuit.getResultReference(anode)
        self.cathodeCurrentReference = circuit.getResultReference(cathode)

        self.anodeVoltageJacobianVoltageReference = circuit.getJacobianReference(anodeCathodeTuple, anode)
        self.cathodeVoltageJacobianVoltageReference = circuit.getJacobianReference(anodeCathodeTuple, cathode)
        self.anodeNodeJacobianCurrentReference = circuit.getJacobianReference(anode, anodeCathodeTuple)
        self.cathodeNodeJacobianCurrentReference = circuit.getJacobianReference(cathode, anodeCathodeTuple)

    def stamp(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the resistor would

        :param environment: The environment of the circuit at the given moment (in this case, not important)
        :return: None
        """

        # Finds the _difference_ between the voltage across it and what the voltage across it should really be
        self.voltageAcrossReference -= (self.voltage
                                        - (self.anodeVoltageReference.value - self.cathodeVoltageReference.value))

        # This is the current from the anode to the cathode - possibly not what you would expect
        self.anodeCurrentReference += self.currentThroughReference.value
        self.cathodeCurrentReference -= self.currentThroughReference.value

        self.anodeVoltageJacobianVoltageReference += 1
        self.cathodeVoltageJacobianVoltageReference -= 1
        self.anodeNodeJacobianCurrentReference += 1
        self.cathodeNodeJacobianCurrentReference -= 1


Component.register(VoltageSource)
