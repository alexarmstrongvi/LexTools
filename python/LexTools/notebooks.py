import subprocess
from random import randint
from contextlib import contextmanager

################################################################################
# Context managers
@contextmanager
def pd_display_all(*args, **kwargs):
    tmp1 = pd.get_option('display.max_rows')
    tmp2 = pd.get_option('display.max_colwidth')
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_colwidth', None)
    try:
        yield
    finally:
        pd.set_option('display.max_rows', tmp1)
        pd.set_option('display.max_colwidth', tmp2)
