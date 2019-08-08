# -*- coding: utf-8 -*-
"""
This script converts the "wide" data in `data-wide` into "tidy" CSVs in `data`.

--------------------------------
Disaggregation naming convention
--------------------------------

While this script can simply create single aggregate series, it also has the
capability of creating any number of disaggregated series. To do this, the
"wide" CSV column headers must follow a strict naming convention. Here are the
rules for that convention:

1. If there is an 'all' column, it is assumed to be the aggregated value for the
   year, and will be what is displayed on the graph by default.

2. Columns to be converted to a disaggregated series must follow this format:

   [category]:[value]

   For example:

   gender:female

3. If a column contains a combination of two or more distinct disaggregations,
   like age and gender, they can be combined with a pipe (|) character, like so:

   [category1]:[value]|[category2]:[value]

   For example:

   gender:female|age:18-64

4. In Open SDG, "Units" is a special disaggregation to be used for units of
   measurement. This can be used in combination with any other dissagregations,
   using the pipe character, as normal. It can also be used in combination with
   the 'all' column, such as in this example of two column headers:

   all|Units:inches,all|Units:feet

   For flexibility and consistency with the all-lowercase naming convention,
   "unit" or "units" will also work.

-----------------------
Handling of legacy data
-----------------------

Historically the US data has allowed any arbitrary column headers, and has used
a metadata field called 'indicator_variable' to decide which column is graphed.
As described above, an alternative to specifying the 'indicator_variable' is to
give the desired column a header of 'all'.

However, to support existing data, if an indicator has no 'all' column, and its
metadata has an 'indicator_variable' value which is an actual column, this
column will be treated as if it were an 'all' column.

Note that if an indicator has no 'all' column, and no valid 'indicator_variable'
columns, AND does not use the naming convention detailed above to produce
disaggregated series, an exception will be raised and the wide-to-tidy conversion
will not complete.

So it is recommended that this script be run as part of a per-pull-request
testing job.
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


def tidy_blank_dataframe():
    """This starts a blank dataframe with our required tidy columns.

    Returns
    -------
    Dataframe
        A blank dataframe ready to receive tidy data.
    """

    # Start with two columns, year and value.
    blank = pd.DataFrame({HEADER_YEAR_WIDE:[], HEADER_VALUE_TIDY:[]})
    # Make sure the year column is typed for integers.
    blank[HEADER_YEAR_WIDE] = blank[HEADER_YEAR_WIDE].astype(int)

    return blank


def tidy_placeholder_dataframe():
    """This returns a placeholder dataframe meant to pass validation.

    Returns
    -------
    Dataframe
        A dataframe with one placeholder row of dummy data.
    """
    placeholder = pd.DataFrame([{
        HEADER_YEAR_TIDY: 2015,
        HEADER_VALUE_TIDY: 0
    }])
    placeholder = placeholder[[HEADER_YEAR_TIDY, HEADER_VALUE_TIDY]]
    return placeholder


def tidy_melt(df, value_var, var_name):
    """This runs a Pandas melt() call with common parameters.

    Paramters
    ---------
    df : Dataframe
        The incoming dataframe
    value_var : string
        TODO: describe this parameter
    var_name : string
        TODO: describe this parameter

    Returns
    -------
    Dataframe
        The incoming dataframe, having been run through pd.melt().
    """

    return pd.melt(
        df,
        id_vars=[HEADER_YEAR_WIDE],
        value_vars=[value_var],
        var_name=var_name,
        value_name=HEADER_VALUE_TIDY)


def get_metadata(csv_filename):
    """This gets metadata for a particular indicator, from YAML in `meta`.

    Parameters
    ----------
    csv_filename : string
        The filename of a CSV data file

    Returns
    -------
    dict
        A dict of key/value metadata pairs
    """
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
    """Make any changes/alterations in the data during the conversion.

    Parameters
    ----------
    df : Dataframe
        The incoming dataframe

    Returns
    -------
    Dataframe
        The incoming dataframe, having had any values altered.
    """
    changes = {
        'yes': 1,
        'no': -1,
        'not_applicable': 0
    }
    df[HEADER_VALUE_TIDY].replace(changes, inplace=True)
    return df


def validate_wide_data(df, metadata, is_placeholder):
    """Validate that the source data meets some minimum requirements.

    The requirements are:
    1. Meets one of the following criteria:
       * Has an 'all' column
       * Has a column matching the 'indicator_variable' metadata field
       * Has a column contains '|' (implying disaggregation)

    Parameters
    ----------
    df : Dataframe
        The dataframe to validate
    metadata : dict
        The metadata fields for this indicator
    is_placeholder : boolean
        Whether or not this is a placeholder CSV file

    Returns
    -------
    boolean
        True or False, depending on whether the input was valid
    """

    if is_placeholder:
        return True

    columns = df.columns.tolist()
    if HEADER_ALL in columns:
        return True

    if 'indicator_variable' in metadata and metadata['indicator_variable'] is not None:
        if metadata['indicator_variable'] in columns:
            return True

    for column in columns:
        if '|' in column:
            return True

    return False


def tidy_dataframe(df, indicator_variable, indicator_id):
    """This converts the data from wide to tidy, based on the column names.

    Parameters
    ----------
    df : Dataframe
        The Pandas dataframe from the "wide" CSV source data
    indicator_variable : string or None
        A specified indicator_variable for this indicator, if any
    indicator_id : string
        The id for this indicator

    Returns
    -------
    Dataframe
        A Pandas dataframe converted into the tidy format
    """

    # Start with our base 2-column (year, value) datafame.
    tidy = tidy_blank_dataframe()
    # Get the columns of the source (wide) dataframe.
    columns = df.columns.tolist()
    # Decide if this indicator has an aggregate series (aka "headline").
    has_headline = False
    # One way to have a headline is if the 'all' column is in the wide CSV.
    if HEADER_ALL in columns:
        has_headline = True
        indicator_variable = HEADER_ALL
    # Another way is if there is an indicator_variable and it is in the wide CSV.
    if not has_headline and indicator_variable is not None and indicator_variable in columns:
        has_headline = True

    # Loop through each column in the CSV file.
    for column in columns:
        if has_headline and column == indicator_variable:
            # If this is the indicator variable, create an aggregate series.
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
                if category_in_column == HEADER_ALL:
                    # Handle the case where the 'all' column has units.
                    # Eg: all|Units:gdp_global, all|Units:gdp_national.
                    # First we "melt" in the Value column.
                    melted = tidy_melt(df, column, HEADER_ALL)
                    # And then immediately remove the 'all' column.
                    del melted[HEADER_ALL]
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

    # Remove rows with no value.
    tidy.dropna(inplace=True, subset=[HEADER_VALUE_TIDY])

    # If we got here, add a dummy row so that validation will pass.
    if len(tidy) == 0:
        return tidy_placeholder_dataframe()

    # Use the tidy year column ('Year') instead of the wide year column ('year').
    tidy = tidy.rename({ HEADER_YEAR_WIDE: HEADER_YEAR_TIDY }, axis='columns')
    # For human readability, move 'year' to the front, and 'value' to the back.
    cols = tidy.columns.tolist()
    cols.pop(cols.index(HEADER_YEAR_TIDY))
    cols.pop(cols.index(HEADER_VALUE_TIDY))
    cols = [HEADER_YEAR_TIDY] + cols + [HEADER_VALUE_TIDY]
    tidy = tidy[cols]

    # Support alternative column names for Units.
    tidy = tidy.rename(axis='columns', mapper={
        'unit': 'Units',
        'units': 'Units'
    })

    # Fix any data issues.
    tidy = fix_data_issues(tidy)

    return tidy

def tidy_csv(csv):
    """This runs all checks and processing on a CSV file and reports exceptions.

    Parameters
    ----------
    csv : string
        Path to the CSV file

    Returns
    -------
    boolean
        True if the tidy CSV was written successfully, False otherwise
    """

    # Get the filename without the .csv.
    csv_filename = os.path.split(csv)[-1]
    # Get the metadata for that indicator.
    metadata = get_metadata(csv_filename)

    try:
        df = pd.read_csv(csv, dtype=str)
    except Exception as e:
        print(csv, e)
        return False

    # Identifiy any placeholders.
    columns = df.columns.tolist()
    is_placeholder = False
    if 'var_1' in columns and 'var_2' in columns and len(df) == 1:
        is_placeholder = True

    # Skip any without rows.
    #if len(df) == 0:
    #    return True

    # Validate the source data before going further.
    valid = validate_wide_data(df, metadata, is_placeholder)
    if not valid:
        raise Exception('Indicator {} failed wide-to-tidy conversion - invalid source data.'.format(metadata['indicator']))

    indicator_variable = None
    if 'indicator_variable' in metadata:
        indicator_variable = metadata['indicator_variable']

    # Allow for some of the current "placeholder" CSV files to work.
    columns = df.columns.tolist()
    if 'var_1' in columns and 'var_2' in columns and len(df) == 1:
       # This is a placeholder file, which we can skip.
        indicator_variable = 'var_1'

    tidy = tidy_dataframe(df, indicator_variable, metadata['indicator'])

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

    for csv in csvs:
        # Process each of the CSVs.
        status = status & tidy_csv(csv)

    return status

if __name__ == '__main__':
    if not main():
        raise RuntimeError("Failed tidy conversion")
    else:
        print("Success")