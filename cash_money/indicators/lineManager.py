from collections import deque
from typing import Deque, Dict, Set, List, Tuple, Optional

from cash_money.cmErrors import IndicatorError

LOW = 'low'
CLOSE = 'close'
HIGH = 'high'
VOLUME = "volume"


def _mangle(indicatorName: str, lineName: str) -> str:
    return f'{indicatorName}_{lineName}'


class LineDeque:
    def __init__(self, maxLen: int = 1):
        self._ml = maxLen
        self.queue = deque()

    @property
    def maxLen(self) -> int:
        return self._ml

    @maxLen.setter
    def maxLen(self, value: int):
        if value > self._ml:
            self._ml = value

    def append(self, value: float):
        self.queue.appendleft(value)
        if len(self.queue) > self._ml:
            self.queue.pop()


class _LineIter:
    def __init__(self, queue: Deque[float], l: int):
        self.i = 0
        self.l = l
        self.q = iter(queue)

    def __next__(self) -> float:
        if self.i < self.l:
            self.i += 1
            return self.q.__next__()
        else:
            raise StopIteration


class Line:
    def __init__(self, neededLen: int, queue: LineDeque):
        self._neededLen = neededLen
        self.lq = queue

    def end(self) -> float:
        return self.lq.queue[0]

    def add(self, value: float):
        self.lq.append(value)

    def __iter__(self) -> _LineIter:
        return _LineIter(self.lq.queue, self._neededLen)

    def __call__(self) -> Optional[float]:
        try:
            return self.end()
        except IndexError:
            return None

class LineManager:
    def __init__(self):
        self._lowD = LineDeque()
        self._closeD = LineDeque()
        self._highD = LineDeque()
        self._volD = LineDeque()

        # Register input data lines
        self.lines: Dict[str, LineDeque] = {
            LOW: self._lowD,
            CLOSE: self._closeD,
            HIGH: self._highD,
            VOLUME: self._volD
        }

        self._registered: Set[str] = set(self.lines.keys())
        self._requested: Set[str] = set()

        # lineName -> indicator that registered name
        self.registers: Dict[str, str] = {}
        # Indicator name -> List of every request
        self.requests: Dict[str, List[str]] = {}

    def update(self, low: float, close: float, high: float, volume: float) -> None:
        # Update input lines
        self._lowD.append(low)
        self._closeD.append(close)
        self._highD.append(high)
        self._volD.append(volume)

    def errorCheck(self):
        # Make sure that every requested line has been registered
        diff = self._requested - self._registered
        if len(diff) > 0:
            raise IndicatorError(f"Unregistered lines requested: {diff}")

    def registerLine(self, myname: str, lineName: str) -> Line:
        m = _mangle(myname, lineName)
        if m in self._registered:
            raise IndicatorError(f'Attempting to register line twice: "{m}"')
        self._registered.add(m)

        self.registers[lineName] = myname

        d = self._getLine(m, 1)

        return Line(1, d)

    def requestLine(self, myname: str, indicatorName: str, lineName: str, memory: int) -> Line:
        m = _mangle(indicatorName, lineName)
        d = self._getLine(m, memory)

        self._requested.add(m)
        self.requests[myname].append(lineName)

        return Line(memory, d)

    def hlc(self, memory: int = 1) -> Tuple[Line, Line, Line]:
        return (
            Line(memory, self._highD),
            Line(memory, self._lowD),
            Line(memory, self._closeD)
        )

    def requestInput(self, name: str, memory: int = 1) -> Line:
        try:
            d = self.lines[name]
            d.maxLen = memory
        except KeyError:
            raise IndicatorError(f"Invalid input line name: {name}")

        return Line(memory, d)

    def _getLine(self, mangle: str, memory: int) -> LineDeque:

        try:
            # Try to find line
            d = self.lines[mangle]
            d.maxLen = memory
        except KeyError:
            # Else create new
            d = LineDeque(maxLen=memory)
            self.lines[mangle] = d

        return d


class Data:
    def __init__(self, lineName: str):
        self.lineName = lineName

    def requestLine(self, myname: str, lineManager: LineManager, memory: int = 1) -> Line:
        return lineManager.requestInput(self.lineName, memory)


class IndicData(Data):
    def __init__(self, indicName: str, lineName):
        super().__init__(lineName)
        self.indicName = indicName

    def requestLine(self, myname: str, lineManager: LineManager, memory: int = 1) -> Line:
        return lineManager.requestLine(myname, self.indicName, self.lineName, memory)
