#!/bin/bash
# This hack is needed in order to install/use multiple SSH keys for the same host.
# In this case, the host is github.com. CircleCI installs them all with the same
# "Host" (eg, github.com) and so they can't be distinguished. This script assumes
# they will be named either "gh-stg" or "gh-prod", and adds the "github.com" as a
# HostName setting.
sed -i -e 's/Host gh-stg/Host gh-stg\n  HostName github.com/g' ~/.ssh/config
sed -i -e 's/Host gh-prod/Host gh-prod\n  HostName github.com/g' ~/.ssh/config
