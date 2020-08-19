import pandas as pd
from Core_Scripts.Custom_Functions.Functions_General import append_df_to_excel
import Core_Scripts.Custom_Functions.Functions_General as extractFunctions
import Core_Scripts.Custom_Functions.Functions_Custom_Functions as processPDFdata
import os
from tkinter import Tk
from tkinter.filedialog import askdirectory
import csv

# so that output doesnt get cut short when displaying, below line will widen what the print window shows
pd.options.display.width = None


def script_extract_pdf_data(pdfFolder, ask_target_directory=False):
    if ask_target_directory:
        Tk().withdraw()  # dont want the full GUI
        print('Choose folder where to analyze PDFs from.')
        pdfFolder = askdirectory()

    # have to change the working directory to the target so that 'open' function works (if the URL ver isnt being used)
    # note where the original directory its running from is
    starting_wd = os.getcwd()
    os.chdir(pdfFolder)
    print('Directory location: ' + pdfFolder)
    fileset = extractFunctions.get_files_from_directory(pdfFolder)

    # get the list of applicable pdfs from file list to run this on, to find only pdfs, use an if
    # condition in the list composition to identify a pdf file
    datafiles = [file for file in fileset if file[-4:] == '.pdf']

    author_column = '/T'
    stringlist = ['/Subtype', '/CreationDate', '/Subj', '/Contents', author_column]
    date_attributes = ['/CreationDate', '/ModDate']

    # extract all markup data and pdf general data for each pdf file and add onto a dataframe for storing
    markupdata = pd.DataFrame()
    pdfdata = pd.DataFrame()
    for filename in datafiles:
        print('Extract PDF Data: Processing ' + filename)
        markup_data_df = processPDFdata.extract_from_pdf(filename, stringlist, ignore_string='/Link', remove=True)
        pdf_data_df = processPDFdata.get_pdf_date_data(filename, date_attributes)
        markupdata = pd.concat([markupdata, markup_data_df], ignore_index=True)
        markupdata[author_column] = [s.replace('.', ' ') for s in markupdata[author_column]]
        pdfdata = pd.concat([pdfdata, pdf_data_df], ignore_index=True)

    # return to the directory started from (to reset if needs to run in succession)
    os.chdir(starting_wd)
    return markupdata, pdfdata


# run this if the script is ran standalone
if __name__ == '__main__':
    configName = '../Local_Config.csv'
    # get the config file
    with open(configName) as config_file:
        reader = csv.reader(config_file)
        config = dict(reader)

    maindirectory = config['Folderpath']

    markupdata, pdfdata = script_extract_pdf_data(maindirectory, ask_target_directory=False)

    db_name = config['DB_Filename']
    xlPath = config['DB_Filepath']

    # saving to excel (eventually should be more efficient database type)
    # need to set directory to save the excel to as well before saving
    sheetname = 'MarkupRawData'
    datasheetname = 'PDF_Data'
    # use path from config file (should be setup to point to main database)
    os.chdir(xlPath)
    print('Extract PDF Data: Saving Data')
    append_df_to_excel(db_name, markupdata, sheetname, startrow=0, truncate_sheet=True)
    append_df_to_excel(db_name, pdfdata, datasheetname, startrow=0, truncate_sheet=True)
    print('Extract PDF Data: Save Complete')
