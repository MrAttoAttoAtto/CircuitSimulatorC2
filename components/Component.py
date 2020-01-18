import abc
from typing import List, Tuple

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
    def getRequiredCrossNodes(self, nodes: List[int], identifier: int) -> List[Tuple[int]]:
        """
        Returns tuples denoting the node connections that need to have a "cross-node" entry in the matrices
        For example, current-through in the input vector and voltage-across in the result vector
        Also gives an opportunity for the component to save its identifier

        :param nodes: The nodes the component will be connected to (in the right order)
        :param identifier: The identifier this component will have in order to refer to the correct cross-node
        :return: A list of tuples (nodeA, nodeB, identifier) representing each required cross-node
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
