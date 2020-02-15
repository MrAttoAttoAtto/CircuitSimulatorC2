from matplotlib import pyplot as plt

from components.Inductor import Inductor
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import TransientSimulation

env = Environment()
# Really shouldn't manually access this, but it's for testing purposes
env.delta_t = 1e-5
vs = VoltageSource(9)
r = Resistor(5)
i = Inductor(1)

circ = Circuit(env)
circ.add(vs, (1, 0))
circ.add(r, (1, 2))
circ.add(i, (2, 0))
circ.finalise(0)

sim = TransientSimulation(circ, 10000, 1e-5)
n = 0
res = []
while True:
    sim.step()
    n += 1
    res.append(circ.getInputReference(2).value)
    if n > 1e5:
        fig, ax = plt.subplots()
        ax.plot([x * 1e-5 for x in range(100000)], res[:100000])
        fig.show()
        input()
