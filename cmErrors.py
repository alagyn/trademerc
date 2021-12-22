class IndicatorError(Exception):
    def __init__(self, msg=''):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg


class CheckError(Exception):
    def __init__(self, msg=''):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg


class NotSetupError(CheckError):
    def __init__(self):
        super(NotSetupError, self).__init__('Check indicator returned None, not enough setup days')


class ActionError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class StrategyError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class JSONStrategyMissingVal(StrategyError):
    def __init__(self, path):
        super().__init__(f'Missing Strategy Variable: {path}')


class JSONStrategyInvalidType(StrategyError):
    def __init__(self, path, expected, actual):
        super().__init__(f"Invalid strategy datatype: Path: {path}, Expected: {expected}, Actual: {actual}")
