
class Check:
    """
    Base Class for checks that look at indicators
    """
    def check(self) -> bool:
        raise NotImplementedError

    @classmethod
    def factory(cls, valFuncs, checks, args):
        raise NotImplementedError