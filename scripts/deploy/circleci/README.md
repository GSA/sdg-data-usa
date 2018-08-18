# CircleCI deployment scripts

This set of scripts supports testing/deployment through CircleCI.

## Assumptions/definitions

These steps assume you have set up 2 Github.com accounts (organisations):

1. The staging organisation: All development/changes will happen here.
1. The production organisation: Only automated deployments will happen here.

## Deployment keys

You'll need to create some SSH keys for deployment. Here are some commands to accomplish this on the command line:
```
mkdir ~/sdg-data-keys
cd ~/sdg-data-keys
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
[for file name, enter "sdg-data-stg", and for passphrase just press Enter]
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
[for file name, enter "sdg-data-prod", and for passphrase just press Enter]
```
This should give you 2 SSH key pairs:
* sdg-data-keys/sdg-data-stg
* sdg-data-keys/sdg-data-stg.pub
* sdg-data-keys/sdg-data-prod
* sdg-data-keys/sdg-data-prod.pub

### Installing keys on Github

1. Login to Github.com as your staging organisation.
1. Go to the "Deploy keys" page, for example:
   https://github.com/[YOUR-ORGANISATION]/sdg-data/settings/keys
1. Click "Add deploy key"
1. Give it any Title you'd like, and paste in the contents of sdg-data-stg.pub

Now we'll repeat for your production organisation.

1. Login to Github.com as your production organisation.
1. Go to the "Deploy keys" page, for example:
   https://github.com/[YOUR_ORGANISATION]/sdg-data/settings/keys
1. Click "Add deploy key"
1. Give it any Title you'd like, and paste in the contents of sdg-data-prod.pub

### Installing the keys on CircleCI

1. Log into Github.com as your staging organisation.
1. In the same browser, go to [CircleCI](https://circleci.com/vcs-authorize/)
   and click "Log in with GitHub".
1. Make sure you see your staging organisation in the top-left dropdown.
1. Click on "Add Projects".
1. Across from "sdg-data" click "Setup project".
1. Leave everything as-is, scroll down and click "Start building".
   (You may see tests attempt to run and fail - this is expected.)
1. Go to the "SSH Permissions" page, for example:
   https://circleci.com/gh/[YOUR_ORGANISATION/sdg-data/edit#ssh

IMPORTANT: For the following the steps, the "Hostname" should be copied exactly!

1. Click "Add SSH Key"
1. Enter a hostname of `gh-stg`
1. Copy into "Private key" the contents of sdg-data-stg.
1. Click "Add SSH Key"
1. Enter a hostname of `gh-prod`
1. Copy into "Private key" the contents of sdg-data-prod.

### Updating the SSH key fingerprints

One last step! You should now see 2 "fingerprints" (you may need to refresh). You'll be copying those into a versioned file in this repository.

1. Open the .circleci/config.yml file.
2. Look for the "fingerprints" entry under "deploy_staging", and replace its value with the fingerprint for `gh-stg`.
3. Look for the "fingerprints" entry under "deploy_prod", and replace its value with the fingerprint for `gh-prod`.

## What have we done?

At this point, the following workflow is in-place for your staging organisation:

* Whenever a pull-request is created for the sdg-data repository, CircleCI will automatically run the "test" jobs, which validate data and metadata.
* Whenever a pull-request is merged into the `develop` branch, CircleCI will automatically deploy the build to the staging site: https://[YOUR_STG_ORGANISATION].github.io/sdg-data.
* Whenever a pull-request is merged into the `master` branch, CircleCI will automatically deploy the build to the production site: https://[YOUR_PROD_ORGANISATION].github.io/sdg-data.