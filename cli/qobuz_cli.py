"""
qobuz commands for the cli
"""

import chimera.concurrency
import cli.dtq_cli
import cli.utils
from chimera.download import any_playlist, any_track
from chimera.utils import timeit
from config import log
from db import cc
from generic.utils import InvalidOrMissingAppID, InvalidQobuzSubscription
from qobuz.qobuz import Qobuz


def login(qobuz, verbose=True):
    try:
        qobuz_user = qobuz.login(email=cc.qobuz_email, password=cc.qobuz_password,
                                 app_id=cc.qobuz_app_id)
    except InvalidQobuzSubscription as e:
        print('Invalid Qobuz Subscription, aborting...')
        return
    except InvalidOrMissingAppID as e:
        print('Invalid or missing app id, aborting...')
        return
    log.info('qobuz logged in')
    if verbose:
        cli.utils.login_message('Qobuz')

def grab_track(song_id, qobuz):
    # 62333205
    track = qobuz.get_track(song_id)
    if track:
        if cc.concurrency:
            return chimera.concurrency.blackhole(track, 'track')
        ds = any_track(track, qobuz, overwrite=cc.dl_track_overwrite, add_to_db=cc.dl_track_add_to_db, check_db=cc.dl_track_check_db)
        cli.utils.parse_ds(ds)
    else:
        print('Track not available on qobuz!')

@timeit
def grab_album(album_id, qobuz: Qobuz):
    album = qobuz.get_album(album_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(album, 'album')
    print('grabbing qobuz album %s' % album.title)
    for track in album.songs:
        ds = any_track(track, qobuz, overwrite=cc.dl_album_overwrite, add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db)
        cli.utils.parse_ds(ds)

def grab_playlist(playlist_id, qobuz):
    playlist = qobuz.get_playlist(playlist_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(playlist, 'playlist')
    print('grabbing qobuz playlist %s' % playlist.name)
    any_playlist(playlist, qobuz, m3u=cc.m3u, log_missing=True)

def grab_saved(qobuz: Qobuz):
    playlist = qobuz.get_user_saved()
    any_playlist(playlist, qobuz, m3u=cc.m3u, log_missing=True)

def search_track(qobuz):
    q = input('Qobuz search track: ')
    tracks = qobuz.search_track(q)
    cli.dtq_cli.search_track(qobuz=qobuz, dtq_tracks=tracks)


def search_album(qobuz):
    """
    Album search, returns no track objects within album.songs
    search for these after user selected which album to download, else too many api calls
    """
    q = input('Qobuz search album: ')
    albums = qobuz.search_album(q)
    cli.dtq_cli.search_album(qobuz=qobuz, dtq_albums=albums)


def show_playlists(qobuz):
    # a list of all playlists
    playlists = qobuz.get_user_playlists_data()
    cli.dtq_cli.ptable(playlists, blacklist=['image', 'description'], truncated=False, row_number=False)
