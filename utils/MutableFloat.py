class MutableFloat:
    def __init__(self, value=0.0):
        """
        Live is constantly updated, value is updated only once an entire matrix set has been constructed, and old holds
        the last step's values

        :param value: The initial value of the Mutable Float
        """
        self.value = value
        self.old = value

    def reset(self, value=0.0):
        self.old = self.value
        self.value = value

    def reset_without_old(self, value=0.0):
        self.value = value

    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __iadd__(self, other):
        self.value += other
        return self

    def __sub__(self, other):
        return self.value - other

    def __rsub__(self, other):
        return other - self.value

    def __isub__(self, other):
        self.value -= other
        return self

    def __repr__(self):
        return f"{self.value}"
