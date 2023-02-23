
class Bar:
    def __init__(self, lo, close, hi, vol, date=None):
        self.lo = lo
        self.close = close
        self.hi = hi
        self.vol = vol
        self.date = date

    def __str__(self) -> str:
        return f"(L:{self.lo}, C:{self.close}, H:{self.hi}, V:{self.vol})"
