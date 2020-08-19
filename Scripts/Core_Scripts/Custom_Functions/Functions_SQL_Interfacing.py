import os
import pandas as pd
import mysql.connector

pd.options.display.width = None


def save_to_SQL(connection, table, table_column_names_list, dataframe, delete_syntax_condition=''):
    # the connection assumed is using mysql.connector library
    my_cursor = connection.cursor()
    # this will join the list of strings into a single string for inputting into the sql syntax
    # the join method onto a string uses the string as the delimiter for the list of elements
    sqlDB_column_names = ', '.join(table_column_names_list)

    # optional to run an extra condition before the insertion of the data using
    # SQL statement before the insert statement for the data
    if delete_syntax_condition != '':
        my_cursor.execute(delete_syntax_condition)

    sql_syntax = "INSERT into " + table + " (" + sqlDB_column_names + ") VALUES \n"
    # accept a list as input in certain cases would be beneficial. The syntax is different for strings
    if type(dataframe) is list:
        # -have to replace single quotes with double so that its read properly as a quote within the string
        # -same principle for the backslash, a backslash represents specific types of characters,
        # flip to forward slash for simplicity. backslash might be representing italics
        # -chaining two replaces back to back allows for replacing two different types of characters in one line
        row_as_string = ["'" + str(i).replace("'", "''").replace("\\", "/") + "'" for i in dataframe]
        sql_syntax += "(" + ','.join(row_as_string) + ");"
        my_cursor.execute(sql_syntax)
    else:
        # dataframe has to be broken apart and converted to string to be compatible with the sql statements
        for rownumber in range(0, len(dataframe.iloc[:, 0])):
            row_as_string = dataframe.iloc[rownumber].tolist()
            # same principle as for single list element, certain characters have to be converted for mySQL to read
            row_as_string = ["'" + str(i).replace("'", "''").replace("\\", "/") + "'" for i in row_as_string]
            if rownumber < len(dataframe.iloc[:, 0]) - 1:
                sql_syntax += "(" + ','.join(row_as_string) + "),\n"
            else:
                sql_syntax += "(" + ','.join(row_as_string) + ");"
        my_cursor.execute(sql_syntax)

    # commit is necessary to save changes, otherwise nothing occurs
    connection.commit()
    return connection, my_cursor
