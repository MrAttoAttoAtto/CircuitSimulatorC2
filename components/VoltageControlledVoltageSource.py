from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class VoltageControlledVoltageSource:
    """
    An ideal voltage-controlled voltage source
    """

    def __init__(self, mu: float):
        """
        Makes the ideal VCVS, setting up all relevant values

        :param mu: The voltage gain of the VCVS, in volts/volt
        """

        self.mu = mu

        self.identifier = None

        self.anodeVoltage = None
        self.cathodeVoltage = None
        self.voltageControlAnode = None
        self.voltageControlCathode = None

        self.currentThrough = None

        self.anodeCurrent = None
        self.cathodeCurrent = None

        self.voltageAcross = None

        self.voltageAcrossByAnodeVoltage = None
        self.voltageAcrossByCathodeVoltage = None
        self.anodeCurrentByCurrentThrough = None
        self.cathodeCurrentByCurrentThrough = None

        self.voltageAcrossByControlAnodeVoltage = None
        self.voltageAcrossByControlCathodeVoltage = None

    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns the (single) cross-node entry required: the one from anode to cathode

        :param nodes: The nodes the voltage source will be connected to (anode, cathode)
        :param identifier: The identifier this voltage source will have in order to refer to the correct cross-node
        :return: The (single) cross-node entry required in a list: the one from anode to cathode
        """

        self.identifier = identifier

        anode, cathode, controlAnode, controlCathode = nodes
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

        anode, cathode, controlAnode, controlCathode = nodes
        anodeCathodeTuple = (anode, cathode, self.identifier)

        self.anodeVoltage = circuit.getInputReference(anode)
        self.cathodeVoltage = circuit.getInputReference(cathode)
        self.voltageControlAnode = circuit.getInputReference(controlAnode)
        self.voltageControlCathode = circuit.getInputReference(controlCathode)

        self.currentThrough = circuit.getInputReference(anodeCathodeTuple)

        self.anodeCurrent = circuit.getResultReference(anode)
        self.cathodeCurrent = circuit.getResultReference(cathode)

        self.voltageAcross = circuit.getResultReference(anodeCathodeTuple)

        self.voltageAcrossByAnodeVoltage = circuit.getJacobianReference(anodeCathodeTuple, anode)
        self.voltageAcrossByCathodeVoltage = circuit.getJacobianReference(anodeCathodeTuple, cathode)
        self.anodeCurrentByCurrentThrough = circuit.getJacobianReference(anode, anodeCathodeTuple)
        self.cathodeCurrentByCurrentThrough = circuit.getJacobianReference(cathode, anodeCathodeTuple)

        self.voltageAcrossByControlAnodeVoltage = circuit.getJacobianReference(anodeCathodeTuple, controlAnode)
        self.voltageAcrossByControlCathodeVoltage = circuit.getJacobianReference(anodeCathodeTuple, controlCathode)

    def stamp_static(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the voltage source would, after infinite time.

        :param environment: The environment of the circuit when this voltage source is operating
        :return: None
        """

        voltage = (self.voltageControlAnode.value - self.voltageControlCathode.value) * self.mu

        # Finds the _difference_ between the voltage across it and what the voltage across it should really be
        self.voltageAcross -= (voltage - (self.anodeVoltage.value - self.cathodeVoltage.value))

        # This is the current from the anode to the cathode - possibly not what you would expect
        self.anodeCurrent += self.currentThrough.value
        self.cathodeCurrent -= self.currentThrough.value

        self.voltageAcrossByAnodeVoltage += 1
        self.voltageAcrossByCathodeVoltage -= 1
        self.anodeCurrentByCurrentThrough += 1
        self.cathodeCurrentByCurrentThrough -= 1

        self.voltageAcrossByControlAnodeVoltage -= self.mu
        self.voltageAcrossByControlCathodeVoltage += self.mu

    def stamp_transient(self, environment: Environment, delta_t: int):
        self.stamp_static(environment)


Component.register(VoltageControlledVoltageSource)

VCVS = VoltageControlledVoltageSource
