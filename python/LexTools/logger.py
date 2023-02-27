import logging
from pathlib import Path
import time
from traceback import TracebackException
import sys
from typing import Union

################################################################################
# Configuration

# Name for project's top level logger
PROJECT_LOGGER_NAME = 'LOG'

# Format options
#LOG_FMT_DEFAULT ='%(levelname)8s | %(message)s'
#LOG_FMT_DEFAULT ='%(levelname)8s | %(module)10s :: %(message)s'
#LOG_FMT_DEFAULT ='%(levelname)8s | %(name)s :: %(message)s'
LOG_FMT_DEFAULT ='%(levelname)8s | %(name_last)s :: %(message)s'
#LOG_FMT_DEFAULT = '%(levelname)8s | (%(filename)s) %(message)s'
#LOG_FMT_DEFAULT ='%(levelname)8s | [%(asctime)s] (%(filename)s) %(message)s'
#LOG_FMT_DEFAULT = "%(levelname)8s | (%(module)s - %(funcName)s()) %(message)s"
#LOG_FMT_DEFAULT = "%(levelname)8s | (%(module)s:%(funcName)s():L%(lineno)d) %(message)s"

# Disable propogation to root logger so project loggers are isolated (e.g.
# messages do not get processed by root logger handlers and logger attributes
# like hasHandlers are not effected by root logger)
logging.getLogger(PROJECT_LOGGER_NAME).propagate = False

def basic_config(level: Union[int,str] = None, log_path: Path = None):
    log = logging.getLogger(PROJECT_LOGGER_NAME)
    if log.hasHandlers():
        log.warning('Project logger already configured: %s', PROJECT_LOGGER_NAME)
        return
    formatter = logging.Formatter(LOG_FMT_DEFAULT)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RecordAttributeAdder())
    log.addHandler(handler)
    if level:
        if isinstance(level, int):
            pass
        elif level.isdigit():
            level = int(level)
        else:
            level = level.upper()
        log.setLevel(level)
    if log_path:
        add_log_file(log, log_path)
    redirect_exceptions_to_logger(log)
    # Use at your own risk. See function docstring for warnings
    #capture_python_stdout(log)

################################################################################
def get_logger(name: str = None, level : Union[str, int] = None):
    if not name or name == '__main__':
        log = logging.getLogger(PROJECT_LOGGER_NAME)
    else:
        # Make all loggers a child of the top level project logger
        log = logging.getLogger(f'{PROJECT_LOGGER_NAME}.{name}')
    if level is not None:
        log.setLevel(level)

    return log

################################################################################
# General logging utilities
def level_name(level: int) -> str:
    if level >= 50:
        name = 'CRITICAL'
    elif level >= 40:
        name = 'ERROR'
    elif level >= 30:
        name = 'WARNING'
    elif level >= 20:
        name = 'INFO'
    elif level >= 10:
        name = 'DEBUG'
    elif level > 0:
        name = ''
    elif level == 0:
        name = 'NOTSET'
    sublevel = level % 10
    if sublevel:
        name += f'+{sublevel}'
    return name

def log_hierarchy_summary_str() -> str:
    ostr = 'Logger Hierarchy\n'
    for name in ['root'] + sorted(logging.root.manager.loggerDict):
        if name == 'root':
            name_last = name
            depth = 0
        else:
            parts = name.split('.')
            name_last = parts[-1]
            depth = len(parts)
        if depth > 1 and not name.startswith(PROJECT_LOGGER_NAME):
            continue
        tabs = '  ' * depth
        log = logging.getLogger(name)
        attr_str = f'lvl={level_name(log.level)}'
        attr_str += f'; n_handlers={len(log.handlers)}'
        attr_str += f'; propogate={log.propagate}'
        ostr += f'{tabs}- {name_last} [{attr_str}]\n'
    ostr += 'Logger Info\n'
    for name in ['root'] + sorted(logging.root.manager.loggerDict):
        log = logging.getLogger(name)
        ostr += log_summary_str(log) + '\n'
    return ostr

def log_summary_str(log):
    log_lvl = log.level
    eff_lvl = log.getEffectiveLevel()
    min_lvl = min([lvl for lvl  in range(logging.CRITICAL+1) if log.isEnabledFor(lvl)])

    s  = f'Log Summary - {log.name}'
    s += f'\n - Levels   : Effective = {level_name(eff_lvl)}; Logger = {level_name(log_lvl)}; Enabled for >={level_name(min_lvl)}'
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

def log_multiline(log_call, txt):
    for line in txt.splitlines():
        log_call(line)

################################################################################
# Configuration utilities
def add_log_file(logger, path: Path = Path('./')) -> Path:
    formatter = logging.Formatter(LOG_FMT_DEFAULT)
    if path.is_dir():
        path = path / f'run_{time.strftime("%Y%m%d_%H%M%S_%Z")}.log'
    logger.info("Adding log file: %s", path)
    file_handler = logging.FileHandler(path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return path

class RecordAttributeAdder(logging.Filter):
    '''Pseudo-Filter that adds useful attributes to log records for formatting'''
    def filter(self, record : logging.LogRecord):
        # Strip off parent logger names
        record.name_last = record.name.rsplit('.', 1)[-1]
        return True

def redirect_exceptions_to_logger(logger: logging.Logger):
    # Overwrite hook for processing exceptions
    # https://stackoverflow.com/questions/6234405/logging-uncaught-exceptions-in-python
    # https://stackoverflow.com/questions/8050775/using-pythons-logging-module-to-log-all-exceptions-and-errors
    def handle_exception(typ, val, tb):
        if issubclass(typ, KeyboardInterrupt):
            # Don't capture keyboard interrupt
            sys.__excepthook__(typ, val, tb)
            return
        nonlocal logger

        # Option 1 - trace in one log error message
        #logger.exception("Uncaught exception", exc_info=(typ, val, tb))

        # Option 2 - trace split into one log error message per newline
        logger.error("Uncaught exception")
        for lines in TracebackException(typ, val, tb).format():
            for line in lines.splitlines():
                logger.error(line)

    sys.excepthook = handle_exception

def capture_python_stdout(log):
    '''Capture all stdout/stderr and send to logger

    NOTES/WARNINGS
    - This will capture messages from all non-child loggers, usually duplicating
      a lot of formatting (e.g. level, module, etc.)
    - This will not capture messages sent directly to terminal stdout/stderr
      instead of via the python streams (see capture_unix_df).
    '''
    stdout_log = logging.getLogger(f'{log.name}.stdout')
    stderr_log = logging.getLogger(f'{log.name}.stderr')

    # Overwrite python stdout and stderr streams
    # Source: https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
    sys.stdout = LoggerWriter(stdout_log.info)
    sys.stderr = LoggerWriter(stderr_log.warning) # log.error?

class LoggerWriter(object):
    def __init__(self, writer):
        #self.encoding = sys.stdout.encoding # Getting issues with doctest
        self._writer = writer
        self._msg = ''

    def write(self, message):
        for line in message.rstrip().splitlines():
            self._writer(line.rstrip())
        ## Prevent carriage return and empty newlines
        #msg = message.lstrip('\r').lstrip('\n')

        #self._msg = self._msg + msg
        #while '\n' in self._msg:
        #    pos = self._msg.find('\n')
        #    self._writer(self._msg[:pos]+'\n')
        #    self._msg = self._msg[pos+1:]

    def flush(self):
        pass
        # if self._msg != '':
        #     self._writer(self._msg)
        #     self._msg = ''

def capture_unix_fd():
    # TODO: Currently doesn't work
    # Also risk of infinite pipe loop as python stdout gets redirected back
    # to logger that prints it to stdout
    # Source: https://stackoverflow.com/questions/616645/how-to-duplicate-sys-stdout-to-a-log-file
    import subprocess, os, sys

    tee = subprocess.Popen(["tee", "log.txt"], stdin=subprocess.PIPE)
    # Cause tee's stdin to get a copy of our stdin/stdout (as well as that
    # of any child processes we spawn)
    os.dup2(tee.stdin.fileno(), sys.stdout.fileno())
    os.dup2(tee.stdin.fileno(), sys.stderr.fileno())

    # The flush flag is needed to guarantee these lines are written before
    # the two spawned /bin/ls processes emit any output
    print("\nstdout", flush=True)
    print("stderr", file=sys.stderr, flush=True)

    # These child processes' stdin/stdout are
    os.spawnve("P_WAIT", "/bin/ls", ["/bin/ls"], {})
    os.execve("/bin/ls", ["/bin/ls"], os.environ)
