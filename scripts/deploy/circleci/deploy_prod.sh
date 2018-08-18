#!/usr/bin/env bash
git config --global user.email $GH_EMAIL
git config --global user.name $GH_NAME

git clone git@gh-prod:$GH_ORG_PROD/sdg-data-usa.git out

cd out
git checkout master || git checkout --orphan master
git rm -rfq .
cd ..

# The fully built site is already available at /tmp/build.
cp -a /tmp/build/_site/. out/.

mkdir -p out/.circleci && cp -a .circleci/. out/.circleci/.
cd out

git add -A
git commit -m "Automated deployment to GitHub Pages: ${CIRCLE_SHA1}" --allow-empty

git push origin master