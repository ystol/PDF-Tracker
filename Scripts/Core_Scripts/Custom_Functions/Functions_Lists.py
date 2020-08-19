from collections import Counter as listCounter


def count_occurences_in_list(findthis, insideoflist):
    # make sure all lowercase for simplicity of comparisons (assumes string)
    findthis = [s.lower() if type(s) is str else s for s in findthis]
    insideoflist = [s.lower() if type(s) is str else s for s in insideoflist]
    # the Counter method from collections make a dictionary, when it counts like this, which has
    # keys that are each unique entry, and values which say how many times it occurs in the list
    allduplicates = listCounter(insideoflist)
    totalmatches = 0
    for eachelement in findthis:
        values = allduplicates[eachelement]
        # print("Current Value for " + eachelement + ': ' + str(values))
        totalmatches += values
    return totalmatches


def list_flatten(l, a=None):  # to flatten a list
    # check a
    if a is None:
        # initialize with empty list
        a = []
    for i in l:
        if isinstance(i, list):
            list_flatten(i, a)
        else:
            a.append(i)
    return a

