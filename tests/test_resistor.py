from testutils import isclose

from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import StaticSimulation


def test_resistor_static():
    environment = Environment()
    circuit = Circuit(environment)

    res1 = Resistor(500)
    res2 = Resistor(500)
    pwr = VoltageSource(1)

    circuit.add(pwr, (1, 0))
    circuit.add(res1, (1, 2))
    circuit.add(res2, (2, 0))
    circuit.finalise(0)

    vref = circuit.getInputReference(2)

    sim = StaticSimulation(circuit, 100)

    sim.simulate()
    assert isclose(vref.value, 0.5)

    res1.resistance = 1000
    sim.simulate()
    assert isclose(vref.value, 1 / 3)
