import chimera.concurrency
import cli.dtq_cli
import cli.utils
from chimera.download import any_playlist, any_track
from db import cc


def login(gpm, verbose=True):
    if gpm.login():
        if verbose:
            cli.utils.login_message('Google Play Music')


def grab_track(song_id, gpm):
    track = gpm.get_track(song_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(track, 'track')
    ds = any_track(track, gpm, overwrite=cc.dl_track_overwrite,
                   add_to_db=cc.dl_track_add_to_db, check_db=cc.dl_track_check_db)
    if ds.failed:
        print(ds.reason)


def grab_album(album_id, gpm):
    album = gpm.get_album(album_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(album, 'album')
    print('grabbing gpm album %s' % album.title)
    for track in album.songs:
        any_track(track, gpm, overwrite=cc.dl_album_overwrite, add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db)

def grab_playlist(playlist_id, gpm):
    playlist_name = input('Playlist Name: ')
    if playlist_name == '':
        playlist_name = None
    playlist = gpm.get_playlist(playlist_id, playlist_name)
    if cc.concurrency:
        return chimera.concurrency.blackhole(playlist, 'playlist')
    print('grabbing gpm playlist %s' % playlist.name)
    any_playlist(playlist, gpm, m3u=cc.m3u, log_missing=True)

def search_track(gpm):
    q = input('search track: ')
    tracks = gpm.search_track(q)
    cli.dtq_cli.search_track(gpm=gpm, dtq_tracks=tracks)


def search_album(gpm):
    q = input('search album: ')
    albums = gpm.search_album(q)
    cli.dtq_cli.search_album(gpm=gpm, dtq_albums=albums)


def show_playlists(gpm):
    # a list of all playlists
    playlists = gpm.get_user_playlists_data()
    # cli.utils.display_user_playlists(playlists)
    cli.dtq_cli.ptable(playlists, blacklist=['image', 'description'], truncated=False, row_number=False)
