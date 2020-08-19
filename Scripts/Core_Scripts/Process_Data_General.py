import pandas as pd
from Core_Scripts.Custom_Functions.Functions_General import append_df_to_excel
import Core_Scripts.Custom_Functions.Functions_Custom_Functions as processPDFdata
import os
import csv

# so that output doesnt get cut short when displaying, below line will widen what the print window shows
pd.options.display.width = None

cwd = os.getcwd()


def script_process_data_general(df_markup, df_pdfdata):
    print('Additional Processing: Calculating markup completion time.')
    datecolumn = 'Time_YMD'
    creationdate = '/CreationDate'

    # remove rows that have no date values (errors or electronic signature/stamps that arent markups)
    df_markup.drop(df_markup[df_markup[datecolumn] == 'None'].index, inplace=True)
    df_markup.reset_index(drop=True)
    df_cut = df_markup.drop(columns=['/Subj', '/Contents'])

    parameterlist = ['/Subtype', creationdate, 'FromTeam', 'Filename']
    pdfData = processPDFdata.determine_completion_times(df_cut, df_pdfdata, parameterlist)

    return pdfData


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

    markupsheet = 'MarkupData'
    pdfsheet = 'PDF_Data'
    print('Additional Processing: Loading data')
    db_markup = pd.read_excel(db_name, sheet_name=markupsheet)
    db_pdf_data = pd.read_excel(db_name, sheet_name=pdfsheet)
    print('Additional Processing: Data loaded')

    df_pdf_data = script_process_data_general(db_markup, db_pdf_data)

    print('Additional Processing: Saving data back to database')
    append_df_to_excel(db_name, df_pdf_data, pdfsheet, startrow=0, truncate_sheet=True)
    print('Additional Processing: Resulting data saved:')
    print(df_pdf_data)
    print('Additional Processing: Markup completion times updated.')

