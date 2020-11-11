# 1. standard
import codecs
import math
import os
import random
import time
from functools import wraps

# 2. third party
from colorama import Fore
from mutagen.flac import FLAC, FLACNoHeaderError
from mutagen.mp3 import MP3, EasyMP3, HeaderNotFoundError, MutagenError
from mutagen.mp4 import MP4, MP4StreamInfoError
from sqlalchemy.exc import OperationalError

# 3. chimera
import chimera.csv
import chimera.utils
from config import log
from db import cc
# from db.db import session
from db.db import create_session
from db.models import DBTrack

import_path = 'import'
sub_dir = 'playlists'
csv_missing = os.path.join(import_path, sub_dir, '{}_missing.csv')

folders = [
    os.path.join(import_path, sub_dir),
    os.path.join(import_path, 'cache'),
    os.path.join(import_path, 'playlists')
]

for folder_path in folders:
    if os.path.exists(folder_path) == False:
        os.makedirs(folder_path)

def write_m3u_file(m3u_playlist, m3u_tracks, verbose=True):
    if os.path.exists(os.path.join(import_path, sub_dir)) is False:
        os.makedirs(os.path.join(import_path, sub_dir))
    with open(m3u_playlist, 'w', encoding='utf-8') as f:
        if verbose:
            print('Writing m3u playlist')
        f.writelines(m3u_tracks)


def write_missing_csv(name, missing_tracks):
    print('Missing Tracks total: {}'.format(len(missing_tracks)))
    chimera.csv.write_csv(csv_missing.format(name), missing_tracks)
    missing_tracks = []


def get_file_length_seconds(file):
    """
    Tries to get length in seconds for a mp3 path
    Args:
        Full Path to Audio File, supports FLAC and MP3
    Returns:
        `Integer` Audio length in seconds
        `None` if it is not a valid Audio file
    """
    if file.endswith('.mp3'):
        try:
            audio = MP3(file)
            return int(audio.info.length)
        except (HeaderNotFoundError, MutagenError) as e:
            return None

    if file.endswith('.flac'):
        try:
            audio = FLAC(file)
            return int(audio.info.length)
        except (FLACNoHeaderError, Exception) as e:
            return None

    if file.endswith(('.m4a', '.mp4')):
        try:
            audio = MP4(file)
            return int(audio.info.length)
        except (KeyError, MP4StreamInfoError, MutagenError) as e:
            return None



def check_track_length(dbtrack):
    """
    Checks if a track is fully downloaded
    Args:
        DBTrack object
    Returns
        `True` if track Length matches with local file
        `False` if local track is not found or bigger difference than 5  seconds
    """
    length_file = get_file_length_seconds(os.path.join(cc.root_path, dbtrack.path))
    try:
        if math.isclose(length_file, int(dbtrack.remote_duration), abs_tol=5): # to int needed because reason
            return True
    except TypeError as e:
        pass
    return False


def check_tags(file):
    """
    Check if id3 or vorbis tags are added
    Args:
        File full path
    """
    if file.endswith('.flac'):
        try:
            audio = FLAC(file)
        except (FLACNoHeaderError, Exception) as e:
            return False

    if file.endswith('.mp3'):
        try:
            audio = EasyMP3(file)
        except (HeaderNotFoundError, MutagenError) as e:
            return False

    if file.endswith(('.m4a', '.mp4')):
        try:
            audio = MP4(file)
        except (KeyError, MP4StreamInfoError, MutagenError) as e:
            return False

    # get tags
    try:
        if not file.endswith(('.m4a', '.mp4')):
            artist = audio['artist'][0]
            title = audio['title'][0]
            return True
        else:
            artist = audio['\xa9ART'][0]
            title = audio['\xa9nam'][0]
            return True
    except KeyError as e:
        return False




def validate_music_archive(delete=False):
    """get all tracks from db
    check each track, creates a list of songs which are not fully or wrong downloaded
    this list does not include not downloaded tracks
    Used function `chimera.utils.check_track_length` for file comparison"""

    wrong_tracks = []
    session = create_session()
    dbtracks = session.query(DBTrack).all()
    for dbtrack in dbtracks:

        if check_track_length(dbtrack) == False:
            wrong_tracks.append(dbtrack)
            length_file = get_file_length_seconds(os.path.join(cc.root_path, dbtrack.path))
            err_msg = f'WRONG: {dbtrack} DEEZER: {dbtrack.remote_duration} LOCAL: {length_file}'
            write_outfile_wrong(err_msg)
            print(err_msg)

            if delete:
                try:
                    # remove from disk
                    os.remove(os.path.join(cc.root_path, dbtrack.path))
                except FileNotFoundError as e:
                    pass
                # remove from db
                session.delete(dbtrack)
                session.commit()
        # else:
            #write_outfile_right(dbtrack)


def validate_disk():
    from pathlib import Path
    root = r'D:\temp\Musik_flac'
    for file in Path(root).glob('**/*.flac'):
        # check if file is valid
        #res = get_file_length_seconds(str(file))

        # check if tags er set
        res = check_tags(str(file))
        if res is False:
            print(str(file))
            #os.remove(str(file))

def update_tracks_in_db(deezer):
    """
    Temporary function to update `DBTrack.remote_duration`
    """
    session = create_session()
    dbtracks = session.query(DBTrack).all()
    for dbtrack in dbtracks:
        if dbtrack.service is None:
            print(f'Updating Track: {dbtrack.id}')
            dbtrack.service = 'deezer'
            session.commit()



def write_outfile_wrong(_text):
    with codecs.open('log_file_wrong.txt', 'a+', 'utf-8-sig') as f:
        f.write(f'{_text}\n')

def write_outfile_right(_text):
    with codecs.open('log_file_right.txt', 'a+', 'utf-8-sig') as f:
        f.write(f'{_text}\n')


def timeit(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        ts = time.time()
        result = f(*args, **kwargs)
        te = time.time()
        if cc.prod == False:
            print('func:{} took: {} sec'.format(f.__name__, round((te - ts), 2)))
        return result
    return wrap

def sql_retry(f):
    """this is just an easy fix for multithreaded sqlwrites problem
    Better solution would be to create a dedicated sqlwriter thread
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except OperationalError as e:
            if 'database is locked' in e.args[0]:
                time.sleep(random.randint(1, 10))

                # get session for this thread
                session = create_session()
                session.rollback()
                return f(*args, **kwargs)
    return wrapper

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

class DownloadResponse:
    def __init__(self, failed, reason, quality=None, status_code=0, status_text='', **kwargs):
        """downloading any track will return this response
        extended with generic.utils.DownloadResult"""
        self.failed = failed
        self.reason = reason
        self.quality = quality
        self.status_code = status_code
        self.status_text = status_text
        for key, value in kwargs.items():
            setattr(self, key, value)
