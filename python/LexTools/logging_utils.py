# Standard library
from pathlib import Path
from traceback import TracebackException
from typing import Optional
import logging
import logging.config
import re
import sys

# Local
import git

# Globals
log = logging.getLogger(__name__)

################################################################################
# Configuration

# Format options
#LOG_FMT_DEFAULT ='%(levelname)8s | %(message)s'
#LOG_FMT_DEFAULT ='%(levelname)8s | %(module)s :: %(message)s'
#LOG_FMT_DEFAULT ='%(levelname)8s | %(name)s :: %(message)s'
LOG_FMT_DEFAULT ='%(levelname)8s | %(name_last)s :: %(message)s'
#LOG_FMT_DEFAULT ='[%(asctime)s] %(levelname)8s | (%(filename)s) %(message)s'
#LOG_FMT_DEFAULT = "%(levelname)8s | (%(module)s:%(funcName)s():L%(lineno)d) %(message)s"

def configure_logging(
    output_dir: Optional[Path] = None,
    fileConfig: Optional[Path] = None,
    dictConfig: Optional[dict] = None, 
    **basicConfig,
) -> None:
    # Update log files to be within output dir
    if output_dir is not None:
        if basicConfig.get('filename'):
            basicConfig['filename'] = str(output_dir/basicConfig['filename'])
        if dictConfig is not None:
            for hcfg in dictConfig.get('handlers',{}).values():
                if hcfg.get('filename') is not None:
                    hcfg['filename'] = str(output_dir/hcfg['filename'])

    if len(basicConfig) > 0:
        logging.basicConfig(**basicConfig)

    if fileConfig is not None:
        logging.config.fileConfig(fileConfig)
    
    if dictConfig is not None:
        logging.config.dictConfig(**dictConfig)
    
    n_args = sum(map(bool, (fileConfig, dictConfig, basicConfig)))
    if n_args > 1:
        log.warning(
            '%d logging configurations provided. '
            'Order called: basicConfig -> fileConfig -> dictConfig'
            , n_args
        )
    
    redirect_exceptions_to_logger()
    # Use at your own risk. See function docstring for warnings
    #capture_python_stdout()
    
################################################################################
def level_name(level: int) -> str:
    name = ''
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
    elif level == 0:
        name = 'NOTSET'
    sublevel = level % 10
    if sublevel:
        name += f'+{sublevel}'
    return name

def all_logger_names() -> [str]:
    return ['root'] + sorted(logging.root.manager.loggerDict)

def logging_hierarchy_str():
    ostr = ''
    for name in all_logger_names():
        if name == 'root':
            name_last = name
            depth = 0
        else:
            parts = name.split('.')
            name_last = parts[-1]
            depth = len(parts)
        tabs = ' ' * 4 * depth
        logger = logging.getLogger(name)
        lvl_name = level_name(logger.level)
        n_handlers = len(logger.handlers)
        propagate = logger.propagate
        if (lvl_name, n_handlers, propagate) == ('NOTSET', 0, True):
            attr_str = ''
        else:
            attr_str = f' [{lvl_name}; {n_handlers} handler(s); {propagate = }]'
        prefix = '' if name == 'root' else f'{tabs}- '
        ostr += f'{prefix}{name_last!r}{attr_str}\n'
    return ostr

def log_summary_str(logger):
    log_lvl = logger.level
    eff_lvl = logger.getEffectiveLevel()
    min_lvl = min([lvl for lvl  in range(logging.CRITICAL+1) if logger.isEnabledFor(lvl)])

    s  = f'Log Summary - {logger.name}'
    s += f'\n - Levels   : Effective = {level_name(eff_lvl)}; Logger = {level_name(log_lvl)}; Enabled for >={level_name(min_lvl)}'
    s += f'\n - Flags    : Disabled = {logger.disabled}'
    s += f', Propagate = {logger.propagate}'
    s += f', Handlers = {logger.hasHandlers()}'
    #if logger.parent:
    #    s += f'\n - Parent : {logger.parent.name}'
    for i, hndl in enumerate(logger.handlers,1):
        s += f'\n - Handler {i}: {hndl}'
    for i, fltr in enumerate(logger.filters,1):
        s += f'\n - Filter {i} : {fltr}'
    return s

def log_multiline(log_call, txt):
    for line in txt.splitlines():
        log_call(line)

def summarize_logging() -> str:
    return logging_hierarchy_str() + '\n' + log_summary_str(logging.root)

def summarize_version_control() -> str:
    # TODO: Handle multiple version control systems
    # import version_control
    # if version_control.SYSTEM is not version_control.VCS.GIT:
    #     raise NotImplementedError

    ########################################
    # Git summary
    git_hash = git.get_hash()
    git_status = git.get_status()
    # Remove hints on how to use git from status
    lines = []
    for line in git_status.splitlines():
        line = re.sub(r'\(use "git.*\)','', line)
        if line.strip():
            lines.append(line.replace('\t',' '*4))
    git_status = '\n'.join(lines)
    summary = (
        f"Git Hash: {git_hash}"
        "\n"
        f"Git Status:\n{git_status}"
    )

    ########################################
    return summary

class RecordAttributeAdder(logging.Filter):
    '''Pseudo-Filter that adds useful attributes to log records for formatting'''
    def filter(self, record : logging.LogRecord):
        # Strip off parent logger names
        record.name_last = record.name.rsplit('.', 1)[-1]
        return True

def redirect_exceptions_to_logger(logger: logging.Logger = logging.root):
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

def capture_python_stdout(logger: logging.Logger = logging.root):
    '''Capture all stdout/stderr and send to logger

    NOTES/WARNINGS
    - This will capture messages from all non-child loggers, usually duplicating
      a lot of formatting (e.g. level, module, etc.)
    - This will not capture messages sent directly to terminal stdout/stderr
      instead of via the python streams (see capture_unix_df).
    '''
    stdout_log = logging.getLogger(f'{logger.name}.stdout')
    stderr_log = logging.getLogger(f'{logger.name}.stderr')

    # Overwrite python stdout and stderr streams
    # Source: https://stackoverflow.com/questions/19425736/how-to-redirect-stdout-and-stderr-to-logger-in-python
    sys.stdout = LoggerWriter(stdout_log.info)
    sys.stderr = LoggerWriter(stderr_log.warning) # stderr_log.error?

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

