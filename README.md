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
python3 scrapper.py 8000
```

or use the `generate_feeds.sh` script, which can be put in a crontab if necessary

```sh
sh ./generate_feeds.sh
sh ./start_service.sh
```


