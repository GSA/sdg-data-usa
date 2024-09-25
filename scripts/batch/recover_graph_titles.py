import sdg
import os
import yaml

"""
This is a one-time script to recover some US-specific config.
"""

# Get the metadata for an indicator.
def get_metadata(filepath):
    with open(filepath, 'r') as stream:
        try:
            for doc in yaml.safe_load_all(stream):
                if hasattr(doc, 'items'):
                    return doc
        except yaml.YAMLError as e:
            print(e)

def write_config(filepath, metadata):
    yaml_string = yaml.dump(metadata,
        allow_unicode=True)
    with open(filepath, 'w') as outfile:
        outfile.write(yaml_string)

def write_metadata(filepath, metadata):
    yaml_string = yaml.dump(metadata,
        default_flow_style=False,
        explicit_start=True,
        explicit_end=True,
        allow_unicode=True)
    with open(filepath, 'w') as outfile:
        outfile.write(yaml_string.replace("\n...\n", "\n---\n"))


ids = sdg.path.get_ids()
for inid in ids:
    old_meta_filepath = os.path.join('..', 'sdg-data-usa', 'meta', inid + '.md')
    new_meta_filepath = os.path.join('meta', inid + '.md')
    config_filepath = os.path.join('indicator-config', inid + '.yml')
    if os.path.isfile(new_meta_filepath) and os.path.isfile(config_filepath):
        new_meta = get_metadata(new_meta_filepath)
        old_meta = get_metadata(old_meta_filepath)
        config = get_metadata(config_filepath)
        graph_title = old_meta['graph_title'] if 'graph_title' in old_meta else None
        indicator_name = old_meta['indicator_name'] if 'indicator_name' in old_meta else None
        if indicator_name == graph_title:
            graph_title = None
        actual_indicator = new_meta['actual_indicator_available'] if 'actual_indicator_available' in new_meta else None
        if actual_indicator != '' and actual_indicator is not None:
            if graph_title is None:
                graph_title = actual_indicator
            config['indicator_available'] = actual_indicator
            if 'actual_indicator_availablel' in new_meta:
                del new_meta['actual_indicator_available']
            new_meta['SDG_INDICATOR'] = actual_indicator
        if graph_title is not None:
            config['graph_title'] = graph_title
        if 'source_organisation_1' in new_meta and new_meta['source_organisation_1'] != '' and new_meta['source_organisation_1'] is not None:
            new_meta['CONTACT_ORGANISATION'] = new_meta['source_organisation_1']
        if 'computation_units' in new_meta and new_meta['computation_units'] != '' and new_meta['computation_units'] is not None:
            new_meta['UNIT_MEASURE'] = new_meta['computation_units']
            del new_meta['computation_units']
        
        SOURCE_TYPE = ''
        if 'source_agency_survey_dataset_1' in new_meta and new_meta['source_agency_survey_dataset_1'] != '':
            SOURCE_TYPE = new_meta['source_agency_survey_dataset_1']
        source_url_1 = ''
        if 'source_url_1' in new_meta and new_meta['source_url_1'] != '':
            source_url_1 = new_meta['source_url_1']
        if SOURCE_TYPE != '' and source_url_1 != '' and source_url_1 is not None:
            SOURCE_TYPE = SOURCE_TYPE + " - " + source_url_1
        elif source_url_1 != '' and source_url_1 is not None:
            SOURCE_TYPE = source_url_1
        if SOURCE_TYPE != '' and SOURCE_TYPE is not None:
            new_meta['SOURCE_TYPE'] = SOURCE_TYPE
        
        new_meta['DATA_SOURCE'] = new_meta['source_agency_staff_name_1'] if 'source_agency_staff_name_1' in new_meta and new_meta['source_agency_staff_name_1'] is not None else ''
        new_meta['REC_USE_LIM'] = new_meta['comments_and_limitations'] if 'comments_and_limitations' in new_meta and new_meta['comments_and_limitations'] is not None else ''
        new_meta['DATA_COMP'] = new_meta['us_method_of_computation'] if 'us_method_of_computation' in new_meta and new_meta['us_method_of_computation'] is not None else ''
        if new_meta['DATA_COMP'] == '':
            new_meta['DATA_COMP'] = new_meta['method_of_computation'] if 'method_of_computation' in new_meta and new_meta['method_of_computation'] is not None else ''

        write_config(config_filepath, config)
        write_metadata(new_meta_filepath, new_meta)
