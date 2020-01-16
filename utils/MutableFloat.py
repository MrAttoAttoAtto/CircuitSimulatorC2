class MutableFloat:
    def __init__(self, value=0.0):
        self.value = value
        self.old = value

    def reset(self, value=0.0):
        self.old = self.value
        self.value = value

    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __iadd__(self, other):
        self.value += other

    def __sub__(self, other):
        return self.value - other

    def __rsub__(self, other):
        return other - self.value

    def __isub__(self, other):
        self.value -= other

    def __repr__(self):
        return f"{self.value}"
