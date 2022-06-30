from collections import deque

class SMA:
    def __init__(self, period: int):
        self.avg = 0
        self.vals = deque()
        self.p = period

    def next(self, data) -> float:
        self.vals.append(data)
        if len(self.vals) <= self.p:
            self.avg = sum(self.vals) / len(self.vals)
        else:
            old = self.vals.popleft()
            self.avg = self.avg + (data - old) / self.p

        return self.avg

    def getValue(self) -> float:
        return self.avg
