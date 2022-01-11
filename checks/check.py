
class Check:
    """
    Base Class for checks that look at indicators
    """
    def check(self) -> bool:
        """Returns the current check without changing any state"""
        raise NotImplementedError

    def update(self) -> bool:
        """Returns the current check, possibly changing state"""
        raise NotImplementedError

    @classmethod
    def factory(cls, valFuncs, checks, args):
        raise NotImplementedError