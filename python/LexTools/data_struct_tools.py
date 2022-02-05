################################################################################
# List tools
def get_unique_elements(list1, list2):
    unique_list1 = []
    for x in list1:
        if x not in list2:
            unique_list1.append(x)
    unique_list2 = []
    for x in list2:
        if x not in list1:
            unique_list2.append(x)
    return unique_list1, unique_list2

def get_shared_elements(list1, list2):
    shared_list = []
    for x in list1:
        if x in list2:
            shared_list.append(x)
    return shared_list

def get_duplicates(lst):
    """ Find and return a list of duplicates for an input list"""
    seen = set()
    dups = []
    for x in lst:
        if x in seen:
            dups.append(x)
        else:
            seen.add(x)
    return dups

def all_elements_equal(input_list):
    """ Checks if all elements in an iterable are the same"""
    return len(set(input_list)) <= 1


