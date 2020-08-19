import datetime
import pandas as pd


def evaluate_date(dateval, dtformat='%Y%m%d%H%M%S', dtformat2='%Y-%m-%d'):
    dateval = str(dateval)
    if dateval == "None":
        dt = dateval
    else:
        try:
            dt = datetime.datetime.strptime(str(dateval), dtformat)
        except ValueError:
            try:
                dt = datetime.datetime.strptime(str(dateval), dtformat2)
            except ValueError:
                dt = dateval
    return dt


def extract_date_time(datevalue):
    # format must be the graphical YYYY-MM-DD HH:MM:SS after converting from %Y%m%d%H%M%S
    # outputs the date in string format
    datestring = str(datevalue)
    stringlength = len(datestring)
    if stringlength == 19:
        yearmonthday = datestring[:4] + '-' + datestring[5:7] + '-' + datestring[8:10]
        hourminutesecond = datestring[-8:-6] + ':' + datestring[-5:-3] + ':' + datestring[-2:]
        return yearmonthday, hourminutesecond
    else:
        return 'None', 'None'


# dtformat represent the source string format to convert from
def extract_ymd(datevalue, dtformat='%Y-%m-%d'):
    # needs to be given a date/time string
    if type(datevalue) is str:
        dt = datetime.datetime.strptime(datevalue, dtformat).date()
    elif type(datevalue) is datetime.datetime:
        dt = datevalue.date()
    # check if the element is a pandas timestamp data type, if so, can convert to a date using the pandas date method
    elif isinstance(datevalue, pd.Timestamp):
        if dtformat == '%y-%m-%d %H:%M:%S':
            dt = datevalue.date()
        else:
            dt = datevalue
    else:
        dt = datevalue
    return dt


def remove_characters(stringele, characterlist):
    x = str(stringele)
    for character in characterlist:
        x = x.replace(character, "")
    return x


def split_string(strval, splitchar, split_output):
    # split_output is used to get back a single value instead of a list of the split characters
    try:
        result = str.split(str(strval), splitchar)
        return result[split_output]
    except IndexError:
        return result[0]


def replace_characters(strlist, targetcharacters, newcharacters):
    store = []
    for eachstring in strlist:
        store.append(eachstring.replace(targetcharacters, newcharacters))
    return store


def left(strval, number, remove=False):
    if not remove:
        return strval[:number]
    else:
        return strval[number:]


def right(strval, number, remove=False):
    if not remove:
        return strval[-number:]
    else:
        number += 1
        return strval[:number]


def extract_before_character(strval, characterlist):
    for identify in characterlist:
        # if there is no attribute (modified date), move on and ignore the missing property
        try:
            location = strval.find(identify)
            if location > 0:
                processedstring = remove_characters(left(strval, location), characterlist)
                break
        except AttributeError:
            location = -1
    if location < 0:
        return strval
    else:
        return processedstring


def extract_after_last_character(strval, character):
    fulllen = len(strval)
    listindicies = list(range(0, fulllen))
    # index from the end of the string until the character is found
    for i in listindicies[::-1]:
        # if the character is found, move back one index, and break the loop, stopping i at the next
        if strval[i] == character:
            i += 1
            break
    # the break and using an i works as well when there is no match, as it'll return the full string
    return strval[i:]


def get_all_first_characters(stringlist, delimiter=' '):
    # assumes string list is a list (single values have to be converted to list when function used)
    abbrev_list = []
    # enumeration used to correctly map prefixes (if used)
    for i, s in enumerate(stringlist):
        charlist = s[0]
        # initial of word gets flagged using save_next flag to signify it is past the delimiter
        save_next = False
        for ch in s:
            if save_next:
                charlist += ch
                save_next = False
            if ch == delimiter:
                save_next = True
        abbrev_list.append(charlist)
    return abbrev_list
