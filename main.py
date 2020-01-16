from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment

env = Environment()
res = Resistor(2)
pwr = VoltageSource(10)

circuit = Circuit(env, 0)
circuit.add(pwr, (0, 1))
circuit.add(res, (0, 1))
circuit.finalise(0)

circuit.simulate_step()
