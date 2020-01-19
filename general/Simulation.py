from general.Circuit import Circuit


class TransientSimulation:
    def __init__(self, circuit: Circuit, convergence_limit: int, delta_t: float):
        # MUST be constant - the lambda catches the local variable
        self.delta_t = delta_t
        self.convergence_limit = convergence_limit
        self.circuit = circuit
        self.f = lambda c, e: c.stamp_transient(e, delta_t)

    def step(self):
        self.circuit.solve(self.convergence_limit, self.f)
        self.circuit.environment.time += self.delta_t


class StaticSimulation:
    def __init__(self, circuit: Circuit, convergence_limit: int):
        self.convergence_limit = convergence_limit
        self.circuit = circuit
        self.f = lambda c, e: c.stamp_static(e)

    def simulate(self):
        self.circuit.solve(self.convergence_limit, self.f)
