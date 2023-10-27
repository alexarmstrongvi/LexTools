#!/usr/bin/env python
'''
<TODO> Module docstring
'''
# Standard library
import configparser
import copy
import json
import logging
from pathlib import Path
try:
    import tomllib # Added in python 3.11
except ImportError:
    import tomli as tomllib # 3rd party
from typing import Iterable, Optional
import time
import shutil

# 3rd party
import yaml

# Local
import user_input

# Globals
log = logging.getLogger(__name__)

################################################################################
# NOTE: Projects are better off choosing a single configuration format so the
# read and save functions below are mostly a reference for how to read files in
# the various configuration libraries. Currently, I prefer YAML for configuring
# scripts though TOML is becoming popular.
def read_config(path: Path) -> dict:
    '''Read configuration file'''
    if path.suffix in ('.yaml', '.yml'):
        with path.open('r') as ifile:
            cfg = yaml.safe_load(ifile)
    elif path.suffix == '.json':
        with path.open('r') as ifile:
            cfg = json.load(ifile)
    elif path.suffix == '.ini':
        cfg = configparser.ConfigParser()
        cfg.read(path)
        # NOTE: This type conversion is not perfect so consider sticking with
        # ConfigParser if INI is the configuration file type for the project
        cfg = dict(cfg)
    elif path.suffix == '.toml':
        with path.open('rb') as ifile:
            cfg = tomllib.load(ifile)
    else:
        raise NotImplementedError(f'Unexpected file format: {path}')
    return cfg

def save_config(cfg: dict, path: Path) -> None:
    '''Save configuration settings'''
    if path.suffix in ('.yaml', '.yml'):
        with path.open('w') as ofile:
            yaml.safe_dump(cfg, ofile)
    elif path.suffix == '.json':
        with path.open('w') as ofile:
            json.dump(cfg, ofile)
    # NOTE: There is no standard way to convert a python dictionary to INI
    # or TOML format as they are more limited than JSON and YAML
    else:
        raise NotImplementedError(f'Unexpected file format: {path}')

def merge_config_files(
    cfgs: Iterable[dict], 
    default_cfg: Optional[dict] = None,
) -> dict:
    '''Merge configuration files with later ones overwriting earlier ones.

    Parameters
    ==========
    cfgs:
        Separate configurations to be merged
    default_cfg:
        Configuration with default values for all parameters

    Returns
    =======
    Single merged configuration file
    '''
    if default_cfg is not None:
        merged_cfg = copy.deepcopy(default_cfg)
        allow_new_keys = False
    else:
        merged_cfg = {}
        allow_new_keys = True

    for cfg_update in cfgs:
        update_config(
            original = merged_cfg, 
            update = cfg_update, 
            copy = False,
            allow_new_keys = allow_new_keys,
        )
    return merged_cfg

def update_config(
    original        : dict,
    update          : dict,
    copy            : bool = True,
    allow_new_keys  : bool = False,
    concat_lists    : bool = False,
    overwrite_lists : bool = False,
) -> dict:
    '''
    Update a configuration dictionary using a dictionary with updated values.

    The intended use case is combining common configuration formats (e.g. YAML,
    JSON, TOML) after being read into python dictionaries. Therefore, this
    function aims to handle the subset of python types these configuration
    formats support (e.g. int, float, str, dict, list). Other types (e.g. tuple,
    set, numpy array, bytes) are not handled in any special way and therefore
    will overwrite the original value similar to an int or float value.

    Parameters
    ==========
    original:
        Original configuration dictionary
    update:
        Configuration dictionary with values to update in the original
    copy:
        Apply updates to a copy of the original, returning a new dictionary
    allow_new_keys:
        Allow the update to contain keys not in the original
    concat_lists:
        Update lists by concatenating them, allowing duplicates
    overwrite_lists:
        Update lists by overwriting the original with the updated list

    Returns
    =======
    Updated configuration dictionary
    '''

    if copy:
        # Use shallow copy to reduce memory usage
        # This requires care be taken when updating mutable values below
        original = original.copy() 

    for key, val in update.items():
        if key not in original:
            if not allow_new_keys:
                raise KeyError(f'{key!r} not in original dictionary')
            original[key] = val
        elif isinstance(val, dict):
            if original[key] is None:
                original[key] = update_config({}, val, copy, allow_new_keys=True)
            else:
                original[key] = update_config(original[key], val, copy, allow_new_keys)
        elif isinstance(val, list):
            original_list = original[key] or []
            if overwrite_lists:
                original[key] = val
            elif concat_lists:
                original[key] = original_list + val
            else:
                # Append new elements, preserving order from both lists.
                # This will not handle duplicates already in the original or
                # update. It is assumed the user intends those duplicates.
                merged_list = original_list.copy()
                for x in val:
                    if x not in original_list:
                        merged_list.append(x)
                original[key] = merged_list
        else:
            original[key] = val
    
    return original

def require_empty_dir(
    path: Path,
    parents: bool = False,
    overwrite: bool = False,
) -> None:
    # Make directory if it doesn't exist or is empty
    if not path.is_dir():
        path.mkdir(parents=parents)
        return
    elif not any(path.iterdir()):
        return

    if not overwrite:
        # Check if user wants to delete contents of directory
        overwrite = user_input.request_permission(f'Delete contents of {path}?')

    files = list(path.rglob('*'))
    if overwrite:
        log.warning('Deleting all %d files from %s', len(files), path)
        time.sleep(2) # Give the user a moment to realize if this was a mistake
        shutil.rmtree(path)
        path.mkdir(parents=parents)
    else:
        raise FileExistsError(
            f'{len(files)} files found (e.g. {files[0].name}): {path}'
        )

################################################################################
# NOTE: Move the unit tests below into a tests directory when adding this
# function to a project.
import pytest
def test_update_config():

    # Value update 
    original = {'A' : 1, 'B' : 2}
    update   = {'A' : 9}
    result   = {'A' : 9, 'B' : 2}
    assert update_config(original, update) == result
    
    # Original input not mutated by default but copying can be disabled
    original = {'A' : 1, 'B' : 2}
    update   = {'A' : 2}
    original_deepcopy = copy.deepcopy(original)
    combined = update_config(original, update)
    assert original == original_deepcopy
    assert original is not combined
    combined = update_config(original, update, copy=False)
    assert original != original_deepcopy
    assert original is combined
    
    # Sub-dictionary update 
    original = {
        'A' : 1,
        'B' : {'X' : 2, 'Y' : 3},
    }
    update = {
        'B' : {'X' : 9},
    }
    result = {
        'A' : 1,
        'B' : {'X' : 9, 'Y' : 3},
    }
    assert update_config(original, update) == result
    
    # Sub-list update 
    original = {'A' : [2,3]}
    update   = {'A' : [2,1]}
    # Append only new elements by default
    assert update_config(original, update)['A'] == [2,3,1]
    # Enable concatenation of lists, allowing for duplicates 
    assert update_config(original, update, concat_lists=True)['A'] == [2,3,2,1]
    # Enable simple overwriting of lists
    assert update_config(original, update, overwrite_lists=True)['A'] == [2,1]

    # New keys not allowed by default but can be explicitely allowed
    original = {'A' : 1}
    update   = {'Z' : 1}
    with pytest.raises(KeyError):
        update_config(original, update)
    update_config(original, update, allow_new_keys=True)

    # Edge cases
    config = {'A' : 1}
    assert update_config(config, {}) == config
    assert update_config({}, config, allow_new_keys=True) == config
    config = {'A' : None}
    update = {'A' : {'X' : 1}}
    assert update_config(config, update) == update
    config = {'A' : None}
    update = {'A' : [1,2]}
    assert update_config(config, update) == update

def test_require_empty_dir(monkeypatch):
    empty_dir = Path('path_to/empty_dir')

    assert not empty_dir.parent.is_dir()

    # Error if parent directory does not exist by default
    with pytest.raises(FileNotFoundError):
        require_empty_dir(empty_dir)
    require_empty_dir(empty_dir, parents=True)
    assert empty_dir.is_dir()

    # Do nothing if directory exists but is empty
    require_empty_dir(empty_dir)
    assert empty_dir.is_dir()

    # Error if directory exists and is not empty
    (empty_dir/'file.txt').write_text('TEST\n')
    with monkeypatch.context() as m:
        with pytest.raises(FileExistsError):
            m.setattr('user_input.request_permission', lambda _ : False)
            require_empty_dir(empty_dir)
        # User can choose to remove output directory
        m.setattr('user_input.request_permission', lambda _ : True)
        require_empty_dir(empty_dir)

    shutil.rmtree(empty_dir.parent)
