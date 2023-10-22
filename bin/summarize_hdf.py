#!/usr/bin/env python3
"""
================================================================================
Print structure of HDF5 file

Examples
    ./summarize_hdf5.py file.hdf5 > output.txt
================================================================================
"""
# Built-in
from datetime import datetime
import sys
import argparse
from pathlib import Path

# 3rd party
import h5py

tab = '    '

################################################################################
def main(args : argparse.ArgumentParser) -> None:
    with h5py.File(args.ifile_path, 'r') as ifile:
        print('Exploring', args.ifile_path)
        start = datetime.today()
        print_hdf5_group(ifile)
        time = datetime.today() - start
        time_str = str(time)
        print(f'Time to process: {time_str}')

def print_hdf5_group(grp, tabs=''):
    print(f'{tabs}- {grp.name}')
    n_datasets = n_datatypes = 0
    if len(grp.attrs):
        print_attributes(grp, tabs=tabs+tab)
    for key, obj in grp.items():
        if isinstance(obj, h5py._hl.group.Group):
            print_hdf5_group(obj, tabs=tabs+tab)
        elif isinstance(obj, h5py._hl.dataset.Dataset):
            n_datasets += 1
            #if obj.dtype is None:
            #    dtype_str = '[NO TYPE]'
            if obj.dtype.names is None:
                dtype_str = f'[{obj.dtype}]'
            else:
                dtype_str = ''
            print(f'{tabs}{tab}- Dataset {n_datasets:>3}) {key} {obj.shape} {dtype_str}')
            if len(obj.attrs):
                print_attributes(obj, tabs=tabs+2*tab)
            if obj.dtype.names:
                for name in obj.dtype.names:
                    t = obj.dtype[name]
                    if t.names is None:
                        t = str(t)
                        print(f'{tabs}{tab*2}- {name} [{t}]')
                    else:
                        print(f'{tabs}{tab*2}- {name} ')
                        for name2 in t.names:
                            t2 = str(t[name2])
                            print(f'{tabs}{tab*3}- {name2} [{t2}]')
        elif isinstance(obj, h5py._hl.datatype.Datatype):
            n_datatypes += 1
            print(f'{tabs}{tab}- Datatype {n_datatypes:>3}) {key}')
        else:
            print(f'{tabs}{tab}- Unkonwn Type:', type(obj))

def print_attributes(obj, tabs=''):
    print(f'{tabs}- Attributes')
    for key, val in obj.attrs.items():
        print(f'{tabs}{tab}- {key} : {val} ')
################################################################################
# Argument parsing
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('ifile_path',
                        type=Path,
                        help='Input HDF5 file')
    args = parser.parse_args()
    return args

def check_inputs(args : argparse.ArgumentParser):
    """Check the input arguments are as expected"""
    if not args.ifile_path.is_file():
        print(f"ERROR :: Cannot find input file: {args.ifile_path}")
        sys.exit()

################################################################################
if __name__ == '__main__':
    args = get_args()
    check_inputs(args)
    main(args)
