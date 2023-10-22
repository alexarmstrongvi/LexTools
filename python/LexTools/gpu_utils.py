'''
Tools for getting information about GPUs

nvidia-smi docs: https://developer.nvidia.com/nvidia-system-management-interface
'''
import subprocess
import os
from datetime import datetime

# Global configuration
GPU_ATTRS = [
    'name', # official product name
    'timestamp', # When the query was made
    'index',
    'uuid', # globally unique immutable alphanumeric identifier of the GPU
    'utilization.gpu',
    'utilization.memory',
    'memory.total',
    'memory.used',
    'memory.free',
    'temperature.gpu',
    'power.draw',
    'power.limit',
    'pstate', # Performance state. P0 (max performance) to P12 (min performance)
]

FLOAT_ATTRS = [
    'utilization.gpu',
    'utilization.memory',
    'memory.total',
    'memory.used',
    'memory.free',
    'power.draw',
    'power.limit',
    'temperature.gpu',
]

def get_gpus():
    '''Get current GPU attributes for all accessible GPUs'''
    cmd = ['nvidia-smi',
           '--query-gpu=' + ','.join(GPU_ATTRS),
           '--format=csv,noheader,nounits',
    ]
    subproc   = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    stdout, _ = subproc.communicate()
    output    = stdout.decode('UTF-8')
    lines     = output.split(os.linesep)
    gpus      = [parse_gpu_output(line) for line in lines if line.strip()]
    gpus      = sorted(gpus, key=lambda gpu : gpu['index'])
    return gpus

def parse_gpu_output(line):
    '''Parse the output for a single GPU from nvidia-smi'''
    gpu = dict(zip(GPU_ATTRS, line.strip().split(', ')))
    gpu = transform(gpu)
    # Add metrics
    gpu['utilization.power']     = round(100 * gpu['power.draw']  / gpu['power.limit'])
    gpu['utilization.fb_memory'] = round(100 * gpu['memory.used'] / gpu['memory.total'])
    return gpu

def transform(gpus):
    '''Transform specific values to desired data type'''
    for key, val in gpus.items():
        if key == 'index':
            gpus[key] = int(val)
        elif key == 'pstate':
            gpus[key] = int(val[1:])
        elif key == 'timestamp':
            gpus[key] = datetime.strptime(val, '%Y/%m/%d %H:%M:%S.%f')
        elif key in FLOAT_ATTRS:
            gpus[key] = float(val)
    return gpus

if __name__ == '__main__':
    from pprint import pprint
    pprint(get_gpus())
