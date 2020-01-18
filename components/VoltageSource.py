from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class VoltageSource:
    """
    A standard DC voltage source
    """

    def __init__(self, voltage: float):
        """
        Creates a voltage source, setting all the nodes to None before the voltage source is connected

        :param voltage: The voltage of this source
        """

        # Basic voltage source properties
        self.voltage = voltage

        self.identifier = None

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

    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns the (single) cross-node entry required: the one from anode to cathode

        :param nodes: The nodes the voltage source will be connected to (anode, cathode)
        :param identifier: The identifier this voltage source will have in order to refer to the correct cross-node
        :return: The (single) cross-node entry required in a list: the one from anode to cathode
        """

        self.identifier = identifier

        anode, cathode = nodes
        anodeCathodeTuple = (anode, cathode, self.identifier)

        return [anodeCathodeTuple]

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the voltage source to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (2) nodes this voltage source is connected to, anode first, then cathode
        :return: None
        """

        anode, cathode = nodes
        anodeCathodeTuple = (anode, cathode, self.identifier)

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

    def stamp_static(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the voltage source would, after infinite time.

        :param environment: The environment of the circuit when this voltage source is operating
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

    def stamp_transient(self, environment: Environment, delta_t: int):
        self.stamp_static(environment)


Component.register(VoltageSource)
