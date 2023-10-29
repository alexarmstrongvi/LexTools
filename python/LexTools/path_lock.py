# Standard library
from contextlib import contextmanager
from pathlib import Path
import collections.abc as CT
from datetime import datetime, timedelta
import psutil
import time
import logging
import os
import typing as T
import pprint

# 3rd party
import yaml

# Globals
log = logging.getLogger(__name__)
DAYS = 24 * 60 * 60 # in seconds

@contextmanager
def path_lock(
    path: Path, 
    max_lock_time: float = 1 * DAYS,
    timeout: float = 0,
) -> CT.Generator[T.Optional[dict], None, None]:
    '''
    Attempt to acquire a lock on a path that will prevent other processes using
    path_lock() from accessing that path at the same time.

    Simple use case:
    ```
    with path_lock(Path(), max_lock_time=10) as acquired_lock:
        if acquired_lock:
            ...
        else:
            ...
    ```
    It is not required that the path exist to acquire a lock. 

    This is designed to work with a few dozen processes acquiring and releasing
    the lock at most every few seconds and may not scale beyond that.

    Parameters
    ==========
    path:
        file or directory one wants a lock for
    max_lock_time:
        Maximum time (sec) the lock can be acquired for, after which time other
        processes will consider the lock expired
    timeout:
        Seconds to wait to aquire path lock
    '''
    lock = path.parent / (path.name + '_PATH_LOCK.yml')
    lock_aquired = not lock.exists()
    lock_info = None
    if not lock_aquired:
        with lock.open('r') as ifile:
            lock_info = yaml.safe_load(ifile)
        start = time.perf_counter()
        sleep_time = min(1, timeout/4)
        lock_info_str = pprint.pformat(lock_info, indent=4, sort_dicts=False)
        while time.perf_counter()-start < timeout and lock_in_use(lock_info):
            # log.debug(
            #     'Waiting for lock to release: %s\n%s', path, lock_info_str
            # )
            time.sleep(sleep_time)
        if not lock_in_use(lock_info):
            lock_aquired = True
        else:
            if timeout > 0:
                log.debug('Timed out waiting for path lock')
            log.debug('Path locked: %s\n%s', path, lock_info_str)
    if lock_aquired:
        lock_info = create_lock_info(lock, path, max_lock_time)
        # log.debug('Creating lock: %s', lock)
        with lock.open('w') as ofile:
            yaml.safe_dump(lock_info, ofile)
    try:
        yield lock_info if lock_aquired else None
    finally:
        if lock_aquired:
            try:
                # log.debug('Deleting lock: %s', lock)
                os.remove(lock)
            except FileNotFoundError:
                log.warning('Lock already deleted: %s', lock)
                pass
        # else:
        #     log.debug('No lock to cleanup')
def create_lock_info(lock: Path, path: Path, max_lock_time: float) -> dict:
    return {
        'lock_path'   : str(lock.resolve()),
        'path'        : str(path.resolve()),
        'user'        : os.getenv('USER'),
        'pid'         : os.getpid(),
        'expire_time' : datetime.now() + timedelta(seconds=max_lock_time),
    }

def lock_in_use(lock_info: dict) -> bool:
    try:
        return (
            psutil.pid_exists(lock_info['pid'])
            and
            datetime.now() < lock_info['expire_time']
        )
    except KeyError:
        # Either an old format or perhaps file created by other user with same
        # naming convention on accident
        log.error('Lock info missing keys: keys = %s', lock_info.keys())
    return False

################################################################################
# PyTests to be moved into tests/ if added to project
import multiprocessing

def test_path_lock():
    opath = Path('test_output_dir')
    with path_lock(opath, max_lock_time=0.1) as aquired_lock:
        assert aquired_lock is not None
        with path_lock(opath) as aquired_lock_again:
            assert aquired_lock_again is None
        with path_lock(opath, timeout=0.2) as aquired_lock_again:
            assert aquired_lock_again is not None

def test_path_lock_timeout():
    n_procs = multiprocessing.cpu_count()
    timeouts = [2] * n_procs
    with multiprocessing.Pool(processes=n_procs) as pool:
        results = pool.map(timeout_test, timeouts)
        pprint.pprint(results)
        assert sum(results) == n_procs

def timeout_test(timeout: float) -> bool:
    opath = Path('test_output_dir')
    # TODO: Sometimes running into issues if processes all try to acquire pathlock
    # immediately. Not sure where the race condition issue 
    time.sleep(os.getpid()%10/100) 
    with path_lock(opath, timeout=timeout) as acquired_lock:
        return bool(acquired_lock)

