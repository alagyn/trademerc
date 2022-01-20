from typing import List, Dict


class LogWrapper:
    def __init__(self):
        self._logs: Dict[str, List[float]] = {}

    def __getitem__(self, item: str) -> List[float]:
        return self._logs[item]

    def __setitem__(self, key: str, value: float):
        if key not in self._logs:
            self._logs[key] = []

        self._logs[key].append(value)

    def clear(self, key: str):
        self._logs[key] = []
