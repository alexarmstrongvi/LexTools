import logging
from pathlib import Path
import time
from traceback import TracebackException
import sys

ROOT_LOG_CONFIGURED = False

# Format options
#LOG_FMT_DEFAULT ='%(levelname)8s :: %(message)s'
LOG_FMT_DEFAULT ='%(levelname)8s :: %(module)s :: %(message)s'
#LOG_FMT_DEFAULT = '%(levelname)8s :: (%(filename)s) %(message)s'
#LOG_FMT_DEFAULT ='%(levelname)8s :: [%(asctime)s] (%(filename)s) %(message)s'
#LOG_FMT_DEFAULT = "%(levelname)8s :: (%(module)s - %(funcName)s()) %(message)s"
#LOG_FMT_DEFAULT = "%(levelname)8s :: (%(module)s:%(funcName)s():L%(lineno)d) %(message)s"

def get_logger(name, lvl=None):
    global ROOT_LOG_CONFIGURED
    if not ROOT_LOG_CONFIGURED:
        formatter = logging.Formatter(LOG_FMT_DEFAULT)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(formatter)
        main_logger = logging.getLogger('__main__')
        main_logger.addHandler(handler)
        ROOT_LOG_CONFIGURED = True

    if name == '__main__':
        log = logging.getLogger(name)
        #capture_python_stdout(log)
    else:
        log = logging.getLogger(f'__main__.{name}')
        if lvl:
            log.setLevel(lvl)

    return log

def add_log_file(logger, path: Path = Path()) -> Path:
    formatter = logging.Formatter(LOG_FMT_DEFAULT)
    if path.is_dir():
        path = path / f'run_{time.strftime("%Y%m%d_%H%M%S_%Z")}.log'
    file_handler = logging.FileHandler(path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return path

def capture_python_stdout(root_log):
    def handle_exception(typ, val, tb):
        # Sources:
        # https://stackoverflow.com/questions/6234405/logging-uncaught-exceptions-in-python
        # https://stackoverflow.com/questions/8050775/using-pythons-logging-module-to-log-all-exceptions-and-errors
        if issubclass(typ, KeyboardInterrupt):
            # Don't capture keyboard interrupt
            sys.__excepthook__(typ, val, tb)
            return
        nonlocal root_log

        # Option 1 - trace in one log error message
        #root_log.exception("Uncaught exception", exc_info=(typ, val, tb))

        # Option 2 - trace split into one log error message per newline
        root_log.error("Uncaught exception")#, exc_info=(typ, val, tb))
        for lines in TracebackException(typ, val, tb).format():
            for line in lines.splitlines():
                root_log.error(line)

    sys.excepthook = handle_exception

    # Source: https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
    sys.stdout = LoggerWriter(root_log.info)
    sys.stderr = LoggerWriter(root_log.warning) # root_log.error?


class LoggerWriter(object):
    def __init__(self, writer):
        #self.encoding = sys.stdout.encoding # Getting issues with doctest
        self._writer = writer
        self._msg = ''

    def write(self, message):
        # Prevent carraige return and empty newlines
        msg = message.lstrip('\r').lstrip('\n')

        self._msg = self._msg + msg
        while '\n' in self._msg:
            pos = self._msg.find('\n')
            self._writer(self._msg[:pos])
            self._msg = self._msg[pos+1:]

    def flush(self):
        if self._msg != '':
            self._writer(self._msg)
            self._msg = ''


def log_multiline(log_call, txt):
    for line in txt.splitlines():
        log_call(line)

def log_summary_str(log):

    log_lvl = log.level
    eff_lvl = log.getEffectiveLevel()
    min_lvl = min([lvl for lvl  in range(logging.CRITICAL) if log.isEnabledFor(lvl)])

    s  = f'Log Summary - {log.name}'
    s += f'\n - Levels   : Effective = {eff_lvl}; Logger = {log_lvl}; Enabled for >={min_lvl}'
    s += f'\n - Flags    : Disabled = {log.disabled}'
    s += f', Propogate = {log.propagate}'
    s += f', Handlers = {log.hasHandlers()}'
    #if log.parent:
    #    s += f'\n - Parent : {log.parent.name}'
    for i, hndl in enumerate(log.handlers,1):
        s += f'\n - Handler {i}: {hndl}'
    for i, fltr in enumerate(log.filters,1):
        s += f'\n - Filter {i} : {fltr}'
    return s
