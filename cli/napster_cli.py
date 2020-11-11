import re

import requests

import chimera.concurrency
import cli.dtq_cli
import cli.utils
from chimera.download import any_playlist, any_track
from chimera.utils import pred
from cli.utils import check_auth
from db import cc
from generic.utils import MissingNapsterApiKey
from napster.napster import Napster


def login(napster, verbose=True):
    try:
        data = napster.login(cc.napster_email, cc.napster_password)
        if verbose:
            cli.utils.login_message('Napster ' + data)
    except MissingNapsterApiKey as e:
        print('Missing Napster Api Key, aborting...')

@check_auth
def grab_track(song_id, napster: Napster):
    if song_id.startswith('http'):
        return grab_track_from_url(song_id, napster)
    track = napster.get_track(song_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(track, 'track')
    ds = any_track(track, napster, overwrite=cc.dl_track_overwrite,
                   add_to_db=cc.dl_track_add_to_db, check_db=cc.dl_track_check_db)
    cli.utils.parse_ds(ds)


@check_auth
def grab_track_from_url(url, napster: Napster):
    track_id = get_id(url, is_track=True)
    if track_id:
        return grab_track(track_id.replace('Tra.', ''), napster)
    else:
        pred('Track id not found!')

@check_auth
def grab_album(album_id, napster: Napster):
    if album_id.startswith('http'):
        return grab_album_from_url(album_id, napster)
    album = napster.get_album(album_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(album, 'album')
    print('grabbing napster album %s' % album.title)
    for track in album.songs:
        ds = any_track(track, napster, overwrite=cc.dl_album_overwrite,
                       add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db)
        if ds.failed:
            pred(ds.reason)

@check_auth
def grab_album_from_url(url, napster: Napster):
    album_id = get_id(url)
    if album_id:
        return grab_album(album_id, napster)
    else:
        pred('Album id not found!')


def grab_playlist(playlist_id, napster: Napster):
    playlist = napster.get_playlist(playlist_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(playlist, 'playlist')
    print('grabbing napster playlist %s' % playlist.name)
    any_playlist(playlist, napster, m3u=cc.m3u, log_missing=True)


def search_track(napster: Napster):
    q = input('search track: ')
    tracks = napster.search_track(q)
    cli.dtq_cli.search_track(napster=napster, dtq_tracks=tracks)

def search_album(napster: Napster):
    q = input('search album: ')
    albums = napster.search_album(q)
    cli.dtq_cli.search_album(napster=napster, dtq_albums=albums)

def show_playlists(napster: Napster):
    # a list of all playlists
    playlists = napster.get_user_playlists_data()
    cli.dtq_cli.ptable(playlists, blacklist=['image', 'description'], truncated=False, row_number=False)


def get_id(url, is_track=False):
    """returns track id or album id from an napster url"""
    shortcut_url = 'https://direct.rhapsody.com/metadata/data/methods/getIdByShortcut.js'
    if is_track:
        re_filter = r'artist/(?P<artist>(.*.))/album/(?P<album>(.*.))/track/(?P<track>(.*.))'
    else:
        re_filter = r'artist/(?P<artist>(.*.))/album/(?P<album>(.*.))'
    re_search = re.search(re_filter, url)
    if re_search:
        re_search = re_search.groupdict()
        params = {
            'albumShortcut': re_search['album'],
            'artistShortcut': re_search['artist'],
            'developerKey': '5C8F8G9G8B4D0E5J'
        }
        if is_track:
            params['trackShortcut'] = re_search['track']
        res = requests.get(shortcut_url, params=params)
        return res.json()['id']
    else:
        return None
