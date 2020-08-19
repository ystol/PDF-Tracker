import pandas as pd
import Core_Scripts.Custom_Functions.Functions_Formatting_Data as formatFunc
from Core_Scripts.Custom_Functions.Functions_General import append_df_to_excel
import os
from collections import Counter
import datetime
import csv

# so that output doesnt get cut short when displaying, below line will widen what the print window shows
pd.options.display.width = None

cwd = os.getcwd()


def script_data_history_summary(df):
    print('Data Gathering: Collating data for summarizing')
    # the column names of the main date values to check for the date ranges
    datecolumn = '/CreationDate'
    datecolumnMod = '/ModDate'
    # in pdf data, the column names for the engineer date stamp and the bim date stamped
    engready = 'Engineer_Revised'
    bimready = 'BIM_Completed'
    # column name for new column in visualization data
    remaining = 'Total_Outstanding'

    # remove rows that have errored date values (errors or electronic signature/stamps that arent markups)
    # if there are any
    try:
        df_date_calc = df.drop(df[df[datecolumn] == 'Error'].index)
    except ValueError:
        df_date_calc = df

    # get the max and minimum dates from all drawings that we have (based on solely creation dates)
    # this assumes that at the deadline day there are no markups remaining, thus creation date can be
    # a good metric to find out the range of dates to make
    try:
        newestCreate = max(df_date_calc[datecolumn])
        # need to separate into two lines to simplify the logic (optimization for one line index might be better?) to
        # only get the column of dates that exclude 'None' values (meaning a drawing is fresh and has no edits)
        modified_list = df_date_calc[df_date_calc[datecolumnMod] != 'None']
        try:
            newestMod = max(modified_list[datecolumnMod])
        except TypeError:
            newestMod = datetime.datetime(0, 0, 0, 0, 0, 0)
        newest = max([newestMod, newestCreate])
    except ValueError:
        newest = datetime.datetime.today()
    oldest = min(df_date_calc[datecolumn])
    # create a list of dates start from a known date and ending at another known date
    daterange = pd.date_range(start=oldest.date(), end=newest.date(), closed=None)
    daterange = [dt.date() for dt in daterange]

    # simplify data by reducing the irrelevant rows to quicker process
    df_adjusted = df.drop(df[df['StampedBy'] == "None"].index)

    # counter object have dictionary interface, so if you use a date as an index, it will return the count of that date
    # or a 0 if there are no matches (https://docs.python.org/2/library/collections.html)
    # making sure the timestamp is in string format helps resolve data type issues for this counter
    ready_ymd = [formatFunc.extract_ymd(dv, dtformat='%y-%m-%d %H:%M:%S') for dv in df_adjusted[engready]]
    ready_dict = Counter(ready_ymd)
    complete_ymd = [formatFunc.extract_ymd(dv, dtformat='%y-%m-%d %H:%M:%S') for dv in df_adjusted[bimready]]
    complete_dict = Counter(complete_ymd)

    ready = []
    completed = []
    outstanding = []
    # enumerating on the for loop line allows us to use the index that the value corresponds to in another list to
    # iterate with two lists
    for i, eachdate in enumerate(daterange):
        # in the dictionary for ready, get the tally of readys for the current date (zero if no match)
        newengstamped = ready_dict[eachdate]
        ready.append(newengstamped)
        # same as for ready
        newbimstamped = complete_dict[eachdate]
        completed.append(newbimstamped)
        # this try block should only fail once (first index) and should not error otherwise
        try:
            previousoustanding = outstanding[i-1]
        except IndexError:
            previousoustanding = 0
        # the new outstanding is the difference between the bim stamps and the engineer stamps, plus what was in backlog
        newoutstanding = newengstamped - newbimstamped + previousoustanding
        outstanding.append(newoutstanding)

    # create the dataframe to store all the resulting data, then store all relevant data
    time_df = pd.DataFrame()
    time_df['Date'] = daterange
    time_df[engready] = ready
    time_df[bimready] = completed
    time_df[remaining] = outstanding
    print('Data Gathering: History summary completed')

    # remove extra dates (long stream of zeros from start to first markup, and from last markup to end)
    # start at first entry, find where there is a submitted or completed drawing and save the index before it
    first_markup = 0
    for eachindex in range(0, len(time_df[remaining])):
        # if there are no engineer or bim stamps, this variable should return true
        all_zeroes = all([time_df[engready].iloc[eachindex] == 0,
                         time_df[bimready].iloc[eachindex] == 0])
        # when the above condition fails, the loop should end (all leading 0's have been identified)
        if not all_zeroes:
            first_markup = eachindex - 1
            break
    # remove all rows that have no entries until just before the first markup is seen
    time_df.drop(time_df.index[:first_markup], inplace=True)

    # start at the maximum index, and go in reverse until the last submitted or completed drawing
    last_markup = len(time_df[remaining])
    for eachindex in range(len(time_df[remaining]) - 1, 0, -1):
        # same condition as for leading zeroes
        all_zeroes = all([time_df[engready].iloc[eachindex] == 0,
                          time_df[bimready].iloc[eachindex] == 0])
        if not all_zeroes:
            # the index needs +2 because we want to keep one date AFTER the found condition above, and to not
            # drop the row after, have to go one past (index is inclusive so you want to go one ahead of the found)
            last_markup = eachindex + 2
            break
    time_df.drop(time_df.index[last_markup:], inplace=True)
    # reset indices for clarity
    time_df.reset_index(inplace=True, drop=True)
    return time_df


# run this if the script is ran standalone
if __name__ == '__main__':
    configName = '../Local_Config.csv'
    # get the config file
    with open(configName) as config_file:
        reader = csv.reader(config_file)
        config = dict(reader)

    db_name = config['DB_Filename']
    xlPath = config['DB_Filepath']
    os.chdir(xlPath)

    datasheet = 'PDF_Data'
    visualize_sheet = 'VisualizationData'
    db_pdf_data = pd.read_excel(db_name, sheet_name=datasheet)

    time_data = script_data_history_summary(db_pdf_data)

    print('Data Gathering: Data result:')
    print(time_data)
    print('Data Gathering: Saving to database')
    append_df_to_excel(db_name, time_data, visualize_sheet, startrow=0, truncate_sheet=True)
    print('Data Gathering: Save complete')
