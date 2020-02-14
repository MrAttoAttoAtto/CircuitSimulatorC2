import math

from components.VoltageSource import VoltageSource
from general.Environment import Environment
from general.Exceptions import TransientException


class ACVoltageSource(VoltageSource):
    """
    A sinusoidal voltage source
    """

    def __init__(self, peakVoltage: float = 10, frequency: float = 1):
        """
        Creates an AC voltage source, setting all the nodes to None before the voltage source is connected

        :param peakVoltage: The peak voltage of the AC source in Volts
        :param frequency: The frequency of the AC source in Hertz
        """
        self.peakVoltage = peakVoltage
        self.frequency = frequency

        super().__init__(0)

    def stamp_static(self, environment: Environment):
        raise TransientException("An AC voltage source cannot be run in a static simulation")

    def stamp_transient(self, environment: Environment, delta_t: int):
        self.voltage = math.sin(environment.time * self.frequency * 2 * math.pi) * self.peakVoltage
        super().stamp_static(environment)
