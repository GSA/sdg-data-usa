from sdg.open_sdg import open_sdg_check
from alterations import alter_meta
from alterations import alter_data

# Validate the indicators.
validation_successful = open_sdg_check(config='config_data.yml', alter_meta=alter_meta, alter_data=alter_data)

# If everything was valid, perform the build.
if not validation_successful:
    raise Exception('There were validation errors. See output above.')
