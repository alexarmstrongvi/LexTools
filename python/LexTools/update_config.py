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
            original[key] = update_config(original[key], val, copy, allow_new_keys)
        elif isinstance(val, list):
            if overwrite_lists:
                original[key] = val
            elif concat_lists:
                original[key] = original[key] + val
            else:
                # Append new elements, preserving order from both lists.
                # This will not handle duplicates already in the original or
                # update. It is assumed the user intends those duplicates.
                merged_list = original[key].copy()
                for x in val:
                    if x not in original[key]:
                        merged_list.append(x)
                original[key] = merged_list
        else:
            original[key] = val
    
    return original

if __name__ == '__main__':
    # NOTE: Move the unit tests below into a tests directory when adding this
    # function to a project.
    import pytest
    from copy import deepcopy

    # Value update 
    original = {'A' : 1, 'B' : 2}
    update   = {'A' : 9}
    result   = {'A' : 9, 'B' : 2}
    assert update_config(original, update) == result
    
    # Original input not mutated by default but copying can be disabled
    original = {'A' : 1, 'B' : 2}
    update   = {'A' : 2}
    original_deepcopy = deepcopy(original)
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

    print('Passed tests')
