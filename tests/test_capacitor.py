import math

from testutils import isclose

from components.Capacitor import Capacitor
from components.Resistor import Resistor
from components.Switch import Switch
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import TransientSimulation


def test_capacitor_charge():
    environment = Environment()
    circuit = Circuit(environment)

    R = 1e4
    C = 1e-6
    RC = R * C

    res = Resistor(R)
    cap = Capacitor(C)
    pwr = VoltageSource(1)

    circuit.add(pwr, (1, 0))
    circuit.add(res, (1, 2))
    circuit.add(cap, (2, 0))
    circuit.finalise(0)

    vref = circuit.getInputReference(2)

    sim = TransientSimulation(circuit, 100, 1e-5)

    while environment.time < 5 * RC:
        sim.step()
        proper_v = 1 - math.e ** (-circuit.environment.time / RC)
        assert isclose(
            vref.value,
            proper_v)


def test_capacitor_discharge():
    environment = Environment()
    circuit = Circuit(environment)

    R = 1e4
    C = 1e-6
    RC = R * C

    sw = Switch(closed=True, closedG=1e10)
    res = Resistor(R)
    cap = Capacitor(C)
    pwr = VoltageSource(1)

    circuit.add(pwr, (1, 0))
    circuit.add(sw, (1, 2))
    circuit.add(cap, (2, 0))
    circuit.add(res, (2, 0))
    circuit.finalise(0)

    vref = circuit.getInputReference(2)

    sim = TransientSimulation(circuit, 1000, 1e-5)
    sim.step()
    sw.open()
    while environment.time < 5 * RC:
        sim.step()
        proper_v = math.e ** (-circuit.environment.time / RC)
        assert isclose(
            vref.value,
            proper_v)
