import tkinter as tk
from tkinter.filedialog import askdirectory


def get_input_data(entries):
    given_data = []
    for entry in entries:
        text = entry[1].get()
        given_data.append(text)
    return given_data


def makeform(root, fields, fields_exist=False, field_dict=(), entry_padding=0):
    entries = []
    for field in fields:
        row = tk.Frame(root)
        text_label = tk.Label(row, width=15, text=field, anchor='w')
        entry_box = tk.Entry(row)
        # if fields were found, fill the entry boxes with whatever fields can be found
        # this should only trigger if there is at least 1 field found in the config file
        if fields_exist:
            try:
                entry_box.insert(0, field_dict[field])
            except:
                pass
        row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        text_label.pack(side=tk.LEFT)
        entry_box.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X, ipadx=entry_padding)
        entries.append((field, entry_box))
    return entries
