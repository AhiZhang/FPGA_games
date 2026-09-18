from .constants import STABLE_N


class Buttons:
    """Debounced rising-edge reader. Holding a key does not retrigger."""

    def __init__(self, gpio):
        self.gpio = gpio
        self._raw = [0, 0, 0, 0]
        self._stable = [0, 0, 0, 0]
        self._count = [0, 0, 0, 0]
        self._prev = [0, 0, 0, 0]

    def _read_raw(self):
        val = int(self.gpio.read()) & 0xF
        return [(val >> i) & 1 for i in range(4)]

    def poll(self):
        raw = self._read_raw()
        for i in range(4):
            if raw[i] == self._raw[i]:
                self._count[i] += 1
            else:
                self._raw[i] = raw[i]
                self._count[i] = 1
            if self._count[i] >= STABLE_N:
                self._stable[i] = self._raw[i]
        edges = []
        for i in range(4):
            if self._stable[i] and not self._prev[i]:
                edges.append(i)
            self._prev[i] = self._stable[i]
        return edges
