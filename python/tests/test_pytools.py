''' Unit testing of pytools.py '''
import pytest
import LexTools as tools

def test_ndigits():
    ''' Unit tests for ndigits '''
    assert tools.ndigits(1234) == 4
    assert tools.ndigits(-12) == 2
    assert tools.ndigits(999999999999997) == 15
    assert tools.ndigits(999999999999998) == 15
    assert tools.ndigits(10**10000 - 1) == 10000
    with pytest.raises(TypeError):
        tools.ndigits('1234')
    with pytest.raises(TypeError):
        tools.ndigits(0.33)

def test_pop_digit():
    ''' Unit tests for pop_digit '''
    assert tools.pop_digit(1234)  == (123, 4)
    assert tools.pop_digit(-1234) == (-123, 4)
    assert tools.pop_digit(1)     == (None, 1)
    assert tools.pop_digit(-1)    == (None, 1)
    assert tools.pop_digit(1234,  from_left=True) == (234, 1)
    assert tools.pop_digit(-1234, from_left=True) == (-234, 1)
    assert tools.pop_digit(10**10000 - 1) == (10**9999 - 1, 9)
    with pytest.raises(TypeError):
        tools.pop_digit(None)
    with pytest.raises(TypeError):
        tools.pop_digit('1234')
    with pytest.raises(TypeError):
        tools.pop_digit(0.33)

def test_split_int():
    ''' Unit tests for split_int '''
    assert tools.split_int(1234)  == [1,2,3,4]
    assert tools.split_int(1)     == [1]
    assert tools.split_int(-1234) == [1,2,3,4]
    assert tools.split_int(10**10000 - 1) == [9]*10000
    with pytest.raises(TypeError):
        tools.split_int('1234')
    with pytest.raises(TypeError):
        tools.split_int(0.33)

def test_join_ints():
    ''' Unit tests for join_ints '''
    assert tools.join_ints([1,2,3,4]) == 1234
    assert tools.join_ints([1]) == 1
    assert tools.join_ints([9]*10000) == 10**10000 - 1
    with pytest.raises(IndexError):
        tools.join_ints([])
    with pytest.raises(TypeError):
        tools.join_ints([1,'2',3])
    with pytest.raises(TypeError):
        tools.join_ints([1,-2,3])

def test_get_nth_digit():
    ''' Unit tests for get_nth_digit '''
    assert tools.get_nth_digit(1234,  0) == 1
    assert tools.get_nth_digit(1234,  2) == 3
    assert tools.get_nth_digit(1,     0) == 1
    assert tools.get_nth_digit(-1234, 0) == 1
    assert tools.get_nth_digit(1234, 0, from_right=True) == 4
    assert tools.get_nth_digit(1234, 2, from_right=True) == 2
    assert tools.get_nth_digit(10**10000 - 1,1) == 9
    with pytest.raises(TypeError):
        assert tools.get_nth_digit('1234', 0)
    with pytest.raises(TypeError):
        assert tools.get_nth_digit(0.33, 0)
    with pytest.raises(IndexError):
        assert tools.get_nth_digit(1234, 99)
