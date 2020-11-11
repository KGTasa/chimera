import sys
from functools import wraps
from config import log
from colorama import Fore

from generic.utils import AuthRequiredException, InvalidQobuzSubscription, InvalidOrMissingAppID, MissingNapsterApiKey
from requests.exceptions import HTTPError

def parse_ds(ds, verbose=True):
    if ds.failed:
        pred(ds.reason, verbose=verbose)
    else:
        if ds.status_code != 0:
            pyel(ds.reason, verbose=verbose)

# these are here and in chimera.utils
# because of import errors
def pred(text, verbose=True):
    if verbose:
        print(Fore.LIGHTRED_EX + text)
    else:
        log.error(text)

def pyel(text, verbose=True):
    if verbose:
        print(Fore.YELLOW + text)
    else:
        log.info(text)

def print_service(service):
    if service == 'deezer':
        sys.stdout.write(Fore.GREEN + 'DEEZER   ')
        sys.stdout.flush()
    elif service == 'tidal':
        sys.stdout.write(Fore.YELLOW + 'TIDAL    ')
        sys.stdout.flush()
    elif service == 'qobuz':
        sys.stdout.write(Fore.MAGENTA + 'QOBUZ    ')
        sys.stdout.flush()
    elif service == 'soundcloud':
        sys.stdout.write(Fore.CYAN + 'SOUNDCLOUD ')
        sys.stdout.flush()
    elif service == 'napster':
        sys.stdout.write(Fore.LIGHTBLUE_EX + 'NAPSTER  ')
        sys.stdout.flush()


def check_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            res = f(*args, **kwargs)
            return res
        except AuthRequiredException as e:
            print('AUTH REQUIRED! USE LOGIN TO AUTHENITCATE')
    return wrapper


def ptable(data, blacklist=[], truncated=False, row_number=True, retry=1):
    if len(data) == 0:
        print('No data found!')
        return

    def pservice(service):
        if service == 'deezer':
            sys.stdout.write(Fore.GREEN + ' deezer\n')
            sys.stdout.flush()
        elif service == 'tidal':
            sys.stdout.write(Fore.YELLOW + ' tidal\n')
            sys.stdout.flush()
        elif service == 'qobuz':
            sys.stdout.write(Fore.MAGENTA + ' qobuz\n')
            sys.stdout.flush()
        elif service == 'soundcloud':
            sys.stdout.write(Fore.CYAN + ' soundcloud\n')
            sys.stdout.flush()
        elif service == 'napster':
            sys.stdout.write(Fore.LIGHTBLUE_EX + ' napster\n')
            sys.stdout.flush()
        elif service == 'gpm':
            sys.stdout.write(Fore.LIGHTRED_EX + ' gpm\n')
            sys.stdout.flush()
        elif service == 'spotify':
            sys.stdout.write(Fore.GREEN + ' spotify\n')
            sys.stdout.flush()

    def cut(text, size):
        if len(str(text)) >= size:
            text = text[:size - 3]
            return text + '...'
        return str(text)

    def psmart(text, size):
        return cut(text, size).ljust(size)

    col_sizes = {}
    col_names = []
    for row in data:
        for key, value in row.items():
            if key in col_sizes and key not in blacklist:
                col_sizes[key].append(len(str(value)))
            elif key not in blacklist:
                col_sizes[key] = [len(str(value))]
            if key not in col_names and key not in blacklist:
                col_names.append(key)

    for key, value in col_sizes.items():
        if truncated:
            try:
                col_sizes[key] = sorted(value)[:-2][-1] + 2 # remove last two entries which are the longst
            except IndexError as e:
                col_sizes[key] = sorted(value)[-1] + 2
        else:
            col_sizes[key] = sorted(value)[-1] + 2

    # if col is only 2 chars and
    # header is longer, header get's truncated
    for h in col_names:
        if col_sizes[h] <= len(h):
            col_sizes[h] = len(h) + 2

    if row_number:
        col_names.insert(0, 'i')
        col_sizes['i'] = 4

    # header = 9 * ' ' # service name with spaces length
    header = ' '.join([psmart(h, col_sizes[h]) for h in col_names])

    # check if row exceeds max limit
    # could end up in a loop
    if len(header) > 208 and retry == 1:
        return ptable(data=data, blacklist=blacklist, truncated=True, row_number=row_number, retry=retry - 1)
    print(header)
    print(len(header) * '-')

    for i, row in enumerate(data):
        if row_number:
            row['i'] = f'{i})'
        if 'type' in row and 'type' not in blacklist:
            text_row = ' '.join([psmart(row[c], col_sizes[c]) for c in col_names if c != 'type'])
            sys.stdout.write(text_row)
            sys.stdout.flush()
            pservice(row['type'])
        else:
            print(' '.join([psmart(row[c], col_sizes[c]) for c in col_names]))


def master_login(deezer=None, tidal=None, qobuz=None, napster=None, gpm=None, verbose=True):
    import cli.deezer_cli
    import cli.tidal_cli
    import cli.qobuz_cli
    import cli.napster_cli
    import cli.gpm_cli
    clis = {
        'DEEZER': cli.deezer_cli,
        'TIDAL': cli.tidal_cli,
        'QOBUZ': cli.qobuz_cli,
        'NAPSTER': cli.napster_cli,
        'GPM': cli.gpm_cli
    }
    # TODO logged in checker? Reauth?
    services = [s for s in [deezer, tidal, qobuz, napster, gpm] if s]
    for service in services:
        try:
            clis[str(service)].login(service, verbose=verbose)
        except InvalidQobuzSubscription as e:
            print('Invalid Qobuz Subscription, aborting...')
        except InvalidOrMissingAppID as e:
            print('Invalid or missing app id, aborting...')
        except MissingNapsterApiKey as e:
            print('Missing Napster Api Key, aborting...')
        except HTTPError as e:
            print(e)


def login_message(text):
    try:
        sys.stdout.write(Fore.GREEN + '✓ ' + Fore.RESET + ' logged in to ' + text + '\n')
    except UnicodeEncodeError as e:
        sys.stdout.write(Fore.GREEN + '+ ' + Fore.RESET + ' logged in to ' + text + '\n')
    sys.stdout.flush()
