# general imports
import pandas as pd
import time
from datetime import datetime
import traceback
# Script imports
from Core_Scripts.Setup_Extract_PDF_Data import script_extract_pdf_data
from Core_Scripts.Setup_Format_Markup_Data import script_format_markup_data
from Core_Scripts.Setup_Analyze_Markups import script_analyze_markups
from Core_Scripts.Process_Data_General import script_process_data_general
from Core_Scripts.Process_Data_History_Summary import script_data_history_summary
# function imports
import Core_Scripts.Custom_Functions.Functions_SQL_Interfacing as save
import Core_Scripts.Custom_Functions.Functions_Custom_Functions as customFunc
import Core_Scripts.Custom_Functions.Functions_Configs as configFunc
import mysql.connector

# so that output doesnt get cut short when displaying, below line will widen what the print window shows
pd.options.display.width = None


def run_analysis_mysql(config_name='SQL_Config.csv'):
    start = time.time()
    # get the config file and database name + directory
    config, found = configFunc.check_for_config(config_name)

    # these values are setup from the config file
    # remove identification is set to be a string 0 or a 1, convert to boolean for ease of use in branches
    project_name = config['Project']
    remove_identification = config['Simplify_Names'] == '1'

    # get SQL connection working
    connection = mysql.connector.connect(host=config['Host'],
                                         user=config['User'],
                                         passwd=config['Password'],
                                         database=config['Database_Name'])

    # this has to come from the DB
    project_table = 'projects'
    mycursor = connection.cursor()
    # SQL syntax for project column name has to be manually updated if it is renamed
    mycursor.execute("SELECT directory FROM " + project_table + " WHERE Project = '" + project_name + "'")
    directory_db = mycursor.fetchone()
    # convert from tuple to a regular string for python to use
    project_directory = directory_db[0]
    # SQL syntax for project column name has to be manually updated if it is renamed
    mycursor.execute("SELECT uses_studio FROM " + project_table + " WHERE Project = '" + project_name + "'")
    studio_property = mycursor.fetchone()
    # convert from tuple to a regular string for python to use
    project_uses_studio = studio_property[0] == 1

    print('Analyzing project: ' + project_name)

    # get team data for classification (only needed for a few functions). team data cant get column names changed
    team_table = 'team_list'
    mycursor = connection.cursor()
    mycursor.execute("SELECT name, type FROM " + team_table)
    # syntax to get data from the database, output is a list of lists per entry, then converted into dataframe
    # to filter results
    team_df = pd.DataFrame(mycursor.fetchall(), columns=['Name', 'Type'])
    eng_team_list = team_df[team_df['Type'] == 'ENG'].Name.tolist()
    bim_team_list = team_df[team_df['Type'] == 'BIM'].Name.tolist()

    # extraction of data, timing for each main process for general time to execute
    start_extracting = time.time()
    raw_markup_data, raw_pdf_data = script_extract_pdf_data(project_directory)
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

    # saving to database, sheet names
    print('Saving data.')
    start_saving = time.time()

    # if we want to remove identification, replace names in the data sets accordingly
    if remove_identification:
        print('Removing Identifying Names')
        # to make functions easier to work with, capitalize the team data
        authors = [s.upper() for s in team_df['Name'].tolist()]
        author_type = [s.upper() for s in team_df['Type'].tolist()]
        # Create a dictionary of author names to types
        team_mapping = dict(zip(authors, author_type))

        author_col = '/T'
        # convert to initials for raw markup data, fix condition where there is no author
        author_initials = customFunc.simplify_author_names(raw_markup_data[author_col].tolist(), team_mapping)
        author_initials = ['None' if s == 'N' else s for s in author_initials]
        raw_markup_data[author_col] = author_initials

        # convert to initials for formatted markup data, fix condition where there is no author
        author_initials = customFunc.simplify_author_names(formatted_markup_data[author_col].tolist(), team_mapping)
        author_initials = ['None' if s == 'N' else s for s in author_initials]
        formatted_markup_data[author_col] = author_initials

        # convert to initials for final pdf data, fix condition where there is no author
        author_col = 'LastMarkupEditFrom'
        author_initials = customFunc.simplify_author_names(analyzed_pdf_data[author_col].tolist(), team_mapping)
        author_initials = ['None' if s == 'N' else s for s in author_initials]
        analyzed_pdf_data[author_col] = author_initials
        print('Author Identification removed')

    # SQL saving variables, pdf table col names should be mapped according to the order the dataframe is in
    pdf_table = 'pdf_data'
    print('Saving: saving pdf data to ' + pdf_table)
    pdf_table_col_names = ['CreationDate', 'ModDate', 'Filename', 'Project', 'DwgNo', 'MarkupCount', 'Last_Editor',
                           'StampedBy', 'Eng_Stamp_Type', 'Latest', 'Engineer_Revised', 'BIM_Complete', 'Complete_Time']
    delete_syntax = "DELETE FROM " + pdf_table + " WHERE Project = '" + project_name + "'"
    save.save_to_SQL(connection, pdf_table, pdf_table_col_names, analyzed_pdf_data,
                     delete_syntax_condition=delete_syntax)

    # prepare the raw markups for saving, this can error if there are no raw markups when savings, so need to catch
    # SQL saving variables, pdf table col names should be mapped according to the order the dataframe is in
    raw_markup_table = 'raw_markups'
    print('Saving: saving raw markup data to ' + raw_markup_table)
    raw_markup_table_col_names = ['Subtype', 'CreationDateRaw', 'Subject', 'Contents', 'Author', 'Filename', 'Project']
    delete_syntax = "DELETE FROM " + raw_markup_table + " WHERE Project = '" + project_name + "'"

    # try to save, and if failed, attempt to log error
    errors = 0
    saving_log = open('Logs/SQL_save_errors.txt', "a")
    try:
        save.save_to_SQL(connection, raw_markup_table, raw_markup_table_col_names, raw_markup_data,
                         delete_syntax_condition=delete_syntax)
    except Exception:
        errors += 1
        # we want to see a timestamp and the project name that this failed on
        errmsg = "\n" + str(datetime.now()) + " EXCEPTION BELOW DURING SAVING RAW MARKUPS FOR PROJECT {"
        errmsg += project_name + "}:\n"
        errmsg += str(traceback.format_exc())
        saving_log.write(errmsg)
        print(errmsg)

    # markups need a drop included until functionality is adjusted to exclude certain columns from being populated
    # functionality can be included in SQL if needed, but may need to get added at a later point
    markup_table = 'markup_data'
    print('Saving: saving markup data to ' + markup_table)
    markup_table_col_names = ['Subtype', 'CreationDate', 'Subject', 'Author', 'Filename', 'Project',
                              'DwgNo', 'AuthorType']
    delete_syntax = "DELETE FROM " + markup_table + " WHERE Project = '" + project_name + "'"
    sql_markup_df = formatted_markup_data.drop(columns=['Time_YMD', 'Time_HMS', '/Contents'])
    # try to save, and if failed, attempt to log error
    try:
        if len(sql_markup_df) < 1:
            print('No markup data to save.')
        else:
            save.save_to_SQL(connection, markup_table, markup_table_col_names, sql_markup_df,
                             delete_syntax_condition=delete_syntax)
    except Exception:
        errors += 1
        # we want to see a timestamp and the project name that this failed on
        errmsg = "\n" + str(datetime.now()) + " EXCEPTION BELOW DURING SAVING FORMATTED MARKUPS FOR PROJECT {"
        errmsg += project_name + "}:\n"
        errmsg += str(traceback.format_exc())
        saving_log.write(errmsg)
        print(errmsg)
    # close the log file as it shouldnt be used anymore past this point
    saving_log.close()

    visualization_table = 'visualization_data'
    print('Saving: saving visualization data to ' + visualization_table)
    visualization_table_col_names = ['Date', 'Engineer_Revised', 'BIM_Completed', 'Total_Outstanding', 'Project']
    delete_syntax = "DELETE FROM " + visualization_table + " WHERE Project = '" + project_name + "'"
    save.save_to_SQL(connection, visualization_table, visualization_table_col_names, visualization_data,
                     delete_syntax_condition=delete_syntax)

    # end timer and figure out the time to execute the scripts
    end = time.time()
    runtime = round(end-start, 3)
    total_file_count = len(analyzed_pdf_data.iloc[:, 0])
    time_list = [datetime.now(), total_file_count, runtime, project_name]
    time_table = 'runtime_history'
    time_table_columns = ['Date', 'File_Count', 'Runtime', 'Project']
    print('Saving: saving data to ' + time_table)
    save.save_to_SQL(connection, time_table, time_table_columns, time_list)
    print('Data saved. All processing complete. Total processed time:', str(runtime), 'seconds for',
          str(total_file_count), 'files.')

    print('Time Summaries (in seconds):')
    print('Time to save:                ', str(round(end-start_saving, 3)))
    print('Time to extract:             ', str(round(start_formatting_markup-start_extracting, 3)))
    print('Time to format:              ', str(round(start_analyzing-start_formatting_markup, 3)))
    print('Time to analyze:             ', str(round(start_data_general-start_analyzing, 3)))
    print('Time to process:             ', str(round(start_data_history-start_data_general, 3)))
    print('Time to calculate history:   ', str(round(start_saving-start_data_history, 3)))

    if errors > 0:
        print('---------------------------------------------',
              '\nERRORS FOUND DURING RUNTIME, REVIEW LOG FILES\n',
              '---------------------------------------------')


if __name__ == '__main__':
    # log errors of main script
    general_log = open('Logs/script_error.txt', 'a')
    try:
        run_analysis_mysql()
    except Exception:
        # we want to see a timestamp and the project name that this failed on
        errmsg = "\n" + str(datetime.now()) + " EXCEPTION BELOW: \n"
        errmsg += str(traceback.format_exc())
        general_log.write(errmsg)
        print(errmsg)
    general_log.close()

