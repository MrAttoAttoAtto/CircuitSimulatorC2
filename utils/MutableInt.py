class MutableInt:
    def __init__(self, value=0):
        self.value = value
        self.old = value

    def __iadd__(self, other):
        self.value += other

    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return self.value + other

    def __repr__(self):
        return f"{self.value}"
