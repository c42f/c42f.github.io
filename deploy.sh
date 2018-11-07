#!/usr/bin/env bash
DEPLOY_BRANCH=master
TARGET_REPO=c42f/c42f.github.io.git
PELICAN_OUTPUT_FOLDER=output

# On Travis this script needs a deploy key to restrict access to this one repo.
# To generate and use such a key, see
# https://gist.github.com/qoomon/c57b0dc866221d91704ffef25d41adcf

set -u
set -o pipefail

if [ "$TRAVIS_PULL_REQUEST" == "false" ]; then
    echo -e "Starting to deploy to Github Pages\n"
    if [ "$TRAVIS" == "true" ]; then
        git config --global user.email "travis@travis-ci.org"
        git config --global user.name "Travis"
    fi
    src_commit=$(git rev-parse --verify HEAD)
    # Using deploy key, clone the deploy branch
    git clone --quiet --branch=$DEPLOY_BRANCH git@github.com:$TARGET_REPO built_website > /dev/null
    #go into directory and copy data we're interested in to that directory
    cd built_website
    rsync -rv --exclude=.git  ../$PELICAN_OUTPUT_FOLDER/* .
    #add, commit and push files
    git add -f .
    git commit -m "Travis build $TRAVIS_BUILD_NUMBER pushed to Github Pages (src: $src_commit)"
    git push -fq origin $DEPLOY_BRANCH > /dev/null
    echo -e "Deploy completed\n"
fi
