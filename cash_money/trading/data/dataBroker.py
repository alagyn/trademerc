from datetime import datetime
from typing import Dict, List, Optional

from cash_money.trading.objects import Bar

BarDict = Dict[str, List[Optional[Bar]]]


class DataBroker:

    def getBars(self, symbols: list[str], startDate: datetime, endDate: datetime) -> BarDict:
        raise NotImplementedError()
