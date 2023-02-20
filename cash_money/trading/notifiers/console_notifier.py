from .notifier import Notifier
from cash_money.utils.log_utils import CMLogger

log = CMLogger("Notify")


class ConsoleNotifier(Notifier):
    def update(self, portfolio_start, portfolio_cur,
               portfolio_pl, trades, positions):
        log.logInfo(f'Port Start: ${portfolio_start}')
        log.logInfo(f'Port Cur: ${portfolio_cur}')
        log.logInfo(f'Port P/L: ${portfolio_pl}')

        msg = "Trades:"
        for x in trades:
            msg += f'\n\t{x}'

        log.logInfo(msg)

        msg = "Positions:"
        for x in positions:
            msg += f'\n\t{x}'

        log.logInfo(msg)
