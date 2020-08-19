import pandas as pd
import Core_Scripts.Custom_Functions.Functions_Formatting_Data as formatFunc
import Core_Scripts.Custom_Functions.Functions_General as generalFunc
import Core_Scripts.Custom_Functions.Functions_Lists as listFunc
import os
import csv

# so that output doesnt get cut short when displaying, below line will widen what the print window shows
pd.options.display.width = None


def script_format_markup_data(base_markup_data, engineers, bimteam):
    markupdf = base_markup_data.reset_index(drop=True)
    # define the author column for identification tasks, column name for the date
    authorcolumn = '/T'
    datecolumn = '/CreationDate'

    # remove extra bloat from date field (extra characters from extractions)
    removestrings = ['D:']

    print('Format Markups: Formatting Dates')
    markupdf[datecolumn] = markupdf[datecolumn].apply(lambda s: formatFunc.remove_characters(formatFunc.extract_before_character(s, ["-", "+"]), removestrings))
    # date time format is YYYYmmDDhhMMss or %Y%m%d%H%M%S
    # try:  # in case formatting was already changed, to keep working on the file
    markupdf[datecolumn] = markupdf[datecolumn].apply(lambda s: formatFunc.evaluate_date(s))
    # except ValueError:  # ignore if the date formatting failed
    #     pass

    # identify the drawing number for easier identification
    column_as_id = 'Filename'
    # characters which signify a split between drawing number and drawing title
    strset = ['_', ' ', '.']
    print('Format Markups: Determining Drawing Numbers')
    markupdf['DwgNo'] = [formatFunc.remove_characters(formatFunc.extract_before_character(s, strset), strset)
                         for s in markupdf[column_as_id]]

    print('Format Markups: Splitting Dates')
    # Split dates into Y-m-d and h-m-s for data visualizations
    datedf = markupdf[datecolumn]
    yearmonday = []
    hrminsec = []
    for datestring in datedf:
        yrmonday, hrmins = formatFunc.extract_date_time(datestring)
        yearmonday.append(yrmonday)
        hrminsec.append(hrmins)
    markupdf['Time_YMD'] = yearmonday
    markupdf['Time_HMS'] = hrminsec

    print('Format Markups: Identifying markup owners')
    # create a column to identify who the markup came from for simplicity
    fromteam = 'FromTeam'
    teamdata = []
    # replace the periods with spaces to be more consistent with the team list data formatting
    markupdf[authorcolumn] = [str(s).replace('.', ' ') for s in markupdf[authorcolumn]]

    for eachmarkup in markupdf[authorcolumn]:
        # count if there are any name matches for engineer list or for bim list
        engfound = listFunc.count_occurences_in_list([eachmarkup], engineers) > 0
        bimfound = listFunc.count_occurences_in_list([eachmarkup], bimteam) > 0
        # this logic might be better optimized
        if engfound and not bimfound:
            owner = 'ENG'
        elif bimfound and not engfound:
            owner = 'BIM'
        else:
            owner = 'N/A'
        teamdata.append(owner)
    # insert team data determined into main dataframe column
    markupdf[fromteam] = teamdata
    print('Format Markups: Markup owners identified')
    # reset index just to keep cleanliness
    markupdf.reset_index(inplace=True, drop=True)
    return markupdf


if __name__ == '__main__':
    configName = '../Local_Config.csv'
    # get the config file and extract database name + directory
    with open(configName) as config_file:
        reader = csv.reader(config_file)
        config = dict(reader)
    # get the name of where to save to and the directory the file is stored
    db_name = config['DB_Filename']
    xlPath = config['DB_Filepath']
    # shift directory to be able to find/save to the right location
    os.chdir(xlPath)

    teamsheet = 'TeamList'
    print('Format Markups: Loading Data')
    df_teamdata = pd.read_excel(db_name, sheet_name=teamsheet)
    # convert dataframe column (series type) to a list in order to work with it easier
    engineers = df_teamdata[df_teamdata['Type'] == 'ENG'].Name.tolist()
    bimteam = df_teamdata[df_teamdata['Type'] == 'BIM'].Name.tolist()
    df = pd.read_excel(db_name, sheet_name='MarkupRawData')
    print('Format Markups: Data Loaded')

    # run function above
    df = script_format_markup_data(df, engineers, bimteam)

    markupsheetname = 'MarkupData'
    print('Format Markups: Saving back to database')
    print('Format Markups: Dataframe output:')
    print(df)
    generalFunc.append_df_to_excel(db_name, df, markupsheetname, startrow=0, truncate_sheet=True)
    print('Format Markups: Markup Formatting Complete')
