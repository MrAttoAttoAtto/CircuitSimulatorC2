import math
from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class MOSFET:
    """
    A normal MOSFET
    """

    def __init__(self, thresholdVoltage: float = 3, width: float = 1e-6, length: float = 1e-9,
                 specificCapacitance: float = 1e-2, electronMobility: float = 500e-4):
        """
        Initialises the MOSFET with its given characteristics

        :param thresholdVoltage: The gate voltage below which the device will operate in the cutoff region
        :param width: The width of the MOSFET
        :param length: The length of the MOSFET
        :param specificCapacitance: The specific capacitance of the oxide layer of the MOSFET
        :param electronMobility: The speed at which an electron moves through the MOSFET per unit voltage. Note that
        the units for this parameter are m^2/(Vs) (i.e. the SI units), NOT cm^2/(Vs)
        """

        self.thresholdVoltage = thresholdVoltage

        self.currentFactor = (electronMobility * specificCapacitance) / 2 * (width / length)

        self.gateVoltage = None
        self.sourceVoltage = None
        self.drainVoltage = None

        self.gateCurrent = None
        self.sourceCurrent = None
        self.drainCurrent = None

        # Should be 0, but that won't work, so it'll just be really low (gMin)
        self.gateCurrentByGateVoltage = None

        self.sourceCurrentByGateVoltage = None
        self.drainCurrentByGateVoltage = None

        self.sourceCurrentBySourceVoltage = None
        self.drainCurrentBySourceVoltage = None
        self.sourceCurrentByDrainVoltage = None
        self.drainCurrentByDrainVoltage = None

    # noinspection PyMethodMayBeStatic
    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns an empty list as cross-node entries are not required for a MOSFET

        :param nodes: The 3 nodes this diode is connected to (gate, source, drain)
        :param identifier: This diode's identifier
        :return: An empty list
        """

        return []

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the MOSFET to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (3) nodes this MOSFET is connected to: (gate, source, drain)
        :return: None
        """

        gateNode, sourceNode, drainNode = nodes

        self.gateVoltage = circuit.getInputReference(gateNode)
        self.sourceVoltage = circuit.getInputReference(sourceNode)
        self.drainVoltage = circuit.getInputReference(drainNode)

        self.gateCurrent = circuit.getResultReference(gateNode)
        self.sourceCurrent = circuit.getResultReference(sourceNode)
        self.drainCurrent = circuit.getResultReference(drainNode)

        # Should be 0, but that won't work, so it'll just be really low (gMin)
        self.gateCurrentByGateVoltage = circuit.getJacobianReference(gateNode, gateNode)

        self.sourceCurrentByGateVoltage = circuit.getJacobianReference(sourceNode, gateNode)
        self.drainCurrentByGateVoltage = circuit.getJacobianReference(drainNode, gateNode)

        self.sourceCurrentBySourceVoltage = circuit.getJacobianReference(sourceNode, sourceNode)
        self.drainCurrentBySourceVoltage = circuit.getJacobianReference(drainNode, sourceNode)
        self.sourceCurrentByDrainVoltage = circuit.getJacobianReference(drainNode, sourceNode)
        self.drainCurrentByDrainVoltage = circuit.getJacobianReference(drainNode, drainNode)

    def stamp_static(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the diode would, after infinite time.

        :param environment: The environment of the circuit when this diode is operating
        :return: None
        """

        gateSourceVoltage = self.gateVoltage - self.sourceVoltage
        drainSourceVoltage = self.drainVoltage - self.sourceVoltage

        gateSourceSign = math.copysign(1, gateSourceVoltage)
        self.gateCurrent += environment.iMin * gateSourceSign
        self.gateCurrentByGateVoltage += environment.gMin * gateSourceSign

        if gateSourceVoltage < self.thresholdVoltage:
            # Off region
            sign = math.copysign(1, drainSourceVoltage)
            current = environment.iMin * sign
            conductance = environment.gMin * sign

            # Act like a pretty strong resistor!
            self.sourceCurrentBySourceVoltage += conductance
            self.drainCurrentBySourceVoltage -= conductance
            self.sourceCurrentByDrainVoltage -= conductance
            self.drainCurrentByDrainVoltage += conductance

        elif drainSourceVoltage < gateSourceVoltage - self.thresholdVoltage:
            # Linear region
            current = self.currentFactor * (2 * (gateSourceVoltage - self.thresholdVoltage) * drainSourceVoltage
                                            - drainSourceVoltage ** 2)

            gateConductance = self.currentFactor * 2 * (self.drainVoltage - self.sourceVoltage)
            sourceConductance = self.currentFactor * 2 * (self.sourceVoltage - self.gateVoltage)
            drainConductance = self.currentFactor * 2 * (self.gateVoltage - self.drainVoltage)

            self.sourceCurrentByGateVoltage -= gateConductance
            self.drainCurrentByGateVoltage += gateConductance

            self.sourceCurrentBySourceVoltage += sourceConductance
            self.drainCurrentBySourceVoltage -= sourceConductance

            self.drainCurrentBySourceVoltage -= drainConductance
            self.drainCurrentByDrainVoltage += drainConductance
        else:
            # Saturation region
            current = self.currentFactor * (gateSourceVoltage - self.thresholdVoltage) ** 2

            conductance = self.currentFactor * 2 * (gateSourceVoltage - self.thresholdVoltage)

            self.sourceCurrentByGateVoltage -= conductance
            self.drainCurrentByGateVoltage += conductance

            self.sourceCurrentBySourceVoltage += conductance
            self.drainCurrentBySourceVoltage -= conductance

        self.sourceCurrent -= current
        self.drainCurrent += current

    def stamp_transient(self, environment: Environment, delta_t: int):
        self.stamp_static(environment)


Component.register(MOSFET)
