from components.Resistor import Resistor
from general.Circuit import Circuit
from general.Environment import Environment

env = Environment()
res = Resistor(2)

circuit = Circuit(env, 0)
circuit.add(res, (0, 1))
circuit.finalise(66)

res.stamp(env)

pass
