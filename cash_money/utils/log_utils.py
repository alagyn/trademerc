import logging
import time
import os
import sys
from cash_money.consts import ROOT_LOGGER

_ERR_C = '\033[91m'
_DBG_C = '\033[92m'
_WRN_C = "\033[93m"
_END_C = '\033[0m'

_DFLT = '%(levelname)5s:%(message)s'
_FILE_FMT = logging.Formatter(f'%(asctime)s {_DFLT}',
                              datefmt='%b-%d %H:%M:%S')

_DFLT_LOG_FMT = logging.Formatter(_DFLT)
_ERR_LOG_FMT = logging.Formatter(f'{_ERR_C}{_DFLT}{_END_C}')
_DBG_LOG_FMT = logging.Formatter(f'{_DBG_C}{_DFLT}{_END_C}')
_WRN_LOG_FMT = logging.Formatter(f"{_WRN_C}{_DFLT}{_END_C}")

class _ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.levelno == logging.DEBUG:
            return _ERR_LOG_FMT.format(record)
        elif record.levelno == logging.WARNING:
            return _WRN_LOG_FMT.format(record)
        elif record.levelno == logging.ERROR:
            return _ERR_LOG_FMT.format(record)
        else:
            return _DFLT_LOG_FMT.format(record)


_logger = logging.getLogger(ROOT_LOGGER)

def _setupLogger(debug: bool, logToFile: bool, logDir: str):

    _logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if logToFile:
        logname = time.strftime(r'%Y_%b_%dT%H_%M_%S')

        os.makedirs(logDir, exist_ok=True)

        # Terminal Log File
        filehandler = logging.FileHandler(
            filename=f'{logDir}/{logname}.log',
            mode='w'
        )
        filehandler.setLevel(level = logging.DEBUG if debug else logging.INFO)
        filehandler.setFormatter(_FILE_FMT)
        _logger.addHandler(filehandler)

    console1 = logging.StreamHandler(sys.stdout)
    console1.setLevel(logging.DEBUG if debug else logging.INFO)
    console1.setFormatter(_ConsoleFormatter())
    _logger.addHandler(console1)

    _logger.debug("Setup logging")

class CMLogger:
    def __init__(self, module: str):
        self.module = module

    def _log(self, level, msg):
        _logger.log(level, f'{self.module:^15s}: {msg}')

    def logWrn(self, msg):
        self._log(logging.WARNING, msg)

    def logInfo(self, msg):
        self._log(logging.INFO, msg)

    def logDbg(self, msg):
        self._log(logging.DEBUG, msg)

    def logErr(self, msg):
        self._log(logging.ERROR, msg)