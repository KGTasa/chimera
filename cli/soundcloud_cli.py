"""
soundcloud commands for the cli
"""

import os
import cli.utils
import re
from db import cc
# track = soundcloud.get_track_from_url('https://soundcloud.com/the-concept-band/goldrushed-mastered')
# track = soundcloud.get_track_from_url('https://soundcloud.com/ynwmelly/dangerously-in-love-772-love-pt-2')
# track = soundcloud.get_track('62986583')

# stream_url = track.get_stream(soundcloud)
# print(stream_url)
# soundcloud.get_playlist_from_url(url = 'https://soundcloud.com/discover/sets/charts-top:alternativerock:ch')

# plist = soundcloud.get_playlist_from_url('https://soundcloud.com/playlist/sets/started-on-soundcloud')

def grab_track(url, soundcloud):
    """
    gets track from url with soundcloud.resolve
    """
    download_soundcloud_track(soundcloud.get_track_from_url(url), soundcloud)

def grab_playlist(url, soundcloud):
    if re.match('^[0-9]*$', url):
        # url is a id
        playlist = soundcloud.get_playlist(url)
    else:
        playlist = soundcloud.get_playlist_from_url(url)

    print('grabbing soundcloud playlist {}'.format(playlist.name))
    for track in playlist.songs:
        download_soundcloud_track(track, soundcloud)


def show_playlists(soundcloud):
    # a list of all playlists
    playlists = soundcloud.get_user_playlists_data()
    cli.dtq_cli.ptable(playlists, blacklist=[], truncated=False, row_number=False)

def download_soundcloud_track(track, soundcloud, task=None):
    print(f'grabbing {track.title} by {track.artist} ID: {track.song_id}')
    file_name = track.download(soundcloud, folder=os.path.join(cc.root_path, track.generate_folder_path()))
    if file_name:
        track.tag(file_name)