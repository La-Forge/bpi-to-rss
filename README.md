# bpi-to-rss

## installation

1. clone the git repository

```sh
git clone git@github.com:La-Forge/bpi-to-rss.git
```

2. create a virtual env and install the libs

```sh
python -m  venv .venv && source .venv/bin/activate 
pip install --upgrade pip # if necessary
pip install -r requirements.txt
```

## launch the web service

Either launch it manually:

```sh
python3 generate_feeds.py
python3 serve_feeds.py 8000
```

or use the `generate_feeds.sh` script to generate the feeds every hour, which can be put in a crontab if necessary : `0 * * * * {path_to_file}`

```sh
sh ./generate_feeds.sh
sh ./start_service.sh
```


