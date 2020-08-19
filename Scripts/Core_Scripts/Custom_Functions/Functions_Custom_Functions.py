from pdfrw import PdfReader
import Core_Scripts.Custom_Functions.Functions_Formatting_Data as formatFunctions
from Core_Scripts.Custom_Functions.Functions_General import *
from Core_Scripts.Custom_Functions.Functions_Lists import count_occurences_in_list
import requests
import io


def pdf_get_data_as_string(annotdata, stringlist):
    # annotdata is the extracted information of the pdf, and a single annotation, after the data has been extracted
    # using pdfrw
    # #datastring is a string of the target data (with / included) Example:
    # from pdfrw import PdfReader
    # pdf = PdfReader(filename)
    # firstlevel = pdf.Root.Pages.Kids
    # unpack_first = firstlevel[0]
    # annotation_holder = unpack_first.Annots
    output = []
    # for each attribute of interest in stringlist, extract and remove extra parenthesis from the data. Store in a list
    for attr in stringlist:
        extractedstring = annotdata[attr]
        finalval = formatFunctions.remove_characters(extractedstring, ["(", ')'])
        output.append(finalval)
    return output


def extract_from_pdf(file, stringlist, ignore_string=None, remove=False, is_URL=False):
    # try:
    # when the user provides a download URL, run a different method
    if is_URL:
        # the file is actually a dictionary of data for a file in the case of the URL version
        # below is specific to extracting from bluebeam API
        # this may error if run on a link that isnt generated on the spot (10minute expiration for URL from studio)
        filename = file['Name']
        downloadURL = file['DownloadUrl']
        getfile = requests.get(downloadURL)
        getdata = io.BytesIO(getfile.content)
        pdf = PdfReader(getdata)
    else:
        pdf = PdfReader(file)
        filename = file
    # Recommended to find out the hierarchy of the pdf to figure out the structure (PDFXplorer is a good one)
    firstlevel = pdf.Root.Pages.Kids
    unpackfirst = firstlevel[0]

    annotation_holder = unpackfirst.Annots

    # extract the data specified below
    try:
        stringmtx = []  # to not have to interact with a dataframe more than needed
        if annotation_holder is None:
            extralevel = unpackfirst.Kids[0]
            annotation_holder = extralevel.Annots
    except TypeError:
        pass
    # except:
    #     annotation_holder = 'Error'

    # if a repeat fails, pdf has nothing on it
    if annotation_holder is None:
        stringmtx = set_row_nones(stringlist, 'None')
        # necessary due to how dataframe is built from a list of strings (brackets have to encase the list)
        df = pd.DataFrame([stringmtx], columns=stringlist)
    elif annotation_holder == 'Error':
        stringmtx = set_row_nones(stringlist, 'Errors')
        # necessary due to how dataframe is built from a list of strings (brackets have to encase the list)
        df = pd.DataFrame([stringmtx], columns=stringlist)
    else:
        for annotdata in annotation_holder:
            # extract the data (specified by stringlist) from a specific annotation on the page
            extracted_data = pdf_get_data_as_string(annotdata, stringlist)
            # check if the data extracted is set to be ignored
            stringcheck = check_string_for_match(ignore_string, extracted_data)
            if len(annotation_holder) == 1 and stringcheck:
                extracted = set_row_nones(stringlist, 'None')
                stringmtx.append(extracted)
            elif remove and stringcheck:
                pass
            elif (ignore_string is not None) and stringcheck:
                extracted = set_row_nones(stringlist, 'None')
                stringmtx.append(extracted)
            else:
                extracted = extracted_data
                stringmtx.append(extracted)
        df = pd.DataFrame(stringmtx, columns=stringlist)

    df['Filename'] = filename  # add filename to know what comes from where
    return df


def get_pdf_date_data(file, attributes, is_URL=False):
    # specific function to return a processed string of data
    # get the pdf data, and get the attributes extracted. Use the category attribute provided to get the data of
    # interest
    # when the user provides a download URL, run a different method
    if is_URL:
        # the file is actually a dictionary of data for a file in the case of the URL version
        # below is specific to extracting from bluebeam API
        # this may error if run on a link that isnt generated on the spot (10minute expiration for URL from studio)
        filename = file['Name']
        downloadURL = file['DownloadUrl']
        getfile = requests.get(downloadURL)
        getdata = io.BytesIO(getfile.content)
        pdf = PdfReader(getdata)
    else:
        pdf = PdfReader(file)
        filename = file
    data = pdf.Info
    # check if the attributes provided is a single element or a list, next step assumes a list was given
    if type(attributes) is not list:
        attributes = [attributes]
    # for each attribute provided, extract from dictionary (cant extract multiple values it seems?)
    catdata = [data[att] for att in attributes]

    removestrings = ["(", ')', 'D:']
    # remove anything past the dash in the provided date, then remove the extra characters that arent date related
    cleandates = [formatFunctions.remove_characters(formatFunctions.extract_before_character(catele, ["-", "+"]), removestrings) for catele in catdata]

    # format the date into a more readable format
    dates_list = [formatFunctions.evaluate_date(date_ele) for date_ele in cleandates]

    # create dataframe from date data and add filename to the list to identify file source
    # nesting the list in a list for input is necessary to properly create the dataframe
    # (probably?) needs a list for each row you want to make in order to map columns correctly
    date_df = pd.DataFrame([dates_list], columns=attributes)
    date_df['Filename'] = filename
    return date_df


def extract_base_pdf_data(filename):
    columnlist = ['/CreationDate', '/ModDate']
    stringmtx = []
    for val in columnlist:
        value = get_pdf_date_data(filename, val)
        stringmtx.append(formatFunctions.evaluate_date(value))
    # print(stringmtx)
    df = pd.DataFrame([stringmtx], columns=columnlist)
    df['Filename'] = filename  # add filename to know what comes from where
    return df


def last_markup_addition(column_identifier, df_pdf_data, df_markupdata, newcolumnname):
    # inputs are: string for column as identifier, df of pdf data, df of markup data,
    # find out who the latest one to add markups was
    pdfdata = df_pdf_data[column_identifier]
    date = '/CreationDate'
    authors = '/T'
    markup_columns = [column_identifier, date, authors]
    markupdata = df_markupdata[markup_columns]
    latest_author_list = []
    for filecheck in pdfdata:
        datafiltered = markupdata[markupdata[column_identifier] == filecheck]
        dates_list = datafiltered[date].tolist()
        # changing to just a max should work in this case (assumes the list is always datetimes which should be safe)
        # if the max dates list fails, means there are no markups (ValueError), should fill with none
        try:
            latestdate = max(dates_list)
            latestrow = datafiltered[datafiltered[date] == latestdate]
            latest_author_name = latestrow.iloc[0][authors]
            latest_author_list.append(latest_author_name)
        except ValueError:
            latest_author_list.append('None')
    df_pdf_data[newcolumnname] = latest_author_list
    return df_pdf_data


def identify_stamps_by_team(column_as_id, df_pdfdata, df_markupdata, engineer_team_list, bim_team_list,
                            category='/Subtype', search_for='/Stamp', authorcolumn='/T', markupcount_col='MarkupCount',
                            content_col='/Subj'):
    # inputs are: column as id (both dataframes need to have matching column name), main dataframe (uniques),
    # secondary dataframe (duplicates and countable objects), list of engineers, list of bim
    # optional - category/column to search for (e.g., search column '/Subtype' for all '/Stamp'
    stampcolumn = 'StampedBy'
    stamptypecolumn = 'Eng_Stamp_Type'
    df_pdfdata[stampcolumn] = 'None'
    df_pdfdata[stamptypecolumn] = 'N/A'
    for eachfile in df_pdfdata[column_as_id]:
        # get the index of the filename from pdf data (just as precaution)
        pdffileindex = df_pdfdata[df_pdfdata[column_as_id] == eachfile].index
        # isolate markups only for the file being checked
        markups = df_markupdata[df_markupdata[column_as_id] == eachfile]
        # further isolate to get only the category and the certain type to look for
        findstamps = markups[markups[category] == search_for]
        # hardcoded column for names (just need first and last name to match the team format)
        stamp_authors = findstamps[authorcolumn]
        # alter conditional to use two lines because we want to use the count later
        engstamps = count_occurences_in_list(engineer_team_list, stamp_authors)
        bimstamps = count_occurences_in_list(bim_team_list, stamp_authors)
        eng_stamped = engstamps > 0
        bim_stamped = bimstamps > 0
        if eng_stamped and bim_stamped:
            stamp_note = 'Both'
        elif eng_stamped and not bim_stamped:
            stamp_note = 'Engineer'
        elif bim_stamped:
            stamp_note = 'BIM'
        else:
            stamp_note = 'None'
        # df.ix[row, column] allows you to replace the value with a new one (similar to matlab)
        df_pdfdata.ix[pdffileindex, stampcolumn] = stamp_note

        # adjust the markup count to remove counts of stamps (get the current markups, remove the eng stamp count,
        # because bim markup count has already been filtered out of the counter)
        df_pdfdata.ix[pdffileindex, markupcount_col] = df_pdfdata.ix[pdffileindex, markupcount_col] - engstamps

        # in the findstamps dataframe, get the stamps corresponding to an engineer, then get the list of all those
        # stamp subj (stamp names such as completed, reviewed, etc), and convert to a list where applicable. get the
        # last stamp name and add to pdfdata
        if eng_stamped:
            stamptypes = findstamps[findstamps['FromTeam'] == 'ENG'][content_col].tolist()
            if len(stamptypes) > 1:
                # join using comma in case there is more than one stamp used by a single engineer
                save_string = ','.join(stamptypes)
            else:
                save_string = str(stamptypes[0])
            df_pdfdata.ix[pdffileindex, stamptypecolumn] = save_string
    return df_pdfdata


def count_total_markups(column_as_id, df_markupdata, df_pdfdata, newcolumname, eng_list, authorcolumn='/T'):
    df_pdfdata[newcolumname] = 0
    filenames = df_pdfdata[column_as_id]

    for eachfile in filenames:
        # get the index of the filename from pdf data (just as precaution)
        pdffileindex = df_pdfdata[df_pdfdata[column_as_id] == eachfile].index
        # isolate the markup rows that are relevant to the current file being checked
        filemarkups = df_markupdata[df_markupdata[column_as_id] == eachfile]
        # isolate the author names per markup (hard codes column names here)
        markupauthors = filemarkups[authorcolumn]
        # count occurrences from Misc_Data_Functions module
        markuptotals = count_occurences_in_list(eng_list, markupauthors)
        # replace the value accordingly
        df_pdfdata.ix[pdffileindex, newcolumname] = markuptotals
    return df_pdfdata


def identify_if_latest(df, dwgnum_column, uniques_column, datecomparison_column, newcolumnname='Latest'):
    # find the latest row (in this context file) from a list of files that can have matching identifiers
    dataframe = df.sort_values(by=uniques_column)
    dataframe.reset_index(drop=True, inplace=True)

    groupednumber = dataframe.groupby(by=dataframe[dwgnum_column])
    groupmaxval = groupednumber[datecomparison_column].agg(max)

    dwgnums = dataframe[dwgnum_column]
    dates = dataframe[datecomparison_column]
    latestlist = []
    # since both dates and dwgnums are the same size, enumerate allows us to index from both
    for i, drawing_date in enumerate(dates):
        checkdrawing = dwgnums[i]
        checkdate = groupmaxval[checkdrawing]
        if checkdate == drawing_date:
            latestlist.append('Yes')
        else:
            latestlist.append('No')
    dataframe[newcolumnname] = latestlist
    return dataframe


def determine_completion_times(markup_df, file_df, parameterlist,
                               subtype_filter='/Stamp', file_df_column='Filename',
                               searchfor=['ENG', 'BIM'], columns_exist=False):
    # separating with commas allows multi-assigns in one-line to reduce excessive clutter and necessity for many lines
    # setup the main column references in order input, as well as other variables from input
    subtype, creationdate, authorcolumn = parameterlist[0], parameterlist[1], parameterlist[2]
    filtered_df_data = markup_df[markup_df[subtype] == subtype_filter]
    eng_tag = searchfor[0]
    bim_tag = searchfor[1]
    # simplified filtered list
    filtered_df_data = filtered_df_data[parameterlist]

    # setup/edit of new columns added to pdf, if columns dont already exist
    engineer_revised, bim_completed, completetime = ['Engineer_Revised', 'BIM_Completed', 'Complete_Time']
    completion_time = [engineer_revised, bim_completed, completetime]
    if not columns_exist:
        fillvalues = ['01-01-01 0:0:0', '01-01-01 0:0:0', '0:0:0']
        for i, header in enumerate(completion_time):
            file_df[header] = fillvalues[i]

    # evaluate completion data from the stamp data for each file
    for eachfile in file_df[file_df_column]:
        # get only the rows that correspond to the specific file being checked
        stamps_in_file = filtered_df_data[filtered_df_data[file_df_column] == eachfile]
        # if there is a stamp in the file being checked, move on, otherwise move to next file
        if len(stamps_in_file) > 0:
            # identify the index where the match was found (should only be single result, as each file should be unique)
            fileindex = file_df[file_df[file_df_column] == eachfile].index
            # get the row where an engineer/bim was found using a filter for author column
            foundeng = stamps_in_file[stamps_in_file[authorcolumn] == eng_tag]
            foundbim = stamps_in_file[stamps_in_file[authorcolumn] == bim_tag]

            # check if complete by checking both founds for a value inside
            # (logic here maybe should be slightly adjusted? can probably be optimized a bit better)
            if len(foundeng) > 0 and len(foundbim) > 0:
                # need to check here in case stamps are added after the bim stamp (in case of backcheck stamp usage)
                engdates = list(foundeng[creationdate])
                checknegatives = True
                # might be more than once this occurs so a while loop may be needed to sort it out
                while checknegatives:
                    latestengstamp = max(engdates)
                    bimdate = max(foundbim[creationdate])
                    if latestengstamp > bimdate:
                        # .remove method will get the element out of the list, and the loop will reset to try again
                        engdates.remove(latestengstamp)
                    else:
                        #  this will stop the loop from trying again
                        checknegatives = False
                time_to_complete = bimdate - latestengstamp
                # index back into the file_df to replace values there with the new calculations
                # df.ix[row, column] allows you to input a value into a specific cell within the dataframe
                file_df.ix[fileindex, completion_time] = [latestengstamp, bimdate, str(time_to_complete)]
            # check if the stamp found was an engineer one only (uncompleted drawing)
            elif len(foundeng) > 0:
                latestengstamp = max(foundeng[creationdate])
                file_df.ix[fileindex, engineer_revised] = latestengstamp
    return file_df


def simplify_author_names(authors, prefix_map, delimiter=' '):
    # assumes dictionary for prefix map and authors as a list
    short_names = []
    for eachauthor in authors:
        # use uppers for simplicity
        initials = formatFunctions.get_all_first_characters([eachauthor.upper()], delimiter)
        # if the name is not found in the prefix map, prefix addition has to be ignored
        # initials comes out as a list because the function built assuming an input of a list, indexing
        # the 0th element will convert back into a string
        try:
            category = prefix_map[eachauthor.upper()]
            short_names.append(category + '-' + initials[0])
        except KeyError:
            short_names.append(initials[0])
    return short_names
