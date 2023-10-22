import sys
from pathlib import Path
import yaml


def get_nested_dict(root, path):
    nested = root
    for i, p in enumerate(path.parts):
        if p not in nested:
            nested[p] = {}
        nested = nested[p]
    # nested[str(Path(*path.parts[-2:]))] = None
    return nested

paths = {}
ipath = Path(sys.argv[1])
with ipath.open() as ifile:
    for line in ifile:
        if 'Permission denied' in line or 'basename' in line:
            print('Skipping: ', line.strip())
            continue
        path = Path(line.strip())
        nested_dict = get_nested_dict(paths, path)

def remove_singleton_entries(dict_, key = None):
    keys = (key,) if key is not None else tuple(dict_.keys())
    # print(f'TESTING A ::', keys)
    for k in keys:
        # print(f'TESTING B ::\t', k)
        if dict_[k] == {}:
            dict_[k] = None
            # print(f'TESTING C ::\tSkipping')
            continue
        elif len(dict_[k]) == 1:
            # print(f'TESTING C ::\tCollapsing')
            sub_key = tuple(dict_[k].keys())[0]
            new_key = str(Path(k, sub_key))
            dict_[new_key] = dict_[k][sub_key]
            del dict_[k]
            if dict_[new_key] is not None:
                remove_singleton_entries(dict_, new_key)
        else:
            # print(f'TESTING C ::\tGoing deeper')
            remove_singleton_entries(dict_[k])

remove_singleton_entries(paths)

opath = ipath.parent / f'{ipath.stem}_bullet_list.yaml'
with opath.open('w') as ofile:
    yaml.dump(paths, ofile, indent=4)
print('Path bullet list saved:', opath)

