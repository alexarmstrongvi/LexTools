# Import all the functions that should be accessible directly from LexTools
# e.g. LexTools.to_ordinal instead of LexTools.string_tools.to_ordinal

# It is possible to use `from string_tools import *` but this pollutes
# the namespace with every global and module defined in those files.
# This is a better practice to get used to.

from LexTools.integer_tools import (
    ndigits,
    pop_digit,
    split_int,
    join_ints,
    get_nth_digit,
)

from LexTools.string_tools import (
    strip_ansi_escape,
    grep,
    to_ordinal,
)

from LexTools.data_struct_tools import (
    get_unique_elements,
    get_shared_elements,
    get_duplicates,
    all_elements_equal,
)

from LexTools.asciihist import ascii_hist

from LexTools.loading_bar import LoadingBar

from LexTools.other_tools import (
    pd_display_all,
    get_cmd_output,
)
