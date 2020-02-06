from components.MOSFET import MOSFET
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment

env = Environment()
# Really shouldn't manually access this, but it's for testing purposes
env.delta_t = 1e-5
vs = VoltageSource(10)
Mo = MOSFET()
r1 = Resistor(100)
r2 = Resistor(100)
r3 = Resistor(12)

circ = Circuit(env)
circ.add(vs, (1, 0))
circ.add(r1, (1, 2))
circ.add(r2, (2, 0))
circ.add(r3, (1, 3))
circ.add(Mo, (2, 0, 3))
circ.finalise(0)


n = 0
while True:
    circ.solve(100000, lambda c, e: c.stamp_static(e))
    n += 1
    if n > 100:
        break
