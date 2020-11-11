import sys
from collections import namedtuple
from functools import wraps

import requests

from config import log

cover_store = []

def print_progress_callback(progress):
    p = float(progress) * 100
    n_eq = int(int(p) / 100 * 20)
    n_m = 20 - n_eq
    fill = n_eq * '=' + n_m * ' '
    sys.stdout.write('\r[{}] {:.2f}%'.format(fill, p))
    sys.stdout.flush()
    if progress == 1:  # if it finished
        sys.stdout.write('\n')
    #   sys.stdout.write('\nfinished downloading\n')


def remove_illegal_characters(p):
    illegal = ['*', '.', '"', '/', '\\', ';', ':', '|', '?', '<', '>']
    for char in illegal:
        if char in p:
            p = p.replace(char, '')
    return p

def authrequired(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # first arg should be self
        if args[0].logged_in == False:
            raise AuthRequiredException()
        return f(*args, **kwargs)
    return wrapper

def retry_and_reauth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            res = f(*args, **kwargs)
            return res
        except ConnectionError as e:
            from cli.utils import master_login # import error
            service = args[0]
            service.session = requests.Session()
            service.logged_in = False
            master_login(**{str(service).lower(): service})

            log.warning(f'{str(service)} crashed, session recreated!')
            res = f(*args, **kwargs)
            return res

    return wrapper


def cover_tester(url):
    """cover handler, checks if a cover url is valid"""
    if url in cover_store:
        return True
    r = requests.head(url)
    if r.status_code == 200:
        cover_store.append(url)
        return True
    else:
        return False


DownloadResult = namedtuple('DownloadResult', ['file_name', 'status_code', 'status_text'])


class AuthRequiredException(Exception):
    pass
class InvalidQobuzSubscription(Exception):
    pass
class InvalidOrMissingAppID(Exception):
    pass
class MissingNapsterApiKey(Exception):
    pass
class InvalidTidalToken(Exception):
    def __init__(self):
        Exception.__init__(self, 'Tidal token invalid!')
class ValidTokenRequired(Exception):
    def __init__(self):
        Exception.__init__(self, 'Delete deezer token in tokens/deezer.token to get a valid session!')
