import Core_Scripts.Custom_Functions.Functions_GUI as GUI
import Core_Scripts.Custom_Functions.Functions_Configs as configFunc
import os
import tkinter as tk
import mysql.connector

# get current path where script is ran
cwd = os.getcwd()

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
identification_checkbox = tk.Checkbutton(master_window, text='Simplify Names', variable=simple_identity)
identification_checkbox.pack(side=tk.LEFT, padx=5, pady=5)
ok_button = tk.Button(master_window, text='Update', command=master_window.quit)
ok_button.pack(side=tk.LEFT, padx=5, pady=5)
quit_button = tk.Button(master_window, text='Quit', command=master_window.destroy)
quit_button.pack(side=tk.LEFT, padx=5, pady=5)

master_window.mainloop()

# if the user hit X or cancel, this should fail and no changes should be made
try:
    # get the data from the entry fields
    entry_inputs = GUI.get_input_data(entry_form)
    # correlate the fields to the entry inputs (same amount of values for each) into key: value pairs
    config = dict(zip(fields, entry_inputs))
    config['Simplify_Names'] = simple_identity.get()

    # destroy the previous window to remove from the user view before the project selection comes up
    master_window.destroy()
    # get SQL connection working to load project data from
    connection = mysql.connector.connect(host=config['Host'],
                                         user=config['User'],
                                         passwd=config['Password'],
                                         database=config['Database_Name'])
    project_table = 'projects'
    print('Default project database name:', project_table)
    mycursor = connection.cursor()
    # SQL syntax for project column name has to be manually updated if it is renamed
    mycursor.execute("SELECT Project FROM " + project_table)
    # SQL comes in as a tuple, vector conversion into a simplified list of strings
    project_list = mycursor.fetchall()
    projects_string_list = [s[0] for s in project_list]

    project_window = tk.Tk()
    project_window.title('Project selection')

    # set the variable and a default value for the menu to use
    variable = tk.StringVar()
    variable.set('None')

    # OptionMenu is a dropdown, needs the root, a variable to store selection, and can take a list of
    # items to show (* allows it to make a proper list)
    options = tk.OptionMenu(project_window, variable, *projects_string_list)
    # extra padding needed to allow the title to be visible for user readability
    options.pack(padx=100, pady=3)

    # add a 'Done' button (eventually have to figure out how to make a pick new here would be good)
    pick_button = tk.Button(project_window, text="Done", command=project_window.quit)
    pick_button.pack()

    # run tkinter to show the dialogue box
    tk.mainloop()
    if variable.get() != 'None':
        config['Project'] = str(variable.get())
    else:
        config['Project'] = 'None'
        print('No project selected')

    print(config)
    os.chdir(cwd)
    configFunc.save_config(configName, config)

except:
    print('No changes to config file.')
