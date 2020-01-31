class Environment:
    """
    A class to hold general data about a circuit's environment, common to all components
    """

    def __init__(self, temperature: float = 293.15, k: float = 1.38064852e-23, q: float = 1.60217662e-19,
                 iMin: float = 1e-9, gMin: float = 1e-12):
        """
        Creates the environment with the desired starting values

        :param temperature: The temperature of the circuit in Kelvin
        :param k: The Boltzmann constant
        :param q: The elementary charge
        """
        self.temperature = temperature
        self.k = k
        self.q = q
        self.iMin = iMin
        self.gMin = gMin

        # The starting time can always be 0: setting a different time would make no difference as only the passage of
        # time matters
        self.time = 0
