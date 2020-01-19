from components.Diode import Diode
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment

env = Environment()
# Really shouldn't manually access this, but it's for testing purposes
env.delta_t = 1e-5
vs = VoltageSource(10)
vs2 = VoltageSource(10)
vs3 = VoltageSource(0)
Rtop = Resistor(1e3)
Rld = Resistor(1e4)
di1 = Diode()
di2 = Diode()
R1 = Resistor(10)
R2 = Resistor(10)

circuit = Circuit(env)
circuit.add(vs, (1, 0))
circuit.add(Rtop, (1, 2))
circuit.add(Rld, (2, 0))
circuit.add(di1, (2, 3))
circuit.add(di2, (2, 4))
circuit.add(vs2, (3, 5))
circuit.add(vs3, (4, 6))
circuit.add(R1, (5, 0))
circuit.add(R2, (6, 0))
circuit.finalise(0)


n = 0
while True:
    circuit.solve(100000, lambda c, e: c.stamp_static(e))
    n += 1
    if n > 100:
        break
