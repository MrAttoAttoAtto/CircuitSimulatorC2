from components.Diode import Diode
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment

env = Environment()
# Really shouldn't manually access this, but it's for testing purposes
env.delta_t = 1e-5
vs = VoltageSource(15)
di = Diode()
res = Resistor(100)

circuit = Circuit(env, env.delta_t)
circuit.add(vs, (1, 0))
circuit.add(di, (1, 2))
circuit.add(res, (2, 0))
circuit.finalise(0)

while True:
    circuit.simulate_step()
