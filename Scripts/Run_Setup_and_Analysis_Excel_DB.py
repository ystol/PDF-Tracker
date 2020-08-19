# general imports
import pandas as pd
import os
import time
from datetime import datetime
# Script imports
from Core_Scripts.Setup_Extract_PDF_Data import script_extract_pdf_data
from Core_Scripts.Setup_Format_Markup_Data import script_format_markup_data
from Core_Scripts.Setup_Analyze_Markups import script_analyze_markups
from Core_Scripts.Process_Data_General import script_process_data_general
from Core_Scripts.Process_Data_History_Summary import script_data_history_summary
# function imports
import Core_Scripts.Custom_Functions.Functions_General as generalFunc
import Core_Scripts.Custom_Functions.Functions_Custom_Functions as customFunc
import Core_Scripts.Custom_Functions.Functions_Configs as configFunc


def run_analysis_excel():
    start = time.time()
    configName = 'Local_Config.csv'
    # get the config file and database name + directory
    config, found = configFunc.check_for_config(configName)

    db_name = config['DB_Filename']
    db_path = config['DB_Filepath']
    maindirectory = config['Folderpath']
    project_name = config['Foldername']
    remove_identification = config['Simplify_Names'] == '1'
    os.chdir(db_path)

    # get team data for classification (only needed for a few functions)
    teamsheet = 'TeamList'
    db_team_data = pd.read_excel(db_name, sheet_name=teamsheet)
    eng_team_list = db_team_data[db_team_data['Type'] == 'ENG'].Name.tolist()
    bim_team_list = db_team_data[db_team_data['Type'] == 'BIM'].Name.tolist()

    # extraction of data, timing for each main process for general time to execute
    start_extracting = time.time()
    raw_markup_data, raw_pdf_data = script_extract_pdf_data(maindirectory)
    raw_markup_data['Project'] = project_name
    raw_pdf_data['Project'] = project_name

    # format and cleanup markup data, keep raw markup data as-is
    start_formatting_markup = time.time()
    formatted_markup_data = script_format_markup_data(raw_markup_data, eng_team_list, bim_team_list)

    # format raw pdf data and calculate summaries of markups for each pdf
    start_analyzing = time.time()
    formatted_pdf_data = script_analyze_markups(formatted_markup_data, raw_pdf_data, eng_team_list, bim_team_list)

    # calculate completion times where applicable (check markups and note most recent ones from each team)
    start_data_general = time.time()
    analyzed_pdf_data = script_process_data_general(formatted_markup_data, formatted_pdf_data)

    # calculate graph and time series showing rates of completion and backlog amount on a given day
    start_data_history = time.time()
    visualization_data = script_data_history_summary(analyzed_pdf_data)
    visualization_data['Project'] = project_name

    # saving to database, sheet names, start timer for saving
    print('Saving data.')
    start_saving = time.time()

    # if we want to remove identification, replace names in the data sets accordingly
    if remove_identification:
        print('Removing Identifying Names')
        # to make functions easier to work with, capitalize the team data
        authors = [s.upper() for s in db_team_data['Name'].tolist()]
        author_type = [s.upper() for s in db_team_data['Type'].tolist()]
        # Create a dictionary of author names to types
        team_mapping = dict(zip(authors, author_type))

        author_col = '/T'
        # convert to initials for raw markup data, fix where there is no author
        author_initials = customFunc.simplify_author_names(raw_markup_data[author_col].tolist(), team_mapping)
        author_initials = ['None' if s == 'N' else s for s in author_initials]
        raw_markup_data[author_col] = author_initials

        # convert to initials for formatted markup data, fix where there is no author
        author_initials = customFunc.simplify_author_names(formatted_markup_data[author_col].tolist(), team_mapping)
        author_initials = ['None' if s == 'N' else s for s in author_initials]
        formatted_markup_data[author_col] = author_initials

        # convert to initials for final pdf data, fix where there is no author
        author_col = 'LastMarkupEditFrom'
        author_initials = customFunc.simplify_author_names(analyzed_pdf_data[author_col].tolist(), team_mapping)
        author_initials = ['None' if s == 'N' else s for s in author_initials]
        analyzed_pdf_data[author_col] = author_initials
        print('Author Identification removed')

    # saving variables for easier adjustments
    rawmarkupsheet = 'MarkupRawData'
    formatted_markup_sheet = 'MarkupData'
    pdf_data_sheet = 'PDF_Data'
    visualize_sheet = 'VisualizationData'
    time_sheet = 'Runtime History'
    # reset the path to make sure it saves to the right location
    os.chdir(db_path)
    generalFunc.append_df_to_excel(db_name, raw_markup_data, rawmarkupsheet, startrow=0, truncate_sheet=True)
    generalFunc.append_df_to_excel(db_name, formatted_markup_data, formatted_markup_sheet, startrow=0, truncate_sheet=True)
    generalFunc.append_df_to_excel(db_name, analyzed_pdf_data, pdf_data_sheet, startrow=0, truncate_sheet=True)
    generalFunc.append_df_to_excel(db_name, visualization_data, visualize_sheet, startrow=0, truncate_sheet=True)

    # end timer and calculate the execution times of portions of the codes, then save
    end = time.time()
    runtime = round(end-start, 3)
    total_file_count = len(analyzed_pdf_data.iloc[:, 0])
    time_df = pd.DataFrame([datetime.now(), total_file_count, runtime, project_name])
    generalFunc.append_df_to_excel(db_name, time_df.transpose(), time_sheet, header=None)
    print('Data saved. All processing complete. Total processed time:', str(runtime), 'seconds for',
          str(total_file_count), 'files.')

    print('Time Summaries (in seconds):')
    print('Time to save:                ', str(round(end-start_saving, 3)))
    print('Time to extract:             ', str(round(start_formatting_markup-start_extracting, 3)))
    print('Time to format:              ', str(round(start_analyzing-start_formatting_markup, 3)))
    print('Time to analyze:             ', str(round(start_data_general-start_analyzing, 3)))
    print('Time to process:             ', str(round(start_data_history-start_data_general, 3)))
    print('Time to calculate history:   ', str(round(start_saving-start_data_history, 3)))


if __name__ == '__main__':
    run_analysis_excel()