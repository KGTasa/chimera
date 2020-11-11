
import os
import time
import webbrowser

import spotipy
import spotipy.oauth2 as oauth2

from app import toggle_flask_thread
from db import cc

TOKEN_PATH = os.path.join('tokens', 'spotify.token')

def create_token(open_auth_url=True):
    """
    Gets cached token, if not found opens spotify auth_url
    """
    # remove me
    old_path = os.path.join('tokens', '.cache-' + cc.spotify_username)
    if os.path.exists(old_path):
        os.rename(old_path, TOKEN_PATH)

    sp_oauth = oauth2.SpotifyOAuth(
        cc.spotify_client_id,
        cc.spotify_client_secret,
        cc.spotify_redirect_uri,
        scope=cc.spotify_scope,
        # cache_path=os.path.join('tokens', '.cache-' + cc.spotify_username)
        cache_path=TOKEN_PATH
    )
    token_info = sp_oauth.get_cached_token()

    if not token_info:
        # check if tests are being run
        if open_auth_url is False:
            return False

        # Not cached token found, redirect user to auth_url
        auth_url = sp_oauth.get_authorize_url()
        # start webserver for callback url
        toggle_flask_thread(state=True)
        # wait for flask and webbrowser to load
        time.sleep(3)
        webbrowser.open(auth_url)
        return False
        # TODO sleep for 20sec?? check if token was created, or callback method app.create_token
    if token_info:
        return token_info['access_token']

def get_all_playlists(token):
    """
    Get all playlists (soft limit 50)
    """
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_playlists(limit=50)
    response = []
    while results:
        response = response + results['items']
        if results['next']:
            results = sp.next(results)
        else:
            results = None
    return response


def get_all_saved_tracks(token):
    """get all saved (liked) tracks"""
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    response = []
    while results:
        for raw_track_data in results['items']:
            response.append(SpotifyTrack(raw_track_data['track']))
        if results['next']:
            results = sp.next(results)
        else:
            results = None
    return response


def get_saved_tracks(token):
    """get 20 saved (liked) tracks"""
    sp = spotipy.Spotify(auth=token)
    results = sp.current_user_saved_tracks()
    response = []
    for raw_track_data in results['items']:
        response.append(SpotifyTrack(raw_track_data['track']))
    return response


def get_artist_top_tracks(token, artist_id):
    # 7iWiAD5LLKyiox2grgfmUT
    sp = spotipy.Spotify(auth=token)
    results = sp.artist_top_tracks(artist_id=artist_id)
    res = []
    for raw_track_data in results['tracks']:
       res.append(SpotifyTrack(raw_track_data))
    return res

def get_user():
    """gets spotify user with cached token"""
    token = create_token()
    if token:
        sp = spotipy.Spotify(auth=token)
        sp_user = sp.user(cc.spotify_username)
        from pprint import pprint
        pprint(sp_user)



def get_playlist_data(playlist_id):
    """get tracks from playlist_id return SpotifyTrack object"""
    token = create_token()
    if token:
        sp = spotipy.Spotify(auth=token)
        results = sp.user_playlist(cc.spotify_username, playlist_id=playlist_id)
        results = results['tracks']
        tracks = []
        while results:
            for raw_track_data in results['items']:
                tracks.append(SpotifyTrack(raw_track_data['track']))
            if results['next']:
                results = sp.next(results)
            else:
                results = None

        return tracks


def get_track(song_id):
    token = create_token()
    if token:
        sp = spotipy.Spotify(auth=token)
        return SpotifyTrack(sp.track(song_id))

def get_playlist(playlist_id, user=cc.spotify_username):
    token = create_token()
    if token:
        sp = spotipy.Spotify(auth=token)
        playlist = SpotifyPlaylist(sp.user_playlist(user, playlist_id))
        tracks = []
        for _track in get_playlist_data(playlist_id):
            _track.is_playlist = True  # set playlist flag
            _track.playlist_name = playlist.name
            _track.playlist_index = str(len(tracks) + 1)
            _track.playlist_length = str(playlist.song_count)
            tracks.append(_track)
        playlist.songs = tracks
        return playlist

def get_user_playlists_data():
    token = create_token()
    if token:
        raw_data = get_all_playlists(token)
        playlists = []
        for raw_playlist in raw_data:
            playlists.append({
                'id': raw_playlist['id'],
                'title': raw_playlist['name'],
                'description': '',
                'image': raw_playlist['images'][0]['url'],
                'length': raw_playlist['tracks']['total'],
                'duration': '0',
                'type': 'spotify'

            })
        return playlists

def get_user_saved():
    token = create_token()
    if token:
        tracks = get_all_saved_tracks(token=token)
        dummy_playlist = {
            'name': 'Spotify Saved Tracks',
            'id': '000000',
            'tracks': {'total': len(tracks)},
            'collaborative': False,
            'owner': {'display_name': 'Me'}
        }
        playlist = SpotifyPlaylist(dummy_playlist)
        playlist.songs = tracks
        return playlist

class SpotifyTrack():
    def __init__(self, raw_data):
        self.title = raw_data['name']
        self.song_id = raw_data['id']
        self.artist = raw_data['artists'][0]['name']
        self.album = SpotifyAlbum(raw_data)
        self.year = self.album.date.split('-')[0]
        self.isrc = raw_data['external_ids'].get('isrc', None)
        # self.isrc = raw_data['external_ids'].get('isrc', None)
        self.duration = int(raw_data['duration_ms'] / 1000)
        self.service = 'spotify'

        self.is_playlist = False
        self.playlist_name = None
        self.playlist_index = None
        self.playlist_length = None

    def __repr__(self):
        return f'ID {self.song_id} Track: {self.title}, Artist: {self.artist}, Album: {self.album.title}, Type: SpotifyTrack'

class SpotifyAlbum():
    def __init__(self, raw_data):
        self.album_id = raw_data['album']['id']
        self.title = raw_data['album']['name']
        self.date = raw_data['album']['release_date']

class SpotifyPlaylist():
    def __init__(self, raw_data):
        self.name = raw_data['name']
        self.playlist_id = raw_data['id']
        self.song_count = raw_data['tracks']['total']
        self.is_public = raw_data['collaborative']
        self.description = raw_data.get('description', '')
        self.owner = raw_data['owner']['display_name']
        self.songs = []
