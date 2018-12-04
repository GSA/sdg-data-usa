# -*- coding: utf-8 -*-
"""
This script makes several tweaks to the metadata to migrate it into the new
platform.

"""

import glob
import os.path
import frontmatter
from urllib.parse import urlparse

# For more readable code below.
FOLDER_META = 'meta'

def is_url(url):
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except ValueError:
    return False

def update_metadata(indicator):

    fields_to_drop = [
        'goal_meta_link_page',
        'graph_status_notes',
        'graph_type_description'
    ]
    fields_with_defaults = {
        'national_geographical_coverage': 'United States'
    }
    fields_to_convert = {
        # Old: New
        'unit_of_measure': 'computation_units'
    }
    fields_to_copy = {
        # Old: New
        'source_agency_survey_dataset': 'source_organisation',
        'source_agency_staff_name': 'source_organisation'
    }
    subnational_indicators = [
        '1.2.1',
        '3.3.1',
        '5.5.2',
        '7.2.1',
        '8.1.1'
    ]

    with open(indicator, 'r') as f:
        post = frontmatter.load(f)

        # Figure out the reporting_status.
        if 'reporting_status' not in post.metadata:
            reporting_status = 'notstarted'
            if 'source_url' in post.metadata and post['source_url'] != None and post['source_url'] != '':
                reporting_status = 'inprogress'
                if 'graph' in post.metadata and post['graph'] != None and post['graph'] != '':
                    reporting_status = 'complete'
            post.metadata['reporting_status'] = reporting_status

        # Make sure it has a published key.
        if 'published' not in post.metadata:
            post.metadata['published'] = False

        # Make sure it has a graph_title key.
        if 'graph_title' not in post.metadata or post['graph_title'] == None or post['graph_title'] == '':
            if 'actual_indicator_available' in post.metadata and post['actual_indicator_available'] != None:
                post.metadata['graph_title'] = post['actual_indicator_available']
            else:
                post.metadata['graph_title'] = post['title']

        # Figure out the graph_type and data_non_statistical.
        data_non_statistical = False
        graph_type = 'line'
        if 'graph' not in post.metadata or post['graph'] == None or post['graph'] == '':
            graph_type = None
            data_non_statistical = True
        elif post['graph'] == 'bar':
            graph_type = 'bar'
        elif post['graph'] == 'binary':
            graph_type = 'binary'
        post.metadata['data_non_statistical'] = data_non_statistical
        post.metadata['graph_type'] = graph_type
        # Clean up the unused variable.
        if 'graph' in post.metadata:
            del post.metadata['graph']

        # Set some defaults.
        for field_with_defaults in fields_with_defaults:
            if field_with_defaults not in post.metadata:
                post.metadata[field_with_defaults] = fields_with_defaults[field_with_defaults]

        # Convert some deprecated fields.
        for field_to_convert in fields_to_convert:
            if field_to_convert in post.metadata:
                converted_field = fields_to_convert[field_to_convert]
                if converted_field not in post.metadata:
                    post.metadata[converted_field] = post.metadata[field_to_convert]
                    del post.metadata[field_to_convert]

        # Copy some platform-required fields.
        for field_to_copy in fields_to_copy:
            if field_to_copy in post.metadata:
                duplicate_field = fields_to_copy[field_to_copy]
                if duplicate_field not in post.metadata:
                    post.metadata[duplicate_field] = post.metadata[field_to_copy]

        # Make sure it has an indicator_sort_order.
        if 'indicator_sort_order' not in post.metadata:
            indicator_parts = post['indicator'].split('.')
            indicator_sort_order = []
            for indicator_part in indicator_parts:
                indicator_sort_order.append(indicator_part.rjust(2, '0'))
            post.metadata['indicator_sort_order'] = '-'.join(indicator_sort_order)

        # Drop certain fields.
        for field_to_drop in fields_to_drop:
            if field_to_drop in post.metadata:
                del post.metadata[field_to_drop]

        # Add subnational data (disabled for now).
        if post.metadata['indicator'] in subnational_indicators:
            post.metadata['data_geocode_regex'] = '.*'
            post.metadata['data_show_map'] = False

        # Convert the source data keys.
        post.metadata['source_active_1'] = True
        fields_to_add = {}
        fields_to_delete = []
        for key in post.metadata:
            if key.startswith('source') and not key.endswith('_1'):
                # Special case of URL fields.
                if key == 'source_url':
                    fields_to_delete.append('source_url')
                    if is_url(post.metadata['source_url']):
                        fields_to_add['source_url_1'] = post.metadata['source_url']
                        fields_to_add['source_url_text_1'] = post.metadata['source_url']
                    else:
                        # Move invalid URLs to the "source_notes" field.
                        fields_to_add['source_notes_1'] = post.metadata['source_url']
                        fields_to_delete.append('source_notes')
                elif key == 'source_notes':
                    # Skip if we already took care of notes.
                    if 'source_notes_1' in fields_to_add:
                        continue
                    else:
                        fields_to_add['source_notes_1'] = post.metadata['source_notes']
                    fields_to_delete.append('source_notes')
                # For other source fields just add a '_1' to the end.
                else:
                    fields_to_add[key + '_1'] = post.metadata[key]
                    fields_to_delete.append(key)
        for key in fields_to_add:
            post.metadata[key] = fields_to_add[key]
        for key in fields_to_delete:
            if key in post.metadata:
                del post.metadata[key]

    with open(indicator, 'w') as f:
        f.write(frontmatter.dumps(post))

    return post

def main():
    """Update all all of the indicators in the metadata folder."""

    status = True

    # Read all the files in the source location.
    indicators = glob.glob(FOLDER_META + "/*.md")
    print("Attempting to update " + str(len(indicators)) + " metadata files...")

    # Compile all the possible metdata keys.
    all_keys = {}

    # Target specific indicators.
    indicators_to_migrate = [
        FOLDER_META + '/' + '8-8-1' + '.md',
        FOLDER_META + '/' + '8-6-1' + '.md',
        FOLDER_META + '/' + '8-5-2' + '.md',
        FOLDER_META + '/' + '8-5-1' + '.md',
        FOLDER_META + '/' + '9-2-2' + '.md',
        FOLDER_META + '/' + '8-2-1' + '.md',
        FOLDER_META + '/' + '5-4-1' + '.md',
    ]
    # Or don't, and just do all indicators.
    indicators_to_migrate = False

    for indicator in indicators:
        if indicators_to_migrate:
            if indicator not in indicators_to_migrate:
                continue

        result = update_metadata(indicator)
        if result:
            for key in result.metadata:
                all_keys[key] = True
        status = status & (result != None)

    #for key in all_keys.keys():
    #    print(key)

    return status

if __name__ == '__main__':
    if not main():
        raise RuntimeError("Failed to migrate metadata")
    else:
        print("Success")