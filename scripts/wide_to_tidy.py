# -*- coding: utf-8 -*-
"""
This script converts the "wide" data in `data-wide` into "tidy" CSVs in `data`.

"""

import glob
import os.path
import pandas as pd
import yaml

# For more readable code below.
HEADER_ALL = 'all'
HEADER_YEAR_WIDE = 'year'
HEADER_YEAR_TIDY = 'Year'
HEADER_VALUE_TIDY = 'Value'
FOLDER_DATA_CSV_TIDY = 'data'
FOLDER_DATA_CSV_WIDE = 'data-wide'
FOLDER_META = 'meta'
FOLDER_DATA_CSV_SUBNATIONAL = 'data-wide/subnational'

# Allows for more human-friendly folder names in the repository.
FOLDER_NAME_CONVERSIONS = {
    'state': 'GeoCode',
}

def tidy_blank_dataframe():
    """This starts a blank dataframe with our required tidy columns."""

    # Start with two columns, year and value.
    blank = pd.DataFrame({HEADER_YEAR_WIDE:[], HEADER_VALUE_TIDY:[]})
    # Make sure the year column is typed for integers.
    blank[HEADER_YEAR_WIDE] = blank[HEADER_YEAR_WIDE].astype(int)

    return blank

def tidy_melt(df, value_var, var_name):
    """This runs a Pandas melt() call with common parameters."""

    return pd.melt(
        df,
        id_vars=[HEADER_YEAR_WIDE],
        value_vars=[value_var],
        var_name=var_name,
        value_name=HEADER_VALUE_TIDY)

def get_metadata(csv_filename):
    """This gets metadata for a particular indicator, from YAML in `meta`."""
    meta_path = os.path.join(FOLDER_META, csv_filename \
        .split('indicator_')[1]                        \
        .split('.csv')[0] + '.md')
    with open(meta_path, 'r') as stream:
        try:
            # Currently the YAML in `meta` has "front matter" and "content",
            # and we only want the "front matter". So we have to get a bit
            # fancy below.
            for doc in yaml.safe_load_all(stream):
                if hasattr(doc, 'items'):
                    return doc
        except yaml.YAMLError as e:
            print(e)

def fix_data_issues(df):
    """Make any changes/alterations in the data during the conversion."""
    changes = {
        'yes': 1,
        'no': -1,
        'not_applicable': 0
    }
    df[HEADER_VALUE_TIDY].replace(changes, inplace=True)
    return df

def tidy_dataframe(df, indicator_variable):
    """This converts the data from wide to tidy, based on the column names."""

    # Start with our base 2-column (year, value) datafame.
    tidy = tidy_blank_dataframe()
    # Get the columns of the source (wide) dataframe.
    columns = df.columns.tolist()
    # If the indicator specifies an 'indicator_variable' that does not actually
    # exist in the CSV, decide what to do.
    if indicator_variable is not None and indicator_variable not in columns:
        # There is the chance that the columns contain Unit versions of the
        # indicator variable, such as: all|Unit:metric, all|Unit:imperial
        indicator_variable_has_units = False
        for column in columns:
            if column.startswith(indicator_variable + '|Unit'):
                indicator_variable_has_units = True
                break
        # We didn't find that special case of an indicator variable with units,
        # then proceed as if the indicator variable is unknown. We will have to
        # guess it below, by assuming it's the first available column.
        if not indicator_variable_has_units:
            indicator_variable = None
    # In some cases we just have to guess at the main column.
    main_column_picked = False
    # Loop through each column in the CSV file.
    for column in columns:
        if indicator_variable is None and column != HEADER_YEAR_WIDE and not main_column_picked:
            # If the indicator doesn't specify an indicator variable, and this
            # is not the Year column, then guess it's the main column.
            main_column_picked = True # Remember that we've guessed already.
            # Here we "melt" or pivot the dataframe so that the column becomes
            # values in the 'Value' column. Here we don't care what the actual
            # column name was, so it gets forgotten.
            melted = tidy_melt(df, column, column)
            # Remove the left-over column.
            del melted[column]
            # Append this on to our "tidy" dataframe.
            tidy = tidy.append(melted)
        elif column == indicator_variable:
            # Otherwise if this is the indicator variable, use this as the main
            # column. This is essentially the same result as above, only here
            # we are not guessing.
            melted = tidy_melt(df, indicator_variable, indicator_variable)
            del melted[indicator_variable]
            tidy = tidy.append(melted)
        elif '|' not in column and ':' in column:
            # Columns matching the pattern 'category:value' get converted into
            # rows where 'category' is set to 'value'.
            category_parts = column.split(':')
            category_name = category_parts[0]
            category_value = category_parts[1]
            # This time the "melt" produces a new column with named according to
            # 'category_name'.
            melted = tidy_melt(df, column, category_name)
            # Immediately populate the new column with values according to
            # 'category_value'.
            melted[category_name] = category_value
            # As before, append it to our growing 'tidy' dataframe.
            tidy = tidy.append(melted)
        elif '|' in column and ':' in column:
            # Columns matching the pattern 'category1:value1|category2:value2'
            # get converted to rows where 'category1' is set to 'value1' and
            # 'category2' is set to 'value2'.
            merged = tidy_blank_dataframe()
            categories_in_column = column.split('|')
            for category_in_column in categories_in_column:
                if category_in_column == indicator_variable:
                    # Handle the case where the 'all' column has units.
                    # Eg: all|unit:gdp_global, all|unit:gdp_national.
                    # First we "melt" in the Value column.
                    melted = tidy_melt(df, column, indicator_variable)
                    # And then immediately remove the indicator_variable column.
                    del melted[indicator_variable]
                    # That's it - we'll now continue looping to get the actual
                    # "Unit" category.
                    merged = melted
                else:
                    category_parts = category_in_column.split(':')
                    category_name = category_parts[0]
                    category_value = category_parts[1]
                    melted = tidy_melt(df, column, category_name)
                    melted[category_name] = category_value
                    merged = merged.merge(melted, on=[HEADER_YEAR_WIDE, HEADER_VALUE_TIDY], how='outer')
            tidy = tidy.append(merged)

    # Use the tidy year column ('Year') instead of the wide year column ('year').
    tidy = tidy.rename({ HEADER_YEAR_WIDE: HEADER_YEAR_TIDY }, axis='columns')
    # For human readability, move 'year' to the front, and 'value' to the back.
    cols = tidy.columns.tolist()
    cols.pop(cols.index(HEADER_YEAR_TIDY))
    cols.pop(cols.index(HEADER_VALUE_TIDY))
    cols = [HEADER_YEAR_TIDY] + cols + [HEADER_VALUE_TIDY]
    tidy = tidy[cols]

    # Fix any data issues.
    tidy = fix_data_issues(tidy)

    # For rows with no value, use 0.
    tidy[HEADER_VALUE_TIDY].fillna(0, inplace=True)

    # If the CSV has no rows, we have to add one to get past data validation.
    if (len(tidy) == 0):
        tidy = tidy.append({HEADER_YEAR_TIDY: 2018, HEADER_VALUE_TIDY: 0}, ignore_index=True)

    return tidy

def tidy_csv_from_subnational_folder(csv, folder_name, subfolder_name):
    """This converts a CSV into a dataframe, tweaks the headers, and returns it."""

    try:
        df = pd.read_csv(csv, dtype=str)
    except Exception as e:
        print(csv, e)
        return False

    # Convert the folder structure into a column according to our syntax rules.
    # For example: state/alabama will turn into 'state:alabama'.
    subfolder_column = folder_name + ':' + subfolder_name

    # Add this to the columns in the dataframe.
    columns = dict()
    for column in df.columns.tolist():
        fixed = column
        if column == HEADER_ALL:
            fixed = subfolder_column
        elif column.startswith(HEADER_ALL + '|'):
            fixed = column.replace(HEADER_ALL + '|', subfolder_column + '|')
        elif column == HEADER_YEAR_WIDE:
            fixed = HEADER_YEAR_WIDE
        else:
            fixed = subfolder_column + '|' + column
        columns[column] = fixed

    return df.rename(columns, axis='columns')

def tidy_csv(csv, subnational_folders):
    """This runs all checks and processing on a CSV file and reports exceptions."""

    # Get the filename without the .csv.
    csv_filename = os.path.split(csv)[-1]
    # Get the metadata for that indicator.
    metadata = get_metadata(csv_filename)

    try:
        df = pd.read_csv(csv, dtype=str)
    except Exception as e:
        print(csv, e)
        return False

    # Look in any subnational folders for a corresponding file.
    for folder in subnational_folders:
        folder_name = os.path.basename(os.path.normpath(folder))
        if folder_name in FOLDER_NAME_CONVERSIONS:
            folder_name = FOLDER_NAME_CONVERSIONS[folder_name]
        for subfolder in subnational_folders[folder]:
            subfolder_name = os.path.basename(os.path.normpath(subfolder))
            if subfolder_name in FOLDER_NAME_CONVERSIONS:
                subfolder_name = FOLDER_NAME_CONVERSIONS[subfolder_name]
            subnational_file = subfolder + csv_filename
            if os.path.isfile(subnational_file):
                dis_df = tidy_csv_from_subnational_folder(subnational_file, folder_name, subfolder_name)
                df = pd.merge(df, dis_df, how='outer', on=HEADER_YEAR_WIDE)

    try:
        tidy = tidy_dataframe(df, metadata['indicator_variable'])
    except Exception as e:
        print(csv, e)
        return False

    try:
        tidy_path = os.path.join(FOLDER_DATA_CSV_TIDY, csv_filename)
        tidy.to_csv(tidy_path, index=False, encoding='utf-8')
        print('Converted ' + csv_filename + ' to tidy format.')
    except Exception as e:
        print(csv, e)
        return False

    return True

def main():
    """Tidy up all of the indicator CSVs in the data folder."""

    status = True

    # Create the place to put the files.
    os.makedirs(FOLDER_DATA_CSV_TIDY, exist_ok=True)
    # Read all the files in the source location.
    csvs = glob.glob(FOLDER_DATA_CSV_WIDE + "/indicator*.csv")
    print("Attempting to tidy " + str(len(csvs)) + " wide CSV files...")

    # Check here to see if there subnational data.
    subnational_folders = dict()
    folders = glob.glob(FOLDER_DATA_CSV_SUBNATIONAL + '/*/')
    for folder in folders:
        subfolders = glob.glob(folder + '/*/')
        if (subfolders):
            subnational_folders[folder] = subfolders

    for csv in csvs:
        # Process each of the CSVs.
        status = status & tidy_csv(csv, subnational_folders)

    return status

if __name__ == '__main__':
    if not main():
        raise RuntimeError("Failed tidy conversion")
    else:
        print("Success")