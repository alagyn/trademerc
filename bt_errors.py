class StrategyError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class StrategyMissingVal(StrategyError):
    def __init__(self, path):
        super().__init__(f'Missing Strategy Variable: {path}')


class StrategyInvalidType(StrategyError):
    def __init__(self, path, expected, actual):
        super().__init__(f"Invalid strategy datatype: Path: {path}, Expected: {expected}, Actual: {actual}")
