import logging
import time
import os
import sys
from cash_money.consts import ROOT_LOGGER

_ERR_C = '\033[91m'
_DBG_C = '\033[92m'
_END_C = '\033[0m'

_F_LOG_FMT = '%(asctime)s %(levelname)s:%(message)s'

_C_DFLT = '%(levelname)5s:%(message)s'

_C_ERR_LOG_FMT = f'{_ERR_C}{_C_DFLT}{_END_C}'
_C_DBG_LOG_FMT = f'{_DBG_C}{_C_DFLT}{_END_C}'
_C_LOG_FMT = _C_DFLT

def _consoleInfofilter(record: logging.LogRecord) -> bool:
    """Filter to just show info messages"""
    return record.levelno == logging.INFO

def _consoleDebugFilter(record: logging.LogRecord) -> bool:
    """Filter to just show info messages"""
    return record.levelno == logging.DEBUG

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
        ff = logging.Formatter(fmt=_F_LOG_FMT,
                               datefmt='%b-%d %H:%M:%S')
        filehandler.setFormatter(ff)
        _logger.addHandler(filehandler)

    # logger that only shows info messages
    console1 = logging.StreamHandler(sys.stdout)
    console1.setLevel(logging.INFO)
    formatter = logging.Formatter(_C_LOG_FMT)
    console1.setFormatter(formatter)
    console1.addFilter(_consoleInfofilter)
    _logger.addHandler(console1)

    # logger that shows error and above
    console2 = logging.StreamHandler(sys.stdout)
    console2.setLevel(logging.WARNING)
    formatter = logging.Formatter(_C_ERR_LOG_FMT)
    console2.setFormatter(formatter)
    _logger.addHandler(console2)

    if debug:
        console3 = logging.StreamHandler(sys.stdout)
        console3.setLevel(logging.DEBUG)
        formatter = logging.Formatter(_C_DBG_LOG_FMT)
        console3.setFormatter(formatter)
        console3.addFilter(_consoleDebugFilter)
        _logger.addHandler(console3)

    _logger.debug("Setup logging")

def _log(level, module, msg):
    _logger.log(level, f'{module:^15s}: {msg}')

def logInfo(module, msg):
    _log(logging.INFO, module, msg)

def logDbg(module, msg):
    _log(logging.DEBUG, module, msg)

def logErr(module, msg):
    _log(logging.ERROR, module, msg)