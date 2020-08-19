import os
import Core_Scripts.Custom_Functions.Functions_Configs as configFunc
import Core_Scripts.Custom_Functions.Functions_Formatting_Data as formatFunc
import tkinter as tk
import tkinter.filedialog

config = {}

# get current path where script is ran
cwd = os.getcwd()
# for easier adjustment, set variables for certain dictionary keys
fold_path, db_path, db_name = 'Folderpath', 'DB_Filepath', 'DB_Filename'
fields = fold_path, db_path

# start tkinter and give the window a title
root = tk.Tk()
root.title("Config Setup")

# setup the variables to store the output into using the dialogue
filename = tk.StringVar()
dirname = tk.StringVar()
simple_identity = tk.IntVar()

# assume config wont exist, check to see if it is found
configName = 'Local_Config.csv'
config, found = configFunc.check_for_config(configName)

# try to set defaults for the dialogue window. Moved to outside the loop as having a default initiation for each
# variable starts to get messy and conditions for config file not being found would be more complicated
try:
    default_foldpath = config[fold_path]
    dirname.set(default_foldpath)
except:
    default_foldpath = "No folder selected"
try:
    default_dbpath = config[db_path] + config[db_name]
    filename.set(default_dbpath)
except:
    default_dbpath = "No file selected"


def ask_user_file_or_dir(request):
    # ask for the directory that holds the pdfs
    if request == 'file':
        # adding filetypes allows the choose dialogue to filter for certain types of extensions
        output = tk.filedialog.askopenfilename(initialdir="/", title="Select database file (Excel)",
                                               filetypes=(("Excel Files", "*.xl;*.xlsx;*.xlsm"), ("All Files", "*.*")))
        file_label.config(text=output)
        filename.set(output)
    elif request == 'dir':
        output = tk.filedialog.askdirectory(title="Select folder containing PDFs")
        folder_label.config(text=output)
        dirname.set(output)
    else:
        print("Input should be 'file' or 'dir'")
        output = 'None'
    return output


# have to use a lambda function on the command line in order to make sure the button can activate anytime the user
# presses the button. If lambda isnt used, it will instantly run and then button will do nothing
# anchor allows you to use a cardinal direction to align to (N/NW/NE/S/SW/SE/E/W/CENTER)
# width allows you to specify the elements overall width as a hard number to alleviate padding necessity
file_button = tk.Button(root, text="Browse for file", command=lambda: ask_user_file_or_dir('file'),
                        anchor="center", width=15)
file_label = tk.Label(root, text=default_dbpath, anchor="w", width=70)

folder_button = tk.Button(root, text="Browse for folder", command=lambda: ask_user_file_or_dir('dir'),
                          anchor="center", width=15)
folder_label = tk.Label(root, text=default_foldpath, anchor="w", width=70)

identification_checkbox = tk.Checkbutton(root, text='Simplify Names', variable=simple_identity,
                                         anchor="w", width=70)

done_button = tk.Button(root, text="Ok", command=root.quit, width=5)
cancel_button = tk.Button(root, text="Cancel", command=root.destroy, width=8)

file_button.grid(row=0, column=2, padx=(10, 10), pady=(10, 0))
file_label.grid(row=0, column=0, padx=(10, 20), pady=(10, 0))
folder_button.grid(row=1, column=2, padx=(10, 10), pady=5)
folder_label.grid(row=1, column=0, padx=(10, 20), pady=5)
identification_checkbox.grid(row=2, column=0, padx=(10, 0))
done_button.grid(row=2, column=1, pady=5)
cancel_button.grid(row=2, column=2)

tk.mainloop()

folder_name = formatFunc.extract_after_last_character(dirname.get(), '/')
config['Foldername'] = folder_name
config[fold_path] = dirname.get()

file = filename.get()
datafilename = formatFunc.extract_after_last_character(file, '/')
config[db_name] = datafilename
config[db_path] = formatFunc.left(file, len(file) - len(datafilename))

config['Simplify_Names'] = simple_identity.get()

print(config)
os.chdir(cwd)
configFunc.save_config(configName, config)
