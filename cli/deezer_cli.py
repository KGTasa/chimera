"""
deezer commands for the cli
"""

import chimera.csv
import chimera.spotify
import cli.dtq_cli
import cli.utils
import chimera.concurrency
from chimera.download import any_playlist, any_track
from chimera.utils import timeit
from config import log
from db import cc
# typing
from deezer.deezer import Deezer


def login(deezer, verbose=True):
    # 1. Try to login with cookie -> filename is username
    try:
        user = deezer.login_with_cookie(cc.deezer_username)
        if verbose:
            cli.utils.login_message('Deezer')
            # print('logged in with cookie as %s' % user['name'])
        log.info('deezer logged in with cookie')
    except Exception as e:
        print(e)
        choice = input('Failed to login with cookie.\n1 Re-Captcha login\n2 Arl login\n-> ')
        if choice == '1':
            print('Enter captcha-response')
            command = input('-> ')
            user = deezer.login(cc.deezer_email, cc.deezer_password, command)
        else:
            arl = input('Arl Code -> ')
            user = deezer.login_with_arl(arl)

        # save cookie for next time
        deezer.save_cookies()
        # print('logged in as %s' % user['name'])
        cli.utils.login_message('Deezer')
        log.info('logged in with re-captcha or with arl')

def grab_track(song_id, deezer: Deezer, add_to_db=True):
    track = deezer.get_track(int(song_id))
    if cc.concurrency:
        return chimera.concurrency.blackhole(track, 'track')
    ds = any_track(track, deezer, overwrite=cc.dl_track_overwrite,
                   add_to_db=cc.dl_track_add_to_db, check_db=cc.dl_track_check_db,
                   lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics)
    cli.utils.parse_ds(ds)

def grab_album(album_id, deezer: Deezer, add_to_db=True):
    album = deezer.get_album(album_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(album, 'album')
    print('grabbing deezer album %s' % album.title)
    for track in album.songs:
        ds = any_track(track, deezer, overwrite=cc.dl_album_overwrite,
                       add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db,
                       lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics)
        cli.utils.parse_ds(ds)

@timeit
def grab_playlist(playlist_id, deezer: Deezer, playlist=None):
    """crash resistant"""
    if playlist is None:
        playlist = deezer.get_playlist(playlist_id)
        if cc.concurrency:
            return chimera.concurrency.blackhole(playlist, 'playlist')
    print('grabbing deezer playlist %s' % playlist.name)
    # try:
    any_playlist(playlist, deezer, m3u=cc.m3u, log_missing=True)
    # except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
    #     print(30 * '#')
    #     print('Download crashed restarting...')
    #     print(30 * '#')
    #     login(deezer)
    #     grab_playlist(playlist_id, deezer, playlist=playlist)

def grab_saved(deezer: Deezer):
    # no need for deezer, it's already a playlist
    playlists = deezer.get_user_playlists_data()
    playlist = next(filter(lambda x: x['title'] == 'Loved Tracks', playlists))
    grab_playlist(str(playlist['id']), deezer)

def grab_show(show_id, deezer):
    show = deezer.get_show(show_id)
    show.download()

def grab_episode(episode_id, deezer):
    episode = deezer.get_episode(episode_id)
    print(f'Downloading Episode: {episode.title}')
    episode.download()

def search_track(deezer, add_to_db=True):
    q = input('search track: ')
    tracks = deezer.search_track(q)
    cli.dtq_cli.search_track(deezer=deezer, dtq_tracks=tracks)

def search_album(deezer):
    q = input('search album: ')
    albums = deezer.search_album(q)
    cli.dtq_cli.search_album(deezer=deezer, dtq_albums=albums)

def search_isrc(deezer, isrc):
    tracks = deezer.search_isrc(isrc)
    print(tracks)

def show_playlist(deezer):
    # show infos about playlist
    pass

def show_playlists(deezer):
    # a list of all playlists
    playlists = deezer.get_user_playlists_data()
    # cli.utils.display_user_playlists(playlists)
    cli.dtq_cli.ptable(playlists, blacklist=['image', 'description'], truncated=False, row_number=False)

def read_csv(deezer):
    """Reads CSV and Downloads Songs"""
    csv_file = input('csv: ')
    chimera.csv.read(csv_file, deezer)
