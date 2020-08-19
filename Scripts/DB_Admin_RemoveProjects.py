import Core_Scripts.Custom_Functions.Functions_GUI as GUI
import Core_Scripts.Custom_Functions.Functions_Configs as configFunc
import os
import tkinter as tk
import mysql.connector
import math

# get current path where script is ran
cwd = os.getcwd()
table_names = ['markup_data', 'pdf_data', 'raw_markups', 'visualization_data']
target_table = 'visualization_data'

# incorporate a check to see if the config file already has data provided
configName = 'SQL_Config.csv'
fields = 'Host', 'User', 'Password', 'Database_Name'
config, config_exist = configFunc.check_for_config(configName, field_list=fields)

master_window = tk.Tk()
master_window.title('Config Setup: Database information')

entry_form = GUI.makeform(master_window, fields, config_exist, config)
# binds code to run if the user presses the enter key when in the form
# master_window.bind('<Return>', (lambda event, e=entry_form: get_input_data(e)))
# Update button and quit button do the same commands
simple_identity = tk.IntVar()
ok_button = tk.Button(master_window, text='Update', command=master_window.quit)
ok_button.pack(side=tk.LEFT, padx=5, pady=5)
quit_button = tk.Button(master_window, text='Quit', command=master_window.destroy)
quit_button.pack(side=tk.LEFT, padx=5, pady=5)

master_window.mainloop()

# if the user hit X or cancel, this should fail and no changes should be made
# get the data from the entry fields
entry_inputs = GUI.get_input_data(entry_form)
# correlate the fields to the entry inputs (same amount of values for each) into key: value pairs
config = dict(zip(fields, entry_inputs))

# destroy the previous window to remove from the user view before the project selection comes up
master_window.destroy()
# get SQL connection working to load project data from
connection = mysql.connector.connect(host=config['Host'],
                                     user=config['User'],
                                     passwd=config['Password'],
                                     database=config['Database_Name'])

print('Default project database name:', target_table)
mycursor = connection.cursor()
# SQL syntax for project column name has to be manually updated if it is renamed
mycursor.execute("SELECT Project FROM " + target_table)
# SQL comes in as a tuple, vector conversion into a simplified list of strings
project_list = mycursor.fetchall()
# convert tuple from mysql into a list of strings, get a set (to remove duplicates), and convert the set into a list
# sort the list afterwards for presentation and clarity
projects_string_list = sorted(list(set([s[0] for s in project_list])))

print(projects_string_list)

project_window = tk.Tk()
project_window.title('Project selection')

# set the variable and a default value for the menu to use
variable = tk.StringVar()
variable.set('None')

windowdata = {}
total = len(projects_string_list)
max_columns = 3
max_rows = math.ceil(total/max_columns)
active_column = 1
active_row = 1
for eachelement in projects_string_list:
    var = tk.IntVar()
    tickbox = tk.Checkbutton(project_window, text=eachelement, variable=var)
    tickbox.grid(row=active_row, column=active_column)
    windowdata[eachelement] = var
    active_row += 1
    if active_row > max_rows:
        active_row = 1
        active_column += 1


# in the button line, have to use no parenthesis to execute a custom function, otherwise have to provide a lambda
# difficult to pass the project window parameter from outside to a function to quit, but using the global variable and
# quitting within the function works.
def confirm_button():
    project_window.quit()
    delete_projects = []
    for eachbutton in windowdata:
        tick_state = windowdata[eachbutton].get()
        # print('tickbox value for: ', eachbutton, "---", tick_state)
        if tick_state == 1:
            delete_projects.append(eachbutton)

    print('Deleting: ', delete_projects)
    for eachproject in delete_projects:
        # delete syntax here
        for eachtable in table_names:
            delete_syntax = "DELETE FROM " + eachtable + " WHERE Project = '" + eachproject + "'"
            print('Executing: ', delete_syntax)
            mycursor.execute(delete_syntax)
    # need to commit to execute the code and save back to database
    connection.commit()


# add 'Done' button, command can be a function, but without parenthesis (above) if necessary to add extra functionality
# this only executes the code if the Done option is pressed and not under any other case
pick_button = tk.Button(project_window, text="Done", command=confirm_button)
# pick_button.pack(side='bottom')
pick_button.grid(row=max_rows+1, column=max_columns)
quit_chosen = tk.BooleanVar()
quit_button = tk.Button(project_window, text='Quit', command=project_window.destroy)
quit_button.grid(row=max_rows+2, column=max_columns)

# run tkinter to show the dialogue box
tk.mainloop()

# print(config)
os.chdir(cwd)
