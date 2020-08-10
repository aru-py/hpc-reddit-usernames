"""
main.py
~~~~~~~~
checks status of all 4 letter words in the english language
as reddit usernames
"""


import logging
import requests
import time

# use multiple threads for faster checking
use_multiple_threads = True
if use_multiple_threads:
    import multiprocessing as mlp

# output to stdout
logging.basicConfig(level=20, format="%(message)s")

# create request session with proper headers
headers = {'User-Agent': 'Mozilla/5.0'}
session = requests.Session()

def check_username(username: str):
    """ returns True is username is available """
    # perform quick HEAD request to first check
    try:
        res = session.head(f'https://www.reddit.com/user/{username}', headers=headers, timeout=10)
    except requests.exceptions.ReadTimeout:
        logging.warning("Timed Out")
        time.sleep(5)
        res = session.head(f'https://www.reddit.com/user/{username}', headers=headers, timeout=10)

    # if page not found username is either available, banned, or deleted
    if res.status_code == 200:
        return username, False
    elif res.status_code == 404:
        # perform GET request to validate
        res = session.get(f'https://www.reddit.com/api/username_available.json?user={username}', headers=headers)
        if res.json():
            return username, True
    else:
        logging.error(f"Unknown response from Reddit ({res.status_code}). Probably too many requests.")
    return username, False


def update(text: list):
    """ updates text file with status of words """
    with open('data/output.txt', 'a+') as f:
        for t in text:
            f.write(f"{t[0]:30}{str(t[1])}\n")

# get list of words
with open('data/english-dictionary.txt') as f:
    words = f.read().split()


total_words = len(words)

if use_multiple_threads:
    pool = mlp.Pool() # create pool with all cores and load words
    chunk_size = mlp.cpu_count()*3 # how many words to retrieve at a time
else:
    chunk_size = 20 # default chunk size


# scrape until words exhausted
logging.info("Begin checking")
while len(words) > 0:
    # get a chuck of words at a time
    curr = words[:chunk_size]
    del words[:chunk_size]

    if use_multiple_threads:
        check = pool.map_async(check_username, curr)
        update(check.get())
    else:
        check = [check_username(name) for name in curr]
        update(check)

    # print update
    logging.info(f"Words checked: {total_words - len(words)}/{total_words}")
