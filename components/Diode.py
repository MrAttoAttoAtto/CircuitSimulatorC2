import math
from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class Diode:
    """
    A basic diode using the Schottky Diode Equation
    """

    def __init__(self, breakdownVoltage: float = 40, saturationCurrent: float = 1e-12, ideality: float = 1):
        """
        Creates a diode, setting all the nodes to None before the resistor is connected

        :param breakdownVoltage: The voltage (in Volts) at which the diode breaks down when in reverse bias
        :param saturationCurrent: The current (in Amps) allowed to flow when the diode is in reverse bias
        :param ideality: The ideality (n) of the diode as modelled by the Schottky Diode Equation
        """
        
        # Basic diode properties
        self.breakdownVoltage = breakdownVoltage
        self.saturationCurrent = saturationCurrent
        self.ideality = ideality

        # The objects that will hold the voltage at the anode and cathode nodes of the resistor
        # These are the values corresponding to the anode and cathode nodes in the INPUT VECTOR
        self.anodeVoltage = None
        self.cathodeVoltage = None

        # The objects that will hold the current at the anode and cathode nodes of the resistor
        # These are the values corresponding to the anode and cathode nodes in the RESULT VECTOR
        self.anodeCurrent = None
        self.cathodeCurrent = None

        # The objects that will hold the conductances at the anode and cathode nodes in the resistor: in essence
        # the derivatives of the currents with respect to the anode and cathode voltages
        # These are the values corresponding to the anode and cathode nodes in the JACOBIAN MATRIX
        self.anodeConductanceByAnodeVoltage = None
        self.anodeConductanceByCathodeVoltage = None
        self.cathodeConductanceByAnodeVoltage = None
        self.cathodeConductanceByCathodeVoltage = None

    # noinspection PyMethodMayBeStatic
    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns an empty list as cross-node entries are not required for a diode

        :param nodes: The nodes this diode is connected to (anode, cathode)
        :param identifier: This diode's identifier
        :return: An empty list
        """

        return []

    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the diode to its specified nodes

        Sets the matrix/vector reference objects as defined above
        :param circuit: The circuit
        :param nodes: A list of the (2) nodes this diode is connected to, with the anode being first
        :return: None
        """

        anodeNode, cathodeNode = nodes
        self.anodeVoltage = circuit.getInputReference(anodeNode)
        self.cathodeVoltage = circuit.getInputReference(cathodeNode)

        self.anodeCurrent = circuit.getResultReference(anodeNode)
        self.cathodeCurrent = circuit.getResultReference(cathodeNode)

        self.anodeConductanceByAnodeVoltage = circuit.getJacobianReference(anodeNode, anodeNode)
        self.anodeConductanceByCathodeVoltage = circuit.getJacobianReference(anodeNode, cathodeNode)
        self.cathodeConductanceByAnodeVoltage = circuit.getJacobianReference(cathodeNode, anodeNode)
        self.cathodeConductanceByCathodeVoltage = circuit.getJacobianReference(cathodeNode, cathodeNode)

    def stamp_static(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the diode would, after infinite time.

        :param environment: The environment of the circuit when this diode is operating
        :return: None
        """

        thermalVoltage = environment.k * environment.temperature / environment.q
        idealityTemperatureModifier = self.ideality * thermalVoltage

        voltageAcross = self.anodeVoltage.value - self.cathodeVoltage.value

        # If the diode is in reverse bias more strong than the breakdown voltage, it's broken down!
        if voltageAcross < -self.breakdownVoltage:
            reverseBiasVoltage = -self.breakdownVoltage - voltageAcross
            current = -(self.saturationCurrent * math.exp(reverseBiasVoltage/idealityTemperatureModifier))

            conductance = self.saturationCurrent * \
                math.exp(reverseBiasVoltage/idealityTemperatureModifier) / idealityTemperatureModifier

        else:
            current = self.saturationCurrent * (math.exp(voltageAcross/idealityTemperatureModifier) - 1)

            conductance = self.saturationCurrent * \
                math.exp(voltageAcross/idealityTemperatureModifier) / idealityTemperatureModifier

        self.anodeCurrent += current
        self.cathodeCurrent -= current

        self.anodeConductanceByAnodeVoltage += conductance
        self.anodeConductanceByCathodeVoltage -= conductance
        self.cathodeConductanceByAnodeVoltage -= conductance
        self.cathodeConductanceByCathodeVoltage += conductance

    def stamp_transient(self, environment: Environment, delta_t: int):
        self.stamp_static(environment)


Component.register(Diode)
