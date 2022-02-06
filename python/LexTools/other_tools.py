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

################################################################################
# Shell interaction
def get_cmd_output(cmd, print_output=False):
    """ Return output from shell command """
    x = randint(1,1000001)
    tmp_file_dump = 'tmp_shell_command_dump_%d.txt'%x
    if print_output:
        shell_cmd = '%s |& tee %s'%(cmd, tmp_file_dump)
    else:
        shell_cmd = '%s &> %s'%(cmd, tmp_file_dump)

    subprocess.call(shell_cmd, shell=True)
    output = []
    with open(tmp_file_dump,'r') as f:
        output = f.readlines()
    shell_cmd = 'rm %s'%tmp_file_dump
    subprocess.call(shell_cmd, shell=True)
    return output
