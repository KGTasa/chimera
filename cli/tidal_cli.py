"""
tidal commands for the cli
"""
import typing

import chimera.concurrency
import cli.dtq_cli
import cli.utils
from chimera.download import any_playlist, any_track
from config import log
from db import cc

if typing.TYPE_CHECKING:
    from tidal.tidal import Tidal

def login(tidal, verbose=True):
    tidal_user = tidal.login(username=cc.tidal_email, password=cc.tidal_password)
    log.info('tidal logged in')
    if verbose:
        cli.utils.login_message('Tidal')

def grab_track(song_id, tidal: 'Tidal'):
    track = tidal.get_track(int(song_id))
    if track:
        if cc.concurrency:
            return chimera.concurrency.blackhole(track, 'track')
        ds = any_track(track, tidal, overwrite=cc.dl_track_overwrite, add_to_db=cc.dl_track_add_to_db, check_db=cc.dl_track_check_db)
        cli.utils.parse_ds(ds)

def grab_album(album_id, tidal):
    album = tidal.get_album(album_id)
    if album:
        if cc.concurrency:
            return chimera.concurrency.blackhole(album, 'album')
        print('grabbing tidal album %s' % album.title)
        for track in album.songs:
            ds = any_track(track, tidal, overwrite=cc.dl_album_overwrite, add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db)
            cli.utils.parse_ds(ds)
    else:
        cli.utils.pred('Album not found!')

def grab_playlist(playlist_id, tidal):
    playlist = tidal.get_playlist(playlist_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(playlist, 'playlist')
    print('grabbing tidal playlist %s' % playlist.name)
    any_playlist(playlist, tidal, m3u=cc.m3u, log_missing=True)

def grab_video(video_id, tidal):
    video = tidal.get_video(video_id)
    print('grabbing tidal video %s' % video.title)
    video.download(tidal)

def grab_videos_from_artist(artist_id, tidal):
    videos = tidal.get_videos_from_artist(artist_id)
    print(f'Found {len(videos)}')
    for video in videos:
        print('grabbing tidal video %s' % video.title)
        video.download(tidal)


def search_track(tidal, add_to_db=True):
    q = input('Tidal: search track: ')
    tracks = tidal.search_track(q)
    cli.dtq_cli.search_track(tidal=tidal, dtq_tracks=tracks)


def search_album(tidal):
    q = input('search album: ')
    albums = tidal.search_album(q)
    cli.dtq_cli.search_album(tidal=tidal, dtq_albums=albums)

def search_isrc(tidal, isrc):
    print('isrc search not implemented for tidal !')

def search_video(tidal):
    q = input('search video: ')
    videos = tidal.search_videos(q)
    for i, video in enumerate(videos):
        print(f'{i}) {video}')
    selection = input("Select ('q' to exit): ")
    if selection == 'q':
        return
    selection = int(selection)
    grab_video(videos[selection].id, tidal)

def show_playlists(tidal):
    playlists = tidal.get_user_playlists_data()
    cli.dtq_cli.ptable(playlists, blacklist=['image', 'description'], truncated=False, row_number=False)


def read_csv(tidal):
    print('csv download not implemented for tidal!')
