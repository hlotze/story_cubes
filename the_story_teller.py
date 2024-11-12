"""this script simmulates 'Story Cubes – Der Geschichten-Generator'
see: https://www.brettspiele-magazin.de/story-cubes/
by means of this python script with
(1) throwing the 9 dices
(2) generating the request's text (aka content)
(3) sending the content's prompt to local ollama
(4) retrieving the answer from ollama
(5) storing all dicing, requests, answers into local Sqlite3 database './stories.db'
(6) finally generating a markdown-md-file (see './stories/') to read"""

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


logger = logging.getLogger(__name__)

GENRE_LST = ['Action', 'Abenteuer', 'Biografie', 'Komödie', 'Krimi', \
                'Drama', 'Fabel', 'Fantasy', 'Märchen', 'Mystery', 'Philosophie', \
                'Politik', 'Romantik', 'Satire', 'Science-Fiction', \
                'Thriller', 'Tragödie', 'Western']


##################################################################
# find - will do the job of clearing the './stories/' directories
##################################################################
#
# to move files manually
# use:
#   find ./stories/ \                     # the directory
#   -maxdepth 1 \                         # only that dir
#   \( -name "*.md" -o -name "*.pdf" \) \ # file patterns
#   -exec mv {} ./stories/__old/ \;       # execute move from -> to
#
# to remove all '*.md' and '.pdf' files at "./stories/__old/" manually
# use:
#   find ./stories/__old/ -maxdepth 1 \( -name "*.md" -o -name "*.pdf" \) -delete  \;
#
# to remove all smybolic links at "stories/by_Genre/<genre>/" manually
# use:
#   find ./stories/by_Genre/ \( -name "*.md" -o -name "*.pdf" \) -delete
#
# from command line at 'story_cube/' main-directory
# you may use:  ./tidy_stories.zsh
##################################################################

def get_dices(fn):
    """get the dices data from dices.tsv"""
    return pd.read_csv(fn,
                       sep='\t', # tab-separated
                       header=0,
                       names=('group', 'dice', 'side', 'word', 'jpg'),
                       index_col=False,
                       dtype={'group' : str,
                              'dice'  : np.int16,
                              'site'  : np.int16,
                              'word'  : str,
                              'jpg'   : str})


def check_or_create_paths(paths_to_check):
    """checks or creates the paths give in the list paths_to_check"""
    for path in paths_to_check:
        try:
            if os.path.exists(path):
                # nothing to do
                pass
            else:
                # if missing --> re-create
                os.makedirs(path)
        except FileExistsError:
            # occurs if dir exists --> nothing to do
            pass
        except FileNotFoundError:
            # occurs if parent dir not exists
            # --> should not occurr as checked before
            pass
        except OSError as e:
            print("An OS error occurred with [%s]: [%s]", path, e)
            sys.exit(1)


def check_or_create_symlinks(pointing_to_src_dir, named_dst__dir_lst):
    """check the dirs at named_dst__dir_lst if it is pointing_to_src_dir
    if not, it created that symbolic link and re-cecks it"""
    for path in named_dst__dir_lst:
        try:
            if os.path.exists(path):
                #print(f'{path} exists')
                if os.path.islink(path):
                    #print(f'{path} is symbolic link')
                    pass
            else:
                logger.info('Error: [%s] not exists -> re-create', path)
                # usage:
                #   os.symlink(src, dst, target_is_directory=False, *, dir_fd=None)
                # that means:
                #   create a symbolic link 'pointing to src' --> 'named dst'.
                os.symlink(pointing_to_src_dir, path,   # 'pointing to src' --> 'named dst'
                        target_is_directory=True)
                if os.path.islink(path):
                    logger.info('done: [%s] re-create; is symbolic link', path)
        except FileExistsError:
            # dir exists --> nothing to do
            pass
        except FileNotFoundError:
            # parent dir not exists --> should not occurr
            pass
        except OSError as e:
            print(f"Error: an OS error occurred with {path}: {e}")
            sys.exit(1)


def check_file_existance(file_lst):
    """checks the existance and accessibility of file given in file_lst"""
    # usage:
    #   os.path.isfile(path) method that returns True
    #   if the path is a file or a symlink to a file.
    for fn in file_lst:
        try:
            if os.path.isfile(fn):
                # nothing to do
                pass
            else:
                logger.info("Error: file [%s] not found", fn)
        except FileNotFoundError as e:
            logger.info("Error: file [%s] not found, with [%s]", fn, e)
            sys.exit(1)
        except PermissionError as e:
            logger.info("Error: no access to file [%s], see: [%s]", fn, e)
            sys.exit(1)


def check_or_create_env():
    """check the environment of this script"""

    # check existance of directories
    genre_lst = [f'./stories/by_Genre/{genre}/' for genre in GENRE_LST]
    dices_dir_lst = [f'./images/basic/dice_{ix}/' for ix in range(1, 9+1)]
    paths_to_check = ['./stories/', './stories/by_Genre/'] + genre_lst + dices_dir_lst
    check_or_create_paths(paths_to_check)

    # check smybolic links
    #        sybolic link                      -->  targeting to
    # (1) './stories/images/'                  --> '../backup/images/'
    # (2) './stories/by_Genre/<genre>/images/' --> '../../../backup/images/'

    # (1) - check symbolic links at './stories/images'
    target_path = '../images'
    paths_to_check = ['./stories/images']
    check_or_create_symlinks(target_path, paths_to_check)

    # (2) - check symbolic links at './stories/by_Genre/<genre>/images'
    target_path = '../../../images'
    images_at_genre__lst = [f'./stories/by_Genre/{genre}/images' for genre in GENRE_LST]
    check_or_create_symlinks(target_path, images_at_genre__lst)

    # check file's existance
    #   file: './backup/dices.tsv'
    #   file: dices.tsv
    file_lst = ['dices.tsv']
    check_file_existance(file_lst)

    # files: './images/dice_<1..6>/<motive.jpg>'
    dices_df = get_dices('dices.tsv')
    jpg_fn__lst = [f'./{fn[2:]}' \
                   for fn in dices_df['jpg'].to_list()]
    check_file_existance(jpg_fn__lst)


def store_to_sqlite_db(df, conn):
    """store the pd.DataFrame to Sqlite DB"""
    df.to_sql('dices',
              con=conn,
              if_exists='replace',
              index=False,
              dtype={'group' : 'TEXT',
                     'dice'  : 'INTEGER',
                     'side'  : 'INTEGER',
                     'word'  : 'TEXT',
                     'jpg'   : 'TEXT'})


def do_dicing(conn, cur):
    """(1) do the dicing for 9 dices,
    (2) give back result as dice_result_list of dicts,
    (3) store dicing into table dicing_done"""
    dice_results_list = []
    # get the current timestamp as a request identifier
    curr_ts_str = dt.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    dices = list(range(1,9+1))
    random.shuffle(dices)
    for dice in dices:
        # throw each dice
        side = random.randint(1, 6)
        stmt = f"""
            SELECT word, jpg
            FROM 'dices'
            WHERE
                dice = {dice}
            AND
                side = {side};"""
        cur.execute(stmt)
        row = cur.fetchone()
        word, jpg = row

        dice_results_list.append({
            'request_id' : curr_ts_str,
            'dice' : dice,
            'side' : side,
            'word' : word,
            'jpg'  : jpg})

    # store the dicing to table dices_done
    dicing_done_df = pd.DataFrame.from_records(dice_results_list)
    #print(dicing_done_df)
    records_inserted = dicing_done_df.to_sql(
        'dicing_done',
        con=conn,
        if_exists='append',
        index=False,
        dtype={
            'request_id' : 'TEXT',
            'dice'  : 'INTEGER',
            'side'  : 'INTEGER',
            'word'  : 'TEXT',
            'jpg'   : 'TEXT'})
    conn.commit()
    if 9 != records_inserted:
        print(f'ERROR: append to table dicing_done with errors\n{dice_results_list}\n')
    return (curr_ts_str, dice_results_list)


def gen_request(dice_result_list, conn, genre_chosen):
    """generate the request for the 9 dices as dicts in dice_result_list,
    and store the result of the dicing and the request into the request table"""

    req_txt = f'''Du bist ein Author von **Kurzgeschichten**.
Verfasse eine **Kurzgeschichte** im Genre **{genre_chosen}** in **deutsch**er Sprache.

Jeder **Abschnitt** beinhaltet **drei Themen**, jedes Thema soll in dem
jeweiligen Abschitt behandelt werden.
Jeder Abschnitt soll mindestens 200 Worte umfassen, sodass die drei Teile der
zu erzählenden Kurzgeschichte auf über 600 Worte kommen soll.

Ein Thema ist durch einen der aufgeführten Begriffe bezeichnet,
wenn ein Thema  mehrere durch | getrennte Begriffe auflistet,
wähle nur einen der gelisteten Begriffe aus:\n\n'''

    req_txt += '1. **Vorspann**:\n'
    for ix, res in enumerate(dice_result_list):
        # Themen
        req_txt += f'   {(ix % 3)+1}. *Thema*: **{res['word'].replace(', ', ' | ')}**\n'

        if ix % 3 == 2:
            if ix == 2:
                req_txt += '\n2. **Mittelteil**\n'
            elif ix == 5:
                req_txt += '\n3. **Abschluss**\n'
    req_txt += """\nDie Geschichte soll einen **Titel** haben,
dieser soll mit vorangestellten ###, als **Überschrift**
auf Level 3, gekennzeichnet sein.

Nach dem **Titel** soll das **Genre** in Klammern benannt werden.

Die Überschriften der Abbschnitte (Vorspann, Mittelteil, Abschluss)
kennzeiche mit vorangestellten ####, als **Überschrift** auf Level 4.

Formatiere die Antwort als Markdown-formatierten Text und markiere
jedes Wort aus einem Thema, das Du verwendet hast **fett**.

"""

    #print(dice_result_list)
    # store the request into table requests
    request_id = dice_result_list[0]['request_id']
    request_answer_dict = {'id'      : request_id,
                           'genre'   : genre_chosen,
                           'request' : req_txt,
                           'answer'  : ""}
    # store the request to table dices_done
    request_answer_df = pd.DataFrame.from_records([request_answer_dict])
    records_inserted = request_answer_df.to_sql(
        'requests',
        con=conn,
        if_exists='append',
        index=False,
        dtype={
            'id'      : 'TEXT',
            'genre'   : 'TEXT',
            'request' : 'TEXT',
            'answer'  : 'TEXT'})
    if 1 != records_inserted:
        print(f'ERROR: append to table requests with errors\n{request_answer_dict}\n')
    return (genre_chosen, req_txt)


def ollama(prompt):
    """ send prompt to running ollama service, and get back response within 50 sec (timeout)"""
    url = "http://localhost:11434/api/chat"     # this process "ollama"
                                                # must be started at localhost
                                                # before running the script
    data = {"model"     : "gemma2:2b",
            "messages"   : [{"role" : "user",
                             "content": prompt}],
            "stream"     : False,
            "keep_alive" : "10m",               # keep_alive ollama model 10 minutes
           }
    headers = {"Content-Type" : "application/json"}
    response = requests.post(url,
                             timeout=100,       # 100 sec. !!
                             headers=headers,
                             json=data)
    return response.json()["message"]["content"]


def store_reponse_to_db(conn, cur, req_id, response):
    """store llama answer into Sqlite DB"""
    stmt = '''UPDATE OR FAIL requests SET answer = ? WHERE id = ?;'''
    cur.execute(stmt, (response, req_id))
    conn.commit()
    return 1 == cur.rowcount


def generate_md_file(request_id, genre, dicing_dicts__list, req_txt, response):
    """generate a markdown file"""
    out_dir ='stories'
    out_txt = ''
    # title
    title = response.split('\n')[0].replace('###', '').split('(')[0].strip()
    out_txt += f'# {title}\n'
    # timestamp identifier
    out_txt += f'{request_id} - **{genre}**\n\n'
    # Seciton -- Würfel
    out_txt += '## Würfel\n\n'
    out_txt += '| Abschnitt     | 1. *Thema* | 2. *Thema* | 3. *Thema* |\n'
    out_txt += '|:------------- |:----------:|:----------:|:----------:|\n'
    # Vorspann
    out_txt += '| 1. **Vorspann** '
    for ix in range(0,2+1):
        out_txt += f'| ![{dicing_dicts__list[ix]['word']}]({dicing_dicts__list[ix]['jpg']}) '
    out_txt += '|\n'
    # Mittelteil
    out_txt += '| 2. **Mittelteil** '
    for ix in range(3,5+1):
        out_txt += f'| ![{dicing_dicts__list[ix]['word']}]({dicing_dicts__list[ix]['jpg']}) '
    out_txt += '|\n'
        # Mittelteil
    out_txt += '| 3. **Abschluss** '
    for ix in range(6,8+1):
        out_txt += f'| ![{dicing_dicts__list[ix]['word']}]({dicing_dicts__list[ix]['jpg']}) '
    out_txt += '|\n\n'
    # Section -- Request an Olama
    out_txt += '## Anfrage an Ollama\n\n'
    out_txt += req_txt
    # Section -- Request an Olama
    out_txt += '## Antwort von Ollama\n\n'
    out_txt += response

    title = response.split('\n')[0].replace('###', '').split('(')[0].strip().replace('**','')
    fn = f'{out_dir}/{request_id.replace(':','-')} ({genre}) {title}.md'
    with open(fn, 'w', encoding='utf-8') as f:
        f.write(out_txt)
    f.close()
    logger.info('done: md-file stored at [%s]', fn)
    return fn


def gen_one_story(conn, cur):
    """(1) do dicing, store dicing in database
       (2) generate request for ollama and store in requests.request
       (3) send request to ollama, get answer
       (4) store the answer beside request identified by its id
           (i.e. the request's timestamp) at requests.answer
       (5) OPEN: generate a TEX file and a PDF as final result"""

    logger.info('Started')

    # do dicing ones
    logger.info('start dicing')
    request_id, dice_result_list = do_dicing(conn, cur)
    logger.info('done: dicing')
    #print(request_id)
    #print()
    #print(dice_result_list)

    # gen_request
    logger.info('start generate request')
    genre, req_txt = gen_request(dice_result_list, conn, genre_chosen=random.choice(GENRE_LST))
    logger.info('done: request generated')
    #print(req_txt)

    # send request to ollama
    # ollama has to be started before!
    logger.info('start: sending request to ollama')
    response = ollama(req_txt)
    logger.info('done: got ollama answer')
    #print(response)

    # store the response into the Sqlite DB with the request_id
    logger.info('start storing request to stories.db')
    processed = store_reponse_to_db(conn, cur, request_id, response)
    if False is processed:
        logger.info('Error: ollama answer not stored')
    else:
        logger.info('done: ollama answer stored')


    # genrate a markdown-md-file and
    # store it at sub-dir './stories/'
    logger.info('start generation of md-file')
    md_fn = generate_md_file(request_id, genre, dice_result_list, req_txt, response)

    # create a symbolic-link at './stories/by_Genre/<genre>/'
    md_fn_with_genre = f'stories/by_Genre/{genre}/{md_fn.split('/')[1:][0]}'

    os.symlink(f'../../{md_fn.split('/')[1:][0]}', md_fn_with_genre)
    logger.info('done: symbolic link to genre [%s]', md_fn_with_genre)

    # TODO: add md-to-pdf convertion
    #
    # pandoc -V geometry:a4paper,margin=2cm \
    # --pdf-engine=lualatex \
    # '2024-10-24_15-51-30 Der Schatten des Baumes.md' \
    # -o '2024-10-24_15-51-30 Der Schatten des Baumes.pdf'

    logger.info('Ready')


def main():
    """main routes actions according command line options with:
    (1) no parameters given -> give usage info
    (2) if a number is given -> genrate n stories"""
    logging.basicConfig(filename='the_story_teller.log',
                    format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

    logger.info('')
    logger.info('Start: Initialization')
    # check existance of sub-dir genre at stories/by_Genre/<genre>/
    logger.info('start checking environment')
    check_or_create_env()
    logger.info('done: checking environment')

    stories_db__file = Path("stories.db")
    try:
        logger.info('start trying to access stories.db')
        _ = stories_db__file.resolve(strict=True)

    except FileNotFoundError:
        # stories.db doesn't exist --> re-create it
        # read dices.tsv
        logger.info('Error: stories.db not accessible, starting recreation')
        dices_df = get_dices('dices.tsv') # t_ab s_eparated v_alues
        # store dices.tsv to Sqlite stories.db at table dices
        conn = sqlite3.connect('stories.db')
        store_to_sqlite_db(dices_df, conn)
        conn.close()
        logger.info('done: stories.db recreated')

    # get connection
    conn = sqlite3.connect('stories.db')
    # get cursor to Sqlite DB stories.db
    cur = conn.cursor()

    logger.info('done: got stories.db')
    logger.info('done: Initialization')

    logger.info('')
    if len(sys.argv) < 2:
        print("""the_story_teller.py

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
""")
    else:
        num_of_stories = int(sys.argv[1])
        if 10 >= num_of_stories > 0:
            logger.info('start creation of %d story', num_of_stories)

            for _ in range(num_of_stories):
                gen_one_story(conn, cur)

        else:
            err_txt = 'Error: number of stories to generate > 10 -> execution aborted'
            print(err_txt)
            logger.info(err_txt)
            sys.exit(1)

    # TODO: add options e.g. for a given genre the story
    # e.g. with a new cmd-line param 'genre'
    #   'python the_story_teller.px 1 Action' --> 1 Action-story
    #   'python the_story_teller.px 3 Action' --> 3 Action-story, each with its own keywords

    # TODO: add options e.g. for
    # generate stories for all genres with this dicing_done (aka keywords)

    logger.info('\n')
    conn.close()


if __name__ == '__main__':
    main()
