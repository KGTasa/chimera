import requests.exceptions
from tqdm import tqdm

import chimera.concurrency
import chimera.spotify
import cli.utils
# from chimera.concurrency import blackhole # ???? import error
from chimera.download import any_playlist, search_track_on_services, sp_track
from db import cc


def login(service):
    print('Not implemented for Spotify!')
def grab_track(song_id, session):
    track = chimera.spotify.get_track(song_id)
    if cc.concurrency:
        return chimera.concurrency.blackhole(track, 'track')
    ds = sp_track(track, session)
    cli.utils.parse_ds(ds)
def grab_album(album_id):
    print('Not implemented for Spotify!')
def grab_playlist(playlist_id, session):
    """session is respective active service for
    spotify conversion"""
    try:
        if playlist_id == 'all':
            grab_all_playlists(session)
        else:
            playlist = chimera.spotify.get_playlist(playlist_id)
            if cc.concurrency:
                return chimera.concurrency.blackhole(playlist, 'playlist')
            any_playlist(playlist, session, m3u=cc.m3u, log_missing=True)
    except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
        print(30 * '#')
        print('Download crashed restarting...')
        print(30 * '#')
        grab_playlist(playlist_id, session)

def grab_all_playlists(session):
    _playlists = chimera.spotify.get_user_playlists_data()
    if cc.concurrency:
        bar = tqdm(total=len(_playlists), unit='Playlists', ncols=100)

    # blacklist handling
    spotify_blacklist = [s.strip() for s in cc.spotify_blacklist.split(',')]
    _playlists = [x for x in _playlists if x['id'] not in spotify_blacklist]

    missing_tracks = []
    for _playlist in _playlists:
        playlist = chimera.spotify.get_playlist(_playlist['id'])
        # TODO handle missing tracks if conurrency is enabled
        if cc.concurrency:
            bar.update(1)
            chimera.concurrency.blackhole(playlist, 'playlist')
        else:
            missing_tracks.extend(
                any_playlist(playlist, session, m3u=True, log_missing=False)
            )
    if len(missing_tracks) > 0:
        chimera.utils.write_missing_csv('spotify_playlists', missing_tracks)

    if cc.concurrency:
        bar.close()

def grab_saved(session, playlist=None):
    if playlist == None:
        playlist = chimera.spotify.get_user_saved()
    try:
        if cc.concurrency:
            chimera.concurrency.blackhole(playlist, 'playlist')
        else:
            any_playlist(playlist, session, m3u=cc.m3u, log_missing=True)
    except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
        print(30 * '#')
        print('Download crashed restarting...')
        print(30 * '#')
        cli.utils.master_login(**{str(session).lower(): session})
        grab_saved(session, playlist=playlist)

def search_track(session):
    pass
def search_album(session):
    pass
def show_playlists(session):
    playlists = chimera.spotify.get_user_playlists_data()
    cli.dtq_cli.ptable(playlists, blacklist=['image', 'description'], truncated=False, row_number=False)


def conversion_test(session):
    playlist = chimera.spotify.get_playlist('28PGaOL3d0jpyfKkGQiuzk')
    # playlist = chimera.spotify.get_playlist('37i9dQZF1DXcx1szy2g67M', 'spotify')
    services = {str(session).lower(): session}
    results = []
    for sptrack in playlist.songs:
        match = search_track_on_services(sptrack.title, sptrack.artist, sptrack.album.title, **services, conversion_test=True)
        results.append({'spotify': sptrack, 'match': match})


    import csv
    with open('import/conversion.csv', 'w', newline='', encoding='utf_8_sig') as f:
        writer = csv.writer(f, delimiter=';', escapechar='')
        writer.writerow(['track_name', 'artist', 'album', 'release_date', 'seconds', 'isrc',
                         'track_name_match', 'artist_match', 'album_match', 'id', 'type', 'ratio', 'match_type'])
        for res in results:
            sptrack = res['spotify']
            match = res['match']
            if match == None:
                match = {
                    'track': {'title': '', 'artist': '', 'album': '', 'id': '', 'type': ''},
                    'ratio': '',
                    'match_type': '',
                }
            writer.writerow([sptrack.title, sptrack.artist, sptrack.album.title, sptrack.album.date, sptrack.duration, sptrack.isrc,
                             match['track']['title'], match['track']['artist'], match['track']['album'],
                             match['track']['id'], match['track']['type'], match['ratio'], match['match_type']])


def multi_search(deezer, tidal, qobuz, napster, gpm):
    # import json
    # with open(r"D:\missing.json", 'r') as f:
    #     raw = f.read()
    #     data = json.loads(raw)
    data = [{'artist': 'Eminem', 'title': 'Berzerk', 'album': 'The Marshall Mathers LP2'}]
    services = {'deezer': deezer, 'qobuz': qobuz}
    # services = {'deezer': deezer, 'qobuz': qobuz,
    #             'napster': napster, 'gpm': gpm}
    results = []
    for song in data:
        match = search_track_on_services(song['title'], song['artist'], song['album'], **services, conversion_test=True)
        results.append({'raw': song, 'match': match})


    import csv
    with open('import/conversion2.csv', 'w', newline='', encoding='utf_8_sig') as f:
        writer = csv.writer(f, delimiter=';', escapechar='')
        writer.writerow(['track_name', 'artist',
                         'track_name_match', 'artist_match', 'album_match', 'id', 'type', 'ratio', 'match_type'])
        for res in results:
            song = res['raw']
            match = res['match']
            if match == None:
                match = {
                    'track': {'title': '', 'artist': '', 'album': '', 'id': '', 'type': ''},
                    'ratio': '',
                    'match_type': '',
                }
            writer.writerow([song['title'], song['artist'],
                             match['track']['title'], match['track']['artist'], match['track']['album'],
                             match['track']['id'], match['track']['type'], match['ratio'], match['match_type']])
