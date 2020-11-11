
import re
import discogs_client as dc
from db import cc
# from colorama import Fore


ds = dc.Client('chimera/0.1', user_token=cc.discogs_token)



class DTag(object):
    def __init__(self):
        self.styles = None
        self.year = None
        self.year_found = False
        self.style_found = False
        self.image = False


def search(title='', artist=''):
    from fuzzywuzzy import process
    # check if track has required tags for searching
    if artist == '' and title == '':
        # print(Fore.RED + 'Track does not have the required tags for searching.')
        return False

    # print(Fore.YELLOW + 'Searching on discogs: {} {}'.format(title, artist))
    # discogs api limit: 60/1minute
    # time.sleep(1.1)
    res = ds.search(type='master', artist=artist, track=title)

    local_string = f'{title} {artist}'
    discogs_list = []
    if res.count > 0:
        for i, track in enumerate(res):
            d_artist = ''
            if track.data.get('artist'):
                d_artist = d_artist['artist'][0]['name']
            d_title = track.title

            # create string for comparison
            discogs_string = f'{d_title} {d_artist}'

            # append to list
            discogs_list.append({'index': i, 'str': discogs_string})

        # get best match from list
        best_one = process.extractBests(local_string, discogs_list, limit=1)[0][0]['index']

        # create return object
        result = DTag()

        # check if style is missing
        if res[best_one].styles:
            styles = ', '.join(sorted([x for x in res[best_one].styles]))
            result.styles = styles
            result.style_found = True

        if res[best_one].data['year']:
            year = res[best_one].data['year']
            result.year = str(year)
            result.year_found = True

        if res[best_one].images:
            result.image = res[best_one].images[0]['uri']

        return result
    else:
        # print(Fore.RED + 'Not Found: {} {}'.format(title, artist))
        return False


def clean(string):
    string = re.sub(r'\([^)]*\)', '', string).strip()
    if ',' in string:
        string = string.split(',')[0].strip()
    if '&' in string:
        string = string.split('&')[0].strip()
    blacklist = ["'", "(Deluxe)"]
    for c in blacklist:
        string = string.replace(c, '')
    return string