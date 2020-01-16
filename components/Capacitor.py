from typing import List

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class Capacitor:
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

    def connect(self, circuit: Circuit, nodes: List[int]):
        frontNode, backNode = nodes
        self.frontVoltage = circuit.getInputVoltageReference(frontNode)
        self.backVoltage = circuit.getInputVoltageReference(backNode)

        self.frontCurrent = circuit.getResultCurrentReference(frontNode)
        self.backCurrent = circuit.getResultCurrentReference(backNode)

        self.frontConductanceByFrontVoltage = circuit.getJacobianVoltageReference(frontNode, frontNode)
        self.frontConductanceByBackVoltage = circuit.getJacobianVoltageReference(frontNode, backNode)
        self.backConductanceByFrontVoltage = circuit.getJacobianVoltageReference(backNode, frontNode)
        self.backConductanceByBackVoltage = circuit.getJacobianVoltageReference(backNode, backNode)

    def stamp(self, environment: Environment):
        derivative_scale = self.capacitance / environment.delta_t
        delta_v = (self.frontVoltage - self.backVoltage) - (self.frontVoltage.old - self.backVoltage.old)

        self.frontCurrent += delta_v * derivative_scale
        self.backCurrent -= delta_v * derivative_scale

        self.frontConductanceByFrontVoltage += derivative_scale
        self.frontConductanceByBackVoltage -= derivative_scale
        self.backConductanceByFrontVoltage -= derivative_scale
        self.backConductanceByBackVoltage += derivative_scale


Component.register(Capacitor)
