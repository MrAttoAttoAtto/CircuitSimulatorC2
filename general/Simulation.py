from general.Circuit import Circuit


class TransientSimulation:
    def __init__(self, circuit: Circuit, convergence_limit: int, delta_t: float):
        self.delta_t = delta_t
        self.convergence_limit = convergence_limit
        self.circuit = circuit

    def step(self):
        self.circuit.solve(self.convergence_limit, lambda c, e: c.stamp_transient(e, self.delta_t))
        self.circuit.environment.time += self.delta_t
