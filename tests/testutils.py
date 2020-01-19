import math


def isclose(a, b):
    return math.isclose(a, b, rel_tol=0.001, abs_tol=0.001)
