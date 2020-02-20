from components.VoltageSource import VoltageSource
from general.Environment import Environment
from general.Exceptions import TransientException


class SweepVoltageSource(VoltageSource):
    """
    A linearly sweeping DC voltage source
    """

    def __init__(self, startVoltage: float = 0, rate: float = 1):
        """
        Creates a linearly sweeping DC voltage source

        :param startVoltage: The voltage this voltage source should start at
        :param rate: The increase in volts per second, the rate this source should sweep at
        """
        self.startVoltage = startVoltage
        self.rate = rate

        super().__init__(0)

    def stamp_static(self, environment: Environment):
        raise TransientException("A sweeping voltage source cannot be run in a static simulation")

    def stamp_transient(self, environment: Environment, delta_t: int):
        self.voltage = self.startVoltage + environment.time * self.rate
        super().stamp_static(environment)
