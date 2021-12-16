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
