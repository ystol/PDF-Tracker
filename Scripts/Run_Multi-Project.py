# general imports
import os
import traceback
from datetime import datetime
import csv
# function imports
import Core_Scripts.Custom_Functions.Functions_Configs as configFunc
# extra imports
from shutil import copyfile

# main imports
from Run_Setup_and_Analysis_SQL_DB import run_analysis_mysql


original_config = 'SQL_Config.csv'
new_config_location = 'SQL_Config_multiple.csv'
project_list_file = 'Project_list.csv'
copyfile(original_config, new_config_location)

config = configFunc.check_for_config(new_config_location)[0]
# open the csv, using the csv reader, and then convert into a list (for single column csv)
project_list = list(csv.reader(open(project_list_file)))

# logging = open('script_results.txt', 'w')
# sys.stdout = logging
logfile = open('Logs/errors.txt', "a")
errors = 0
for eachproject in project_list:
    # have to convert the list into its main string object
    print('Run on project:', eachproject[0])
    # adjust the active project
    config['Project'] = eachproject[0]
    # overwrite the config to make function use the altered project without user input
    configFunc.save_config(new_config_location, config)
    try:
        run_analysis_mysql(config_name=new_config_location)
    except Exception as error:
        errors += 1
        rightnow = datetime.now()
        errormessage = '\n' + str(rightnow) + '  --  Project {' + eachproject[0] \
                       + '} threw an exception. Needs review. Check error message below.\n'
        # this writes the basic error message with a time stamp
        logfile.write(str(errormessage))
        # logfile.write(str(error))
        errmsg = traceback.format_exc()
        logfile.write(str(errmsg))
        print(errmsg)

# delete config file after everything is complete
os.remove(new_config_location)
logfile.close()

# flag user somehow to review (has to be adjusted if remote)
if errors > 0:
    print('ERRORS DURING RUNTIME, REVIEW LOG FILE')

