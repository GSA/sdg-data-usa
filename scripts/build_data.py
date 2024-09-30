from sdg.open_sdg import open_sdg_build
from alterations import alter_meta
from alterations import alter_data

open_sdg_build(config='config_data.yml', alter_meta=alter_meta, alter_data=alter_data)
