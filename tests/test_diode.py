from testutils import isclose

from components.Diode import Diode
from components.Resistor import Resistor
from components.VoltageSource import VoltageSource
from general.Circuit import Circuit
from general.Environment import Environment
from general.Simulation import StaticSimulation


def test_diode_forward_bias():
    environment = Environment()
    circuit = Circuit(environment)

    source = VoltageSource(10)
    res = Resistor(100)
    diode = Diode(40, 1e-12, 1)

    circuit.add(source, (1, 0))
    circuit.add(res, (1, 2))
    circuit.add(diode, (2, 0))
    circuit.finalise(0)

    diodeVoltage = circuit.getInputReference(2)
    circuitCurrent = circuit.getInputReference((1, 0, source.identifier))

    sim = StaticSimulation(circuit, 100)
    sim.simulate()

    assert isclose(diodeVoltage.value, 0.638)
    # -ve because that's the current from cathode to anode, not vice versa
    assert isclose(circuitCurrent.value, -0.0936)


def test_diode_reverse_bias():
    environment = Environment()
    circuit = Circuit(environment)

    source = VoltageSource(10)
    res = Resistor(100)
    diode = Diode(40, 1e-12, 1)

    circuit.add(source, (1, 0))
    circuit.add(res, (1, 2))
    circuit.add(diode, (0, 2))
    circuit.finalise(0)

    diodeVoltage = circuit.getInputReference(2)
    circuitCurrent = circuit.getInputReference((1, 0, source.identifier))

    sim = StaticSimulation(circuit, 100)
    sim.simulate()

    assert isclose(diodeVoltage.value, 10)
    assert isclose(circuitCurrent.value, 0)


def test_diode_breakdown():
    environment = Environment()
    circuit = Circuit(environment)

    # Breakdown voltage is 40V
    source = VoltageSource(50)
    res = Resistor(100)
    diode = Diode(40, 1e-12, 1)

    circuit.add(source, (1, 0))
    circuit.add(res, (1, 2))
    circuit.add(diode, (0, 2))
    circuit.finalise(0)

    diodeVoltage = circuit.getInputReference(2)
    circuitCurrent = circuit.getInputReference((1, 0, source.identifier))

    sim = StaticSimulation(circuit, 10000)
    sim.simulate()

    # Remember 0.638 and -0.0936?
    assert isclose(diodeVoltage.value, 40.638)
    assert isclose(circuitCurrent.value, -0.0936)
