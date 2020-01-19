class MutableFloat:
    def __init__(self, value=0.0):
        """
        Live is constantly updated, value is updated only once an entire matrix set has been constructed, and old holds
        the last step's values

        :param value: The initial value of the Mutable Float
        """
        self.live = value
        self.value = value
        self.old = value

    def update(self):
        self.value = self.live

    def reset(self, value=0.0):
        self.old = self.live
        self.value = value
        self.live = value

    def __add__(self, other):
        return self.live + other

    def __radd__(self, other):
        return other + self.live

    def __iadd__(self, other):
        self.live += other
        return self

    def __sub__(self, other):
        return self.live - other

    def __rsub__(self, other):
        return other - self.live

    def __isub__(self, other):
        self.live -= other
        return self

    def __gt__(self, other):
        return self.value > other

    def __lt__(self, other):
        return self.value < other

    def __repr__(self):
        return f"{self.live}"
