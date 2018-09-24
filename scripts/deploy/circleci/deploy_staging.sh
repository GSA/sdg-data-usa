#!/usr/bin/env bash
# This script deploys the built site to the gh-pages branch of the same repo.
git config --global user.email $GH_EMAIL
git config --global user.name $GH_NAME

# CircleCI will identify the SSH key with a "Host" of gh-stg. In order to tell
# Git to use this key, we need to hack the SSH key:
sed -i -e 's/Host gh-stg/Host gh-stg\n  HostName github.com/g' ~/.ssh/config
# Now we can use "gh-stg" below to identify the SSH key to use.
git clone git@gh-stg:$GH_ORG_STG/$CIRCLE_PROJECT_REPONAME.git out

cd out
git checkout gh-pages || git checkout --orphan gh-pages
git rm -rfq .
cd ..

# The fully built site is already available at /tmp/build/_site.
cp -a /tmp/build/_site/. out/.

mkdir -p out/.circleci && cp -a .circleci/. out/.circleci/.
cd out

git add -A
git commit -m "Automated deployment to GitHub Pages: ${CIRCLE_SHA1}" --allow-empty

git push origin gh-pages
