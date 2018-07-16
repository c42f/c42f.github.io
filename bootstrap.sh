#!/bin/bash

# Bootstrap blog development environment.  Requires that conda is installed and
# available to the shell.

conda activate
conda create -n blog
conda activate blog
conda install markdown
pip install pelican
