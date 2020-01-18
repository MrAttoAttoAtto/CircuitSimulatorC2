from typing import List, Tuple

from components.Component import Component
from general.Circuit import Circuit
from general.Environment import Environment


class OperationalAmplifier:
    """
    A standard operational amplifier, with standard configurable parameters
    """

    def __init__(self, openLoopGain: float, inputImpedance: float, outputImpedance: float, slewRate: float,
                 saturationOffsetVoltage: float, gainBandwidthProduct: float, inputOffsetVoltage: float):

        self.openLoopGain = openLoopGain
        self.inputImpedance = inputImpedance
        self.inputConductance = 1 / self.inputImpedance
        self.outputImpedance = outputImpedance
        self.slewRate = slewRate
        self.saturationOffsetVoltage = saturationOffsetVoltage
        self.gainBandwidthProduct = gainBandwidthProduct
        self.inputOffsetVoltage = inputOffsetVoltage

        self.identifier = None

        self.invertingVoltage = None
        self.nonInvertingVoltage = None
        self.outputVoltage = None
        self.supplyHiVoltage = None
        self.supplyLoVoltage = None

        self.currentThroughOutput = None

        self.invertingCurrent = None
        self.nonInvertingCurrent = None
        self.outputCurrent = None

        self.voltageAcrossOutput = None

        self.outputVoltageByNonInvertingVoltage = None
        self.outputVoltageByInvertingVoltage = None
        self.outputVoltageByCurrentThrough = None
        self.outputVoltageByOutputVoltage = None

        self.outputCurrentByCurrentThrough = None

        self.nonInvertingCurrentByNonInvertingVoltage = None
        self.nonInvertingCurrentByInvertingVoltage = None
        self.invertingCurrentByNonInvertingVoltage = None
        self.invertingCurrentByInvertingVoltage = None

    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int, int, int]]:
        """
        Returns the (single) cross-node entry required: the one from the anode of the internal "voltage source" (output)
        to the cathode (ground)

        :param nodes: The nodes the op-amp will be connected to:
        (invertingInput, nonInvertingInput, output, supplyHi, supplyLo)
        :param identifier: The identifier this op-amp will have in order to refer to the correct cross-node
        :return: The (single) cross-node entry required in a list: the one from anode to cathode of the internal
        voltage source
        """

        self.identifier = identifier

        invertingInput, nonInvertingInput, output, supplyHi, supplyLo = nodes
        anodeCathodeTuple = (output, 0, self.identifier)

        return [anodeCathodeTuple]

    def connect(self, circuit: Circuit, nodes: List[int]):
        invertingInput, nonInvertingInput, output, supplyHi, supplyLo = nodes
        anodeCathodeTuple = (output, 0, self.identifier)

        self.invertingVoltage = circuit.getInputReference(invertingInput)
        self.nonInvertingVoltage = circuit.getInputReference(nonInvertingInput)
        self.outputVoltage = circuit.getInputReference(output)
        self.supplyHiVoltage = circuit.getInputReference(supplyHi)
        self.supplyLoVoltage = circuit.getInputReference(supplyLo)

        self.currentThroughOutput = circuit.getInputReference(anodeCathodeTuple)

        self.invertingCurrent = circuit.getResultReference(invertingInput)
        self.nonInvertingCurrent = circuit.getResultReference(nonInvertingInput)
        self.outputCurrent = circuit.getResultReference(output)

        self.voltageAcrossOutput = circuit.getResultReference(anodeCathodeTuple)

        self.outputVoltageByNonInvertingVoltage = circuit.getJacobianReference(anodeCathodeTuple, nonInvertingInput)
        self.outputVoltageByInvertingVoltage = circuit.getJacobianReference(anodeCathodeTuple, invertingInput)
        self.outputVoltageByCurrentThrough = circuit.getJacobianReference(anodeCathodeTuple, anodeCathodeTuple)
        self.outputVoltageByOutputVoltage = circuit.getJacobianReference(anodeCathodeTuple, output)

        self.outputCurrentByCurrentThrough = circuit.getJacobianReference(output, anodeCathodeTuple)

        self.nonInvertingCurrentByNonInvertingVoltage = \
            circuit.getJacobianReference(nonInvertingInput, nonInvertingInput)
        self.nonInvertingCurrentByInvertingVoltage = circuit.getJacobianReference(nonInvertingInput, invertingInput)
        self.invertingCurrentByNonInvertingVoltage = circuit.getJacobianReference(invertingInput, nonInvertingInput)
        self.invertingCurrentByInvertingVoltage = circuit.getJacobianReference(invertingInput, invertingInput)

    def stamp_transient(self, environment: Environment, delta_t: int):
        """
        Amends the values at its nodes to affect the circuit as the op-amp would, in the time interval specified.

        :param environment: The environment of the circuit when this op-amp is operating
        :param delta_t: The time that has passed
        :return: None
        """
        # Adjusts the non-inverting voltage to take into account the input offset
        adjustedNonInvertingVoltage = self.nonInvertingVoltage.value - self.inputOffsetVoltage
        adjustedOldNonInvertingVoltage = self.nonInvertingVoltage.old - self.inputOffsetVoltage

        # The gain of the amplifier amplifies the difference of the two inputs
        outVoltage = (adjustedNonInvertingVoltage - self.invertingVoltage.value) * self.openLoopGain
        oldCoarseOutVoltage = (adjustedOldNonInvertingVoltage - self.invertingVoltage.old) * self.openLoopGain

        # if the op-amp is working without being bounded, and thus the derivatives are normal
        normalDerivatives = False
        # What a silly situation...
        if self.supplyLoVoltage > self.supplyHiVoltage:
            outVoltage = 0

        elif abs(outVoltage - oldCoarseOutVoltage) > self.slewRate * delta_t:
            # Slew rate restricts how fast this signal can increase
            if oldCoarseOutVoltage < outVoltage:
                outVoltage = oldCoarseOutVoltage + self.slewRate * delta_t
            else:
                outVoltage = oldCoarseOutVoltage - self.slewRate * delta_t

        elif outVoltage > self.supplyHiVoltage - self.saturationOffsetVoltage:
            # The output voltage would exceed the +ve supply voltage (accounting for saturation offset)

            # The offset would make it more negative that it could be. This is an illegal state,
            # so just choose a reasonable voltage
            if self.supplyHiVoltage - self.saturationOffsetVoltage < self.supplyLoVoltage:
                outVoltage = (self.supplyHiVoltage + self.supplyLoVoltage)/2
            else:
                outVoltage = self.supplyHiVoltage - self.saturationOffsetVoltage

        elif outVoltage < self.supplyLoVoltage + self.saturationOffsetVoltage:
            # The output voltage would be below the -ve supply voltage (accounting for saturation offset)

            # See above
            if self.supplyLoVoltage + self.saturationOffsetVoltage > self.supplyHiVoltage:
                outVoltage = (self.supplyHiVoltage + self.supplyLoVoltage)/2
            else:
                outVoltage = self.supplyLoVoltage + self.saturationOffsetVoltage

        else:
            normalDerivatives = True

        # By V=IR, this is the effect of the output impedance on the voltage of the output
        outVoltage -= self.currentThroughOutput.value * self.outputImpedance
        self.voltageAcrossOutput -= (outVoltage - self.outputVoltage.value)

        if normalDerivatives:
            self.outputVoltageByNonInvertingVoltage -= self.openLoopGain
            self.outputVoltageByInvertingVoltage += self.openLoopGain
            self.outputVoltageByCurrentThrough += self.outputImpedance
        # Otherwise, the derivatives are all 0 (except for outputVoltageByOutputVoltage), as changing the variables
        # would not (directly arithmetically) change the output voltage
        self.outputVoltageByOutputVoltage += 1

        self.outputCurrent += self.currentThroughOutput
        self.outputCurrentByCurrentThrough += 1

        # Creates the effective resistor between the inverting and non-inverting inputs
        inputCurrent = (adjustedNonInvertingVoltage - self.invertingVoltage.value) / self.inputImpedance
        self.nonInvertingCurrent += inputCurrent
        self.invertingCurrent -= inputCurrent

        self.nonInvertingCurrentByNonInvertingVoltage += self.inputConductance
        self.nonInvertingCurrentByInvertingVoltage -= self.inputConductance
        self.invertingCurrentByNonInvertingVoltage -= self.inputConductance
        self.invertingCurrentByInvertingVoltage += self.inputConductance


Component.register(OperationalAmplifier)
