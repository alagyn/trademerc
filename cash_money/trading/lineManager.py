class LineManager:

    def __init__(self) -> None:
        # only one value per key per step
        self.lines: dict[str, float] = {}

    def postValue(self, key: str, value: float) -> None:
        self.lines[key] = value

    def clear(self):
        self.lines.clear()
