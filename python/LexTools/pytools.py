#!/bin/bash/env python
import math
from typing import List

################################################################################
# Integer tools
def ndigits(n : int) -> int:
    ''' Get number of digits in integer '''
    if type(n) != int:
        raise TypeError("Input value must be an integer")
    n = abs(n)
    
    # Option 1: One-liner
    # ndigits = len(str(n))

    # Option 2: Fast; No type conversion
    if n == 0:
        ndigits = 1
    else:
        ndigits = math.floor((math.log10(abs(n))))+1
        if n > 999999999999997: # correct floating point rounding error in log10 
            ndigits -= 1
    return ndigits


def pop_digit(n : int, from_left=False) -> int:
    ''' Pop off the last digit in an integer '''
    if type(n) != int:
        raise TypeError("Input value must be an integer")
    n, sign = abs(n), n//abs(n)

    # Edge cases
    if n < 10:
       return None, n 

    # Option 1: Fast; No type conversion
    if from_left:
        d, n = divmod(n, 10**(ndigits(n)-1))
    else:
        n, d = divmod(n, 10)
    
    # Option 2
    # s = str(n)
    # if from_left:
    #     n, d = int(s[1:]), int(s[0])
    # else:
    #     n, d = int(s[:-1]), int(s[-1])

    return sign*n, d

def split_int(n : int) -> List[int]:
    ''' Split integer into list of digits '''
    if type(n) != int:
        raise TypeError("Input value must be an integer")
    n = abs(n)

    # Option 1 : One liner
    l = [int(c) for c in str(n)]

    # Option 2 : No type conversion
    #l = []
    #while n:
    #    n, d = divmod(n, 10)
    #    l.append(d)
    #l = l[::-1]
    
    return l

def join_ints(l : List[int]) -> int:
    if not l:
        raise IndexError("Input list is empty") 
    n = 0
    for d in l:
        if type(d) != int or d < 0:
            raise TypeError("Input list must only contain unsigned integers")
        n = 10*n + d
    return n

def get_nth_digit(x : int, n : int, from_right=False) -> int:
    ''' Get the nth digit in an integer '''
    if type(x) != int or type(n) != int:
        raise TypeError("Input value must be an integer")
    if n < 0:
        raise IndexError("Cannot access index %s" % n)
    x = abs(x)


    # Option 1
    # s = str(x)[::-1] if from_right else str(x)
    # if n >= len(s):
    #     raise IndexError(f'Cannot access index {n} of {x}')
    # d = int(s[n])

    # Option 2 : No type conversion
    if 10**n > x:
        raise IndexError(f'Cannot access index {n} of {x}')
    divisor = 10**n if from_right else 10**(ndigits(x)-1-n)
    d = (x // divisor) % 10
    
    return d

################################################################################
# Context managers

################################################################################
# Environment checks

