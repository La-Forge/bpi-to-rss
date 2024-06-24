#!/bin/bash

source .venv/bin/activate

pip install --upgrade pip

pip install -r requirements.txt

python3 generate_feeds.py

deactivate
