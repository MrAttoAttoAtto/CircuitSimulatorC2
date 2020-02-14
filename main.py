from components.Diode import Diode
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment

env = Environment()
# Really shouldn't manually access this, but it's for testing purposes
env.delta_t = 1e-5
vs = VoltageSource(9)
r = Resistor(1)
d = Diode

circ = Circuit(env)
circ.add(vs, (1, 0))
circ.add(r, (2, 0))
circ.add(d, (1, 2))
circ.finalise(0)

n = 0
while True:
    circ.solve(100000, lambda c, e: c.stamp_static(e))
    n += 1
    if n > 100:
        break
