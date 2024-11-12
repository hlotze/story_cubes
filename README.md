# The Story Teller

It is about random generated short-stories in German language; see directory [_./examples_pdf/_](./examples_pdf)

Inspired by [StoryCubes](https://www.storycubes.com/), see a review at "Brettspiele-Magazin: [Story Cubes – Der Geschichten-Generator](https://www.brettspiele-magazin.de/story-cubes/)", this Python script sends random keywords to LLM: _gemma2:27b_ using _Ollama_, requesting a story from some random genres:

>  Abenteuer Action, Biografie, Drama, Fabel, Fantasy, Komödie, Krimi, Mystery, Märchen, Philosophie, Politik, Romantik, Satire, Science-Fiction, Thriller, Tragödie, Western

**_Best, you play [StoryCubes](https://www.storycubes.com/) in real life, with your family and/or friends - it is about fantasy._**

## What it does

the_story_teller.py

1. checks its environment
   - some paths, (it creates them)
     - [_./images/basic/_](./images/basic/)dice_1 .. dice_9/ each dice_n subdir with six (6) images for each dices' site (this is a must to have here)
     - _./stories/_ (it creates them)
     - _./stories/by_Genre/_ (it creates them)
       >  Abenteuer Action, Biografie, Drama, Fabel, Fantasy, Komödie, Krimi, Mystery, Märchen, Philosophie, Politik, Romantik, Satire, Science-Fiction, Thriller, Tragödie, Western
   - existance of (it creates them)
     - _dices.tsv_, (this is a must to have here)
     - _stories.db_, (it creates that)
     - soft-link _./stories/images/_ to _./images/_
     - soft-link _./stories/by_Genre/[genre]/images/_
2. throws nine (9) dices
3. sends the dices' images as keywords, see file _dices.tsv_ (tab separated values) and a request for a story within a random genre
4. to a local installed Ollama using the LLM _gemma2:2b_
5. retrieves the response and stores the dicing, the request and the response into a local Sqlite3 database
6. stores the dicings' images, the request and the response as one Markdown file for each request at directory _./stories/_
7. and provide some soft-links the the sub-folder __./stories/by_Genre/_
8. logging is written to _the_story:_eller.log_

## Prerequisites

1. at least 16 GB RAM, depends on the LLM you choose - as the LLM needs the RAM for operations
2. local installed [Ollama](https://ollama.com/)
3. LLM [_gemma2:2b_](https://huggingface.co/google/gemma-2-2b) installed
    ```Python
    $ ollama run gemma2:2b
    >>> Send a message (/? for help)
    ```
4. Python requirements installed, e.g. with support from [Pipenv: Python Dev Workflow for Humans](https://pipenv.pypa.io/en/latest/)
    ```Python
    import os
    import sys
    import random
    import sqlite3

    from pathlib import Path
    import datetime as dt

    import logging
    import requests

    import pandas as pd
    import numpy as np
    ```

## Operations
1. start your local Ollama (just clicking your desktop icon) and ensure that you have _gemma2:2b_ downloaded
   - to list your install LLMs:
     ```Python
     $ ollama list
     ```
     will show you e.g.:
     ```shell
     $ ollama list
     NAME                       ID              SIZE      MODIFIED
     llama3.2-vision:latest     38107a0cd119    7.9 GB    4 days ago
     llama3.1:latest            42182419e950    4.7 GB    2 weeks ago
     mistral:latest             2ae6f6dd7a3d    4.1 GB    4 months ago
     gemma2:2b                  8ccf136fdd52    1.6 GB    9 days ago 
     ```
   - to install _gemma2:2b_
     ```Python
     $ ollama run gemma2:2b
     ```
2. start _the_story_teller.py_ with
    ```shell
    $ pipenv shell # ensure you have a Pipfile.lock at working-dir
    $ python the_story_teller.py
    ```
    This will give you hints - how to use it:
    ```shell
    $ python the_story_teller.py
    the_story_teller.py

    simmulates 'Story Cubes – Der Geschichten-Generator'
    see: https://www.brettspiele-magazin.de/story-cubes/

    for each short story to generate, it will
        (1) simulate throwing the 9 dices
        (2) generating the request's text (aka content)
        (3) sending the content's prompt to local ollama
        (4) retrieving the answer from ollama
        (5) storing all dicing, requests, answers into local Sqlite3 database './stories.db'
        (6) finally generating a markdown-md-file (see './stories/') to read.
        (7) genrate a symbolic link to the story at './stories/by_Genre/<genre>/'
        (8) logs all it actions at 'story_teller.log'

    usage: python the_story_teller.py <number of stories (min 1, max 10)>'
     e.g.: python the_story_teller.py 1
           python the story_teller.py 10
    ```
3. check _the_story_teller.log_ for processing progress; response generation may take ~60-70 sec.
4. check _stories.db_ e.g. with 
   - VScode plugin e.g. from [Weijan Chen - database-client.com](https://database-client.com/#/home)
     - MYSQL: Database manager for MySQL/MariaDB, PostgreSQL, SQLite, Redis and ElasticSearch
   - [DB Browser for SQLite](https://sqlitebrowser.org) for Windows, Apple Intel, Apple Silicon, Linux

## Notes 

### Watch the LLM working

If you like to observe the LLM, while working on its requests, you should start _Ollama_ from prompt by
```shell
$ ollama serve
```

### Other LLM

You may use any other LLM, but have to change at _the_story_teller.py_:
```Python
def llama(prompt):
    """ send prompt to running ollama service, and get back response within 50 sec (timeout)"""
    url = "http://localhost:11434/api/chat"     # this process "ollama"
                                                # must be started at localhost
                                                # before running the script
    data = {"model"     : "gemma2:2b",         # <---- your changes here <----
            #"model"      : "llama3.1:latest",
            #"model"      : "llama3:70b",
            "messages"   : [{"role" : "user",
                             "content": prompt}],
            "stream"     : False,
            "keep_alive" : "10m",               # keep_alive llama model 10 minutes
           }
    headers = {"Content-Type" : "application/json"}
    ...
    ...
```

### Pipenv

When using _pipenv_ for the Python environment:
see [Pipenv: Python Dev Workflow for Humans](https://pipenv.pypa.io/en/latest/)

use the given _Pipfile_:
```Python
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
#sqlalchemy = "*" # not needed, later for accessing a MySql / Maria database
requests = "*"
pandas = "*"
numpy = "*"

[dev-packages]
#ipykernel = "*"   # not needed, just for IPython Notebooks

[requires]
python_version = "3.12"
```

To enable _pipenv_:
- go to cwd and ```pipenv```will show your options:
```Python
$ pipenv
Usage: pipenv [OPTIONS] COMMAND [ARGS]...

Options:
  --where                         Output project home information.
  --venv                          Output virtualenv information.
  --py                            Output Python interpreter information.
  --envs                          Output Environment Variable options.
  --rm                            Remove the virtualenv.
  --bare                          Minimal output.
  --man                           Display manpage.
  --support                       Output diagnostic information for use in
                                  GitHub issues.
  --site-packages / --no-site-packages
                                  Enable site-packages for the virtualenv.

  --python TEXT                   Specify which version of Python virtualenv
                                  should use.
  --clear                         Clears caches (pipenv, pip).
  -q, --quiet                     Quiet mode.
  -v, --verbose                   Verbose mode.
  --pypi-mirror TEXT              Specify a PyPI mirror.
  --version                       Show the version and exit.
  -h, --help                      Show this message and exit.


Usage Examples:
   Create a new project using Python 3.7, specifically:
   $ pipenv --python 3.7

   Remove project virtualenv (inferred from current directory):
   $ pipenv --rm

   Install all dependencies for a project (including dev):
   $ pipenv install --dev

   Create a lockfile containing pre-releases:
   $ pipenv lock --pre

   Show a graph of your installed dependencies:
   $ pipenv graph

   Check your installed dependencies for security vulnerabilities:
   $ pipenv check

   Install a local setup.py into your virtual environment/Pipfile:
   $ pipenv install -e .

   Use a lower-level pip command:
   $ pipenv run pip freeze

Commands:
  check         Checks for PyUp Safety security vulnerabilities and against
                PEP 508 markers provided in Pipfile.
  clean         Uninstalls all packages not specified in Pipfile.lock.
  graph         Displays currently-installed dependency graph information.
  install       Installs provided packages and adds them to Pipfile, or (if no
                packages are given), installs all packages from Pipfile.
  lock          Generates Pipfile.lock.
  open          View a given module in your editor.
  requirements  Generate a requirements.txt from Pipfile.lock.
  run           Spawns a command installed into the virtualenv.
  scripts       Lists scripts in current environment config.
  shell         Spawns a shell within the virtualenv.
  sync          Installs all packages specified in Pipfile.lock.
  uninstall     Uninstalls a provided package and removes it from Pipfile.
  update        Runs lock, then sync.
  upgrade       Resolves provided packages and adds them to Pipfile, or (if no
                packages are given), merges results to Pipfile.lock
  verify        Verify the hash in Pipfile.lock is up-to-date.
```

You have to generate a _Pipfile.lock_ by: 
```shell
pipenv lock
``` 
and start the environment with 
```shell
$ pipenv shell
```
now you can start the python script with
```shell
$ python the_story_teller.py
```

## Open Items - ToDo's
1. add other command-line options like: 1 story for all genres
2. dockerize with docker-compose
   - Python container with _the_story_teller.py_
   - evtl.: 
     - bind docker volume for access to directory _./stories/_ and the _the_story_teller.log_
     - as a command line service sending all to _stdout_
     - with a nodes- or php-based Web-fontend showing 
       - the dicing
       - the request
       - the response(s)
   - _MySql_ container incl. dedicated _phpmyadmin_ container for database
   - _Ollama_ container with the LLM _gemma2:2b_
   - an application specific _docker network_
