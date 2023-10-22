from types import ModuleType

def dirset(t):
    return {f for f in dir(t) if not f.startswith('_')}

def dircat(obj, ignore_obj = None, overlap_set = None):
    result = {
        'attribute' : [],
        'method'    : [],
        'function'  : [],
        'class'     : [],
        'module'    : [],
        'other'     : [],
        'missing'   : [],
        'crash'     : [],
    }
    xs = dirset(obj)
    if ignore_obj is not None:
        xs -= dirset(ignore_obj)
    if overlap_set is not None:
        xs = xs & overlap_set
    for x in xs:
        try:
            if not hasattr(obj, x):
                result['missing'].append(x)
                continue
            e = eval(f'obj.{x}')
        except (RuntimeError, AttributeError) as e:
            msg = ' '.join(e.args)
            result['crash'].append(x+' -> '+msg)
#             if 'eager execution' in msg or 'EAGER mode' in msg:
#                 result['lazy'].append(x) 
            continue

        s = str(e)
        if s.startswith(('<bound method', '<built-in method')):
            result['method'].append(x+'()')
        elif s.startswith(('<function', '<built-in function')):
            result['function'].append(x+'()')
        elif s.startswith('<class'):
            result['class'].append(x)
        elif isinstance(e, ModuleType):
            result['module'].append(x)
        elif s.startswith('<'):
            result['other'].append(x+' = '+s)
        else:
            result['attribute'].append(x+' = '+s)

    return {k : v for k,v in result.items() if len(v)>0}


if __name__ == '__main__':
    import requests
    result = dircat(requests)
    for k, v in result.items():
        print(k)
        for x in sorted(v):
            print('\t-',x)
