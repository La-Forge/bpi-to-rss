#!/bin/bash

# cd to the directory of this file
cd $(dirname "$0")

# activate the virtual env
source .venv/bin/activate

# generate the RSS feeds
python3 generate_feeds.py

# deactivate the virtual env
deactivate
