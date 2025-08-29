#!/bin/bash

# cd to the directory of this file
cd $(dirname "$0")

# update dependencies
uv sync

# generate the RSS feeds
uv run python3 generate_feeds.py