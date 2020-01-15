import abc
from typing import List

from general.Circuit import Circuit

from general.Environment import Environment


class Component(abc.ABC):
    """
    Abstract base class for components
    """

    @abc.abstractmethod
    def __init__(self):
        """
        Creates the component with its attributes and sets its node variables to None

        The arguments should be some attributes physically related to the component, e.g. resistance
        """

    @abc.abstractmethod
    def connect(self, circuit: Circuit, nodes: List[int]):
        """
        Connects the component to its nodes by setting its node variables

        The arguments should be all the node MutableFloats in order
        :param circuit: The circuit this component is in
        :param nodes: A list of the nodes this component is connected to, in the right order for this component
        :return: None
        """

    @abc.abstractmethod
    def stamp(self, environment: Environment):
        """
        Amends the values at its nodes to affect the circuit as the component would

        :param environment: The environment of the circuit when this component is operating
        :return: None
        """
