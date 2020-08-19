import csv


def check_for_config(filename, field_list=None):
    config_exist = False
    try:
        print('Looking for config file', filename)
        # get the config file and database name + directory
        with open(filename) as config_file:
            reader = csv.reader(config_file)
            config = dict(reader)
        config_exist = True
        print('Config found')
    # if the config is found, a boolean output signifying it is output
    except:
        config = {}
        print('Config not found')
    return config, config_exist


def save_config(filename, config_as_dict):
    # the new line is necessary due to the below reasons
    # https://stackoverflow.com/questions/3348460/csv-file-written-with-python-has-blank-lines-between-each-row
    with open(filename, 'w', newline='') as config_file:
        writer = csv.writer(config_file)
        for key, value in config_as_dict.items():
            writer.writerow([key, value])
    print('Config file Saved')
