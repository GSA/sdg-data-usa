# -*- coding: utf-8 -*-
"""
This script makes several tweaks to the metadata to migrate it into the new
platform.

"""

import glob
import os.path
import frontmatter

# For more readable code below.
FOLDER_META = 'meta'

def update_metadata(indicator):
    with open(indicator, 'r') as f:
        post = frontmatter.load(f)

        # Figure out the reporting_status.
        if 'reporting_status' not in post.metadata:
            reporting_status = 'notstarted'
            if 'source_url' in post.metadata and post['source_url'] is not None and post['source_url'] is not '':
                reporting_status = 'inprogress'
                if 'graph' in post.metadata and post['graph'] is not None and post['graph'] is not '':
                    reporting_status = 'complete'
            post.metadata['reporting_status'] = reporting_status

        # Make sure it has a published key.
        if 'published' not in post.metadata:
            post.metadata['published'] = False

        # Make sure it has a graph_title key.
        if 'graph_title' not in post.metadata or post['graph_title'] is None or post['graph_title'] is '':
            if 'actual_indicator_available' in post.metadata and post['actual_indicator_available'] is not None:
                post.metadata['graph_title'] = post['actual_indicator_available']
            else:
                post.metadata['graph_title'] = post['title']

        # Figure out the graph_type and data_non_statistical.
        data_non_statistical = False
        graph_type = 'line'
        if 'graph' not in post.metadata or post['graph'] is None or post['graph'] is '':
            graph_type = None
            data_non_statistical = True
        elif post['graph'] is 'bar' or post['graph'] is 'binary':
            graph_type = 'bar'
        post.metadata['data_non_statistical'] = data_non_statistical
        post.metadata['graph_type'] = graph_type

        # Convert the source data keys.
        post.metadata['source_active_1'] = True
        for key in post.metadata:
            if key.startswith('source') and not key.endswith('_1'):
                post.metadata[key + '_1'] = post.metadata[key]
                del post.metadata[key]

        # Make sure it has an indicator_sort_order.
        if 'indicator_sort_order' not in post.metadata:
            indicator_parts = post['indicator'].split('.')
            indicator_sort_order = []
            for indicator_part in indicator_parts:
                indicator_sort_order.append(indicator_part.rjust(2, '0'))
            post.metadata['indicator_sort_order'] = '-'.join(indicator_sort_order)

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

    for indicator in indicators:
        result = update_metadata(indicator)
        if result:
            for key in result.metadata:
                all_keys[key] = True
        status = status & (result is not None)

    #for key in all_keys.keys():
    #    print(key)

    return status

if __name__ == '__main__':
    if not main():
        raise RuntimeError("Failed to migrate metadata")
    else:
        print("Success")