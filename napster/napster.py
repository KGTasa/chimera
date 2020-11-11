import json
import os
import time
from typing import TYPE_CHECKING

import requests

import napster.album
import napster.playlist
import napster.track
from db import cc
from generic.utils import MissingNapsterApiKey, authrequired

if TYPE_CHECKING:
    from napster.track import NapsterTrack
    from napster.album import NapsterAlbum
    from napster.playlist import NapsterPlaylist


API_LOGIN_URL = 'https://playback.rhapsody.com/login.xml'
API_BASE_URL = 'https://api.napster.com/v2.2/{}'
# API_KEY = 'ZDU1MDMzMzItZTMwNy00YThiLThlYmQtZWUwNjBiZTJjNDZm'

RE_PASSWORD_HASH = r'<rhapsodyAccessToken \S.*>(?P<password_hash>\S.*)</rhapsodyAccessToken>'
RE_TOKEN = r'<token \S.*>(?P<token>\S.*)</token>'
token_regex = {'token': RE_TOKEN, 'password_hash': RE_PASSWORD_HASH}

TOKEN_PATH = os.path.join('tokens', 'napster.token')

class Napster:
    def __init__(self, api_token):
        self.session = requests.Session()
        self.http_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.user = None
        self.api_token = api_token
        self.token = None
        self.password_hash = None
        self.logged_in = False

    def __repr__(self):
        return 'NAPSTER'

    def call_api(self, path, headers={}, params={}):
        url = API_BASE_URL.format(path)
        headers = {**self.http_headers, **headers}
        if self.access_token:
            headers['Authorization'] = 'Bearer {}'.format(self.access_token)

        args = {
            'params': params,
            'headers': headers
        }
        res = self.session.get(url, **args)
        return res.json()


    def login(self, email, password):
        """
        login with token, if expired create one
        """
        if os.path.exists('tokens/napster'):
            os.rename('tokens/napster', TOKEN_PATH)
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, 'r') as f:
                token_info_str = f.read()
                token_info = json.loads(token_info_str)
            now = int(time.time())
            if token_info['expires_at'] < now:
                return self._login(email, password)
        else:
            return self._login(email, password)

        # token is still good
        # print('Logged in with cached token!')
        return self.post_login(token_info, text='')

    def post_login(self, token_info, text='(with new token)'):
        self.token_info = token_info
        self.access_token = token_info['access_token']
        self.logged_in = True
        return text

    def _login(self, email, password):
        """
        creates new token, oauth limit!
        """
        if self.api_token == '':
            raise MissingNapsterApiKey
        # This was used to get password hash for login
        # but it isn't needed anymore because api.napster
        # allows you to login with an unhashed password
        # res = self.session.post(
        #     API_LOGIN_URL, data={'username': email, 'password': password},
        #     headers={**self.http_headers}
        # )
        # # create new token
        token_info = {}
        # for name, reg in token_regex.items():
        #     re_search = re.search(reg, res.text)
        #     if re_search:
        #         re_search = re_search.groupdict()
        #         token_info[name] = re_search[name]

        res = requests.post(
            'https://api.napster.com/oauth/token',
            headers={
                'Authorization': 'Basic {}'.format(self.api_token),
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
            },
            data={
                'username': email,
                # 'password': token_info['password_hash'],
                'password': password,
                'grant_type': 'password'
            }
        ).json()
        # save token
        token_info['access_token'] = res['access_token']
        token_info['expires_at'] = int(time.time()) + int(res['expires_in'])
        token_info['username'] = res['username']
        token_info['token_type'] = res['token_type']
        with open(TOKEN_PATH, 'w') as f:
            json.dump(token_info, f, indent=2)

        return self.post_login(token_info)

    @authrequired
    def get_track(self, track_id) -> 'NapsterTrack':
        # napster track format : tra.ID
        # i want to store track_id as int so prepend tra.
        raw_data = self.call_api('tracks/tra.{}'.format(track_id))
        # napster can return multiple tracks for one single element
        # so we just grab element1
        if raw_data['meta']['returnedCount'] == 1:
            return napster.track.NapsterTrack.grab_or_create(
                track_id, raw_data=raw_data['tracks'][0], napster_session=self
            )

    def get_stream(self, track_id, quality):
        raw_data = self.call_api('streams', params=quality)
        if raw_data['meta']['returnedCount'] == 0:
            return 'NapsterNoTrackStream'
        return napster.track.NapsterTrackStream.grab_or_create(
            track_id, raw_data=raw_data['streams'][0]
        )

    @authrequired
    def get_album(self, album_id, full=True) -> 'NapsterAlbum':
        album_data = self.call_api(path='albums/{}'.format(album_id))
        album_pictures = self.call_api(path='albums/{}/images'.format(album_id))
        album_tracks = {}
        if full:
            album_tracks = self.call_api(path='albums/{}/tracks'.format(album_id))
        return napster.album.NapsterAlbum.grab_or_create(
            album_id, raw_data={'album': album_data['albums'][0], **album_pictures, **album_tracks}
        )

    @authrequired
    def get_playlist(self, playlist_id) -> 'NapsterPlaylist':
        limit = 100
        offset = 0
        args = {
            'limit': limit,
            'offset': offset
        }
        raw_playlist = self.call_api(path='playlists/{}'.format(playlist_id))
        playlist = napster.playlist.NapsterPlaylist(raw_data=raw_playlist['playlists'][0])
        total = raw_playlist['playlists'][0]['trackCount']
        tracks = []
        results = self._get_playlist(playlist_id, args)

        # every track has to grab its album
        # this is very slow...
        if cc.cli:
            from tqdm import tqdm
            bar = tqdm(total=playlist.song_count, unit='Track', ncols=100, desc='grabbing Tracks')
        while results:
            for raw_track in results['tracks']:
                _track = napster.track.NapsterTrack.grab_or_create(
                    raw_track['id'], raw_data=raw_track, napster_session=self
                )
                _track.is_playlist = True  # set playlist flag
                _track.playlist_name = playlist.name
                _track.playlist_index = str(len(tracks) + 1)
                _track.playlist_length = str(playlist.song_count)
                tracks.append(_track)
                if cc.cli:
                    bar.update(1)
            if total <= offset + limit:
                break
            else:
                offset += limit
                args['offset'] = offset
                results = self._get_playlist(playlist_id, args)
        playlist.songs = tracks
        if cc.cli:
            bar.close()
        return playlist



    def _get_playlist(self, playlist_id, args={}):
        """helper for `get_playlist`"""
        return self.call_api(
            path='playlists/{}/tracks'.format(playlist_id),
            params=args
        )

    @authrequired
    def search_track(self, q, limit=10):
        raw_data = self.call_api('search', params={'query': q, 'type': 'track', 'per_type_limit': limit})
        track_list = []
        for track_data in raw_data['search']['data']['tracks']:
            track_list.append({
                'id': track_data['id'].replace('tra.', ''), # fix track id
                'title': track_data['name'],
                'artist': track_data['artistName'],
                'album': track_data['albumName'],
                'explicit': track_data['isExplicit'],
                'type': 'napster',
                'album_id': track_data['albumId'],
                'isrc': track_data['isrc']
            })

        if len(track_list) < limit:
            return track_list
        return track_list[0:limit]

    @authrequired
    def search_album(self, q, limit=10):
        raw_data = self.call_api('search', params={'query': q, 'type': 'album', 'per_type_limit': limit})
        albums = []
        for raw_album in raw_data['search']['data']['albums']:
            albums.append({
                'id': raw_album['id'],
                'title': raw_album['name'],
                'artist': raw_album['artistName'],
                'song_count': raw_album['trackCount'],
                'type': 'napster'
            })

        if len(albums) < limit:
            return albums
        return albums[0:limit]

    @authrequired
    def get_user_playlists_data(self):
        raw_data = self.call_api(path='me/library/playlists')
        playlists = []
        for raw_playlist in raw_data['playlists']:
            playlists.append({
                'id': raw_playlist['id'],
                'title': raw_playlist['name'],
                'description': raw_playlist['description'],
                'image': raw_playlist['images'][0],
                'length': raw_playlist['trackCount'],
                'duration': '0',
                'type': 'napster'
            })
        return playlists
