import Core_Scripts.Custom_Functions.Functions_GUI as GUI
import Core_Scripts.Custom_Functions.Functions_Configs as configFunc
import os
import tkinter as tk
import mysql.connector
from datetime import datetime
import traceback

# get current path where script is ran
cwd = os.getcwd()
target_table = 'projects'

# incorporate a check to see if the config file already has data provided
configName = 'SQL_Config.csv'
fields = 'Host', 'User', 'Password', 'Database_Name'
config, config_exist = configFunc.check_for_config(configName, field_list=fields)

# database credentials
master_window = tk.Tk()
master_window.title('Config Setup: Database information')

entry_form = GUI.makeform(master_window, fields, config_exist, config)
# binds code to run if the user presses the enter key when in the form
# master_window.bind('<Return>', (lambda event, e=entry_form: get_input_data(e)))
# Update button and quit button do the same commands
ok_button = tk.Button(master_window, text='Update', command=master_window.quit)
ok_button.pack(side=tk.LEFT, padx=5, pady=5)
quit_button = tk.Button(master_window, text='Quit', command=master_window.destroy)
quit_button.pack(side=tk.LEFT, padx=5, pady=5)

master_window.mainloop()
# end database credentials

# if the user hit X or cancel, this should fail and no changes should be made
# get the data from the entry fields
entry_inputs = GUI.get_input_data(entry_form)
# correlate the fields to the entry inputs (same amount of values for each) into key: value pairs
config = dict(zip(fields, entry_inputs))

# destroy the previous window to remove from the user view before the project selection comes up
master_window.destroy()
# get SQL connection working to save project data to
connection = mysql.connector.connect(host=config['Host'],
                                     user=config['User'],
                                     passwd=config['Password'],
                                     database=config['Database_Name'])


# ###----------------------------Start project choosing-------------------------------###
# start tkinter and give the window a title
root = tk.Tk()
root.title("Add Project to Database")
# setup the variables to store the output into using the dialogue
project_name = tk.StringVar()
directory_name = tk.StringVar()

# by default, let the browse button navigate to the users local area where the revu studio project should be, otherwise
# it will navigate to last chosen path or a regular random location
default_path = os.getenv('LOCALAPPDATA') + "\Revu\\00"
default_foldpath = "No folder selected"


def choose_directory():
    # ask for the directory that holds the pdfs
    output = tk.filedialog.askdirectory(title="Select folder containing PDFs", initialdir=default_path)
    folder_label.config(text=output)
    directory_name.set(output)
    return output


# have to use a lambda function on the command line in order to make sure the button can activate anytime the user
# presses the button. If lambda isnt used, it will instantly run and then button will do nothing
# anchor allows you to use a cardinal direction to align to (N/NW/NE/S/SW/SE/E/W/CENTER)
# width allows you to specify the elements overall width as a hard number to alleviate padding necessity
folder_button = tk.Button(root, text="Browse for folder", command=choose_directory,
                          anchor="center", width=15)
folder_label = tk.Label(root, text=default_foldpath, anchor="w", width=70)

proj_entry_field = tk.Entry(root, textvariable=project_name, width=70)
project_entry_label = tk.Label(root, text="Enter Project Name", anchor="w")

done_button = tk.Button(root, text="Ok", command=root.quit, width=5)
cancel_button = tk.Button(root, text="Cancel", command=root.destroy, width=8)

proj_entry_field.grid(row=1, column=1)
project_entry_label.grid(row=1, column=0)
folder_button.grid(row=2, column=0, padx=(10, 10), pady=5)
folder_label.grid(row=2, column=1, padx=(10, 20), pady=5)
done_button.grid(row=3, column=0, pady=5)
cancel_button.grid(row=3, column=1)

tk.mainloop()
# ###----------------------------End project choosing, Save data to DB-------------------------------###
# default behavior is to overwrite the previous entry if a duplicate is found
column_names = ['Project', 'directory']
insert_directory = "'" + directory_name.get() + "'"
insert_projname = "'" + project_name.get() + "'"
sql_syntax = "INSERT into " + target_table + " (" + ','.join(column_names) + ") VALUES (" + \
             ','.join([insert_projname, insert_directory]) + ");"
print("SQL syntax being used:", sql_syntax)
db_cursor = connection.cursor()
saving_log = open('Logs/SQL_Add_Project_Errors.txt', "a")
try:
    db_cursor.execute(sql_syntax)
except Exception:
    # case error when entry exists, delete and try again
    delete_syntax = "DELETE FROM " + target_table + " WHERE Project = " + insert_projname
    db_cursor.execute(delete_syntax)
    try:
        db_cursor.execute(sql_syntax)
    except Exception:
        # we want to see a timestamp and the project name that this failed on
        errmsg = "\n" + str(datetime.now()) + " EXCEPTION BELOW DURING SQL EXECUTION FOR PROJECT {"
        errmsg += project_name + "}:\n"
        errmsg += str(traceback.format_exc())
        saving_log.write(errmsg)
        print(errmsg)
connection.commit()

