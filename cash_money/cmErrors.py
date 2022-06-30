class CMError(Exception):
    def __init__(self, msg=''):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg

class StatError(CMError):
    def __init__(self, msg):
        super(StatError, self).__init__(msg)

class IndicatorError(CMError):
    def __init__(self, msg=''):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg

class IndicatorDependError(IndicatorError):
    def __init__(self, name: str):
        super(IndicatorDependError, self).__init__()
        self.msg = f"Indicator Dependency not calculated: {name}"

class IndicatorCircleDependError(IndicatorError):
    def __init__(self, indicList):
        super(IndicatorCircleDependError, self).__init__()
        self.msg = f'Circular Indicator Dependency detected: {[x.name for x in indicList]}'

class CheckError(CMError):
    def __init__(self, msg=''):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg


class NotSetupError(CheckError):
    def __init__(self):
        super(NotSetupError, self).__init__('Check indicator returned None, not enough setup days')


class ActionError(CMError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class StrategyError(CMError):
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


class BacktestError(StrategyError):
    def __init__(self, msg):
        super(BacktestError, self).__init__(msg)
