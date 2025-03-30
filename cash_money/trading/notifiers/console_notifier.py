from ..events import CMEventListener, Notification, EndOfTradeStepEvent
from .plain_text_notifier import PlainTextFormatter
import logging

log = logging.getLogger("Notify")


class ConsoleNotifier(PlainTextFormatter):

    def __init__(self) -> None:
        super().__init__()

    def write(self, lines: list[str]) -> None:
        log.info("\n\t".join(lines))
