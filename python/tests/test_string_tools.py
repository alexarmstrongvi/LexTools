import LexTools.string_tools as tools
import pytest

def test_strip_ansi_escape():
    ''' Unit tests for strip_ansi_escape '''
    test = 'ls\r\n\x1b[00m\x1b[01;31mexamplefile.zip\x1b[00m\r\n\x1b[01;31m'
    assert tools.strip_ansi_escape(test) == 'ls\r\nexamplefile.zip\r\n'

def test_extract_string():
    ''' Unit tests for extract_string '''
    assert tools.grep('this', 'Extract this') == 'this'
    assert tools.grep('t[a-z]*s', 'Extract this') == 'this'


def test_to_ordinal():
    ''' Unit tests for to_ordinal '''
    assert tools.to_ordinal(0)    == '0th'
    assert tools.to_ordinal(1)    == '1st'
    assert tools.to_ordinal(2)    == '2nd'
    assert tools.to_ordinal(3)    == '3rd'
    assert tools.to_ordinal(4)    == '4th'
    assert tools.to_ordinal(11)   == '11th'
    assert tools.to_ordinal(12)   == '12th'
    assert tools.to_ordinal(13)   == '13th'
    assert tools.to_ordinal(21)   == '21st'
    assert tools.to_ordinal(1234) == '1234th'
    assert tools.to_ordinal(-2)   == '-2nd'
    assert tools.to_ordinal('1')  == '1st'

    with pytest.raises(ValueError):
        tools.to_ordinal('a')
    with pytest.raises(ValueError):
        tools.to_ordinal('1.1')
    with pytest.raises(TypeError):
        tools.to_ordinal(1.1)