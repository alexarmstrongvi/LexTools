import re

def strip_ansi_escape(string):
    ''' Strip ANSI escape sequences from string '''
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', string)

def grep(pattern, string, mode=0b0):
    matches = [m.group() for m in re.finditer(pattern, string, mode)]

    # Correct for patterns that match zero-lenth strings (e.g. '.*', '.?')
    if len(matches) > 0 and not matches[0]:
        # e.g. ['','a','','b',''] -> ['']
        del matches[0]
    if len(matches) > 1 and not matches[-1]:
        # e.g. ['a','b',''] -> ['a','b']
        del matches[-1]


    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        return matches
    else:
        return None

def to_ordinal(n) -> str:
    """
    Converts integer (or their string
    representations) to an ordinal value.
    """
    if isinstance(n, str):
        if n.isdigit():
            n = int(n)
        else:
            raise ValueError('Input string cannot be converted to an integer')
    elif not isinstance(n, int):
        raise TypeError("Input value must be an integer or string")
    
    last_digit = abs(n) % 10
    if last_digit == 1 and n % 100 != 11:
        ordval = "%d%s" % (n, "st")
    elif last_digit == 2 and n % 100 != 12:
        ordval = "%d%s" % (n, "nd")
    elif last_digit == 3 and n % 100 != 13:
        ordval = "%d%s" % (n, "rd")
    else:
        ordval = "%d%s" % (n, "th")

    return ordval