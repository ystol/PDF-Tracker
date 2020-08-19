import pandas as pd
from Core_Scripts.Custom_Functions.Functions_General import append_df_to_excel
import Core_Scripts.Custom_Functions.Functions_Formatting_Data as formatFunctions
import Core_Scripts.Custom_Functions.Functions_Custom_Functions as processFunctions
import os
import csv

# so that output doesnt get cut short when displaying, below line will widen what the print window shows
pd.options.display.width = None

cwd = os.getcwd()


def script_analyze_markups(df_markupdata, df_pdfdata, engineers, bimteam):
    column_as_id = 'Filename'

    # remove rows that have no date values (errors or electronic signature/stamps that arent markups)
    try:
        df_markupdata.drop(df_markupdata[df_markupdata['/CreationDate'] == 'None'].index, inplace=True)
        df_markupdata.reset_index(drop=True)
    except ValueError:
        pass

    # characters which signify a split between drawing number and drawing title
    strset = ['_', ' ', '.']
    df_pdfdata['DwgNo'] = [formatFunctions.remove_characters(formatFunctions.extract_before_character(s, strset), strset)
                           for s in df_pdfdata[column_as_id]]
    # find out how many markups are on each file, only counts markups with an author coming from the
    # engineer team
    print('Analyze Markups: Calculating Total Markup Volume')
    df_pdfdata = processFunctions.count_total_markups(column_as_id, df_markupdata, df_pdfdata, 'MarkupCount', engineers)

    # find out who the latest one to add markups was
    print('Analyze Markups: Identifying last editor')
    df_pdfdata = processFunctions.last_markup_addition(column_as_id, df_pdfdata, df_markupdata, 'LastMarkupEditFrom')

    # label who has stamped the drawing (both, engineer only, bim only)
    print('Analyze Markups: Finding stamp users')
    df_pdfdata = processFunctions.identify_stamps_by_team(column_as_id, df_pdfdata, df_markupdata, engineers, bimteam)

    # add and identify which file is the latest
    print('Analyze Markups: Calculating Latest drawings')
    latestcol, dwgcol, createdcol = 'Latest', 'DwgNo', '/CreationDate'
    df_pdfdata = processFunctions.identify_if_latest(df_pdfdata, dwgcol, column_as_id, createdcol)

    return df_pdfdata


# run this if the script is ran standalone
if __name__ == '__main__':
    configName = '../Local_Config.csv'
    # get the config file
    with open(configName) as config_file:
        reader = csv.reader(config_file)
        config = dict(reader)

    db_name = config['DB_Filename']
    xlPath = config['DB_Filepath']
    markupsheet = 'MarkupData'
    pdfsheet = 'PDF_Data'
    teamsheet = 'TeamList'

    # have to change path to the location of the database to read the file properly
    os.chdir(xlPath)
    print('Analyze Markups: Loading data')
    db_format_markup_data = pd.read_excel(db_name, sheet_name=markupsheet)
    db_pdf_data = pd.read_excel(db_name, sheet_name=pdfsheet)
    db_team_data = pd.read_excel(db_name, sheet_name=teamsheet)
    print('Analyze Markups: Data loaded')

    # convert dataframe column (series type) to a list in order to work with it easier
    engineers = db_team_data[db_team_data['Type'] == 'ENG'].Name.tolist()
    bimteam = db_team_data[db_team_data['Type'] == 'BIM'].Name.tolist()

    df_pdfdata = script_analyze_markups(db_format_markup_data, db_pdf_data, engineers, bimteam)

    print('Analyze Markups: Saving back to database')
    append_df_to_excel(db_name, df_pdfdata, pdfsheet, startrow=0, truncate_sheet=True)
    print(df_pdfdata)
    print('Analyze Markups: Markup Analysis Processed')
