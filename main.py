from components.Inductor import Inductor
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment

env = Environment()
# Really shouldn't manually access this, but it's for testing purposes
env.delta_t = 1e-5
vs = VoltageSource(9)
res = Resistor(100)
ind = Inductor(10)

circuit = Circuit(env, 0)
circuit.add(vs, (1, 0))
circuit.add(res, (1, 2))
circuit.add(ind, (2, 0))
circuit.finalise(66)

res.stamp(env)
ind.stamp(env)
vs.stamp(env)

pass
