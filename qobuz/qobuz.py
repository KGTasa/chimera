# 1. standard
import hashlib
import re
import time
from typing import TYPE_CHECKING
from urllib.parse import urlencode

# 2. third party
import requests

# 3. local
import qobuz.album
import qobuz.playlist
import qobuz.seed
import qobuz.track
import qobuz.utils
from db import cc
from generic.utils import (InvalidOrMissingAppID, InvalidQobuzSubscription,
                           authrequired)

if TYPE_CHECKING:
    from qobuz.track import QobuzTrack
    from qobuz.album import QobuzAlbum
    from qobuz.playlist import QobuzPlaylist


class Qobuz:
    def __init__(self):
        self.session = requests.Session()
        self.app_id = None
        self.user_auth_token = None
        self.subscription_type = None
        self.logged_in = False
        self.user_id = None
        # self.qobuz_secret = qobuz_secret
        self.http_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Content-Language': 'en-US',
            'Cache-Control': 'max-age=0',
            'Accept': '*/*',
            'Accept-Charset': 'utf-8,ISO-8859-1;q=0.7,*;q=0.3',
            'Accept-Language': 'en-US,en;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive'
        }

    def __repr__(self):
        return 'QOBUZ'

    def call_api(self, path, args={}):
        """call qobuz api
        Args:
            path = /user/login
            args = {}
        Returns:
            json
        """
        if self.app_id != None:
            self.http_headers['X-App-Id'] = self.app_id
        if self.user_auth_token != None:
            self.http_headers['X-User-Auth-Token'] = self.user_auth_token
        res = self.session.get(
            qobuz.utils.API_URL + path + '?' + urlencode(args),
            headers=self.http_headers
        )
        if res.status_code >= 500:
            res.raise_for_status()
        return res.json()

    def login(self, email, password, app_id):
        user = self.call_api(
            path='user/login',
            args={
                'email': email,
                'password': password,
                'app_id': app_id
            })
        # check for invalid app id
        if 'code' in user:
            if user['code'] == 400:
                raise InvalidOrMissingAppID

        # check if free account
        sub_desc = user['user']['credential']['description']
        if sub_desc in ['Qobuz Lid', 'Qobuz Member']:
            raise InvalidQobuzSubscription
            #pass
        self.subscription_type = user['user']['credential']['parameters']['label']
        #self.subscription_type = 'Invalid'
        self.app_id = app_id
        # getting user auth token
        self.user_auth_token = user['user_auth_token']
        self.logged_in = True
        self.user_id = user['user']['id']
        return {'user': user['user']['display_name'], 'subscription': self.subscription_type}

    def get_type_seed(self):
        return None

    def get_appid_and_secret(self):
        qobuz.seed.get_appid_secrets()

    @authrequired
    def get_track(self, track_id, compilation=None) -> 'QobuzTrack':
        """set compilation flag if the track is in a compilation"""
        raw_data = self.get_track_data(track_id)
        # check for 404
        if raw_data.get('code') == 404:
            return None
        return qobuz.track.QobuzTrack.grab_or_create(
            track_id,
            raw_data=raw_data,
            compilation=compilation
        )

    def get_track_data(self, track_id):
        return self.call_api(
            'track/get',
            args={'track_id': track_id}
        )

    def get_stream(self, track_id, quality):
        _time = time.time()
        request_sig = hashlib.md5(
            qobuz.utils.STREAM_URL.format(quality, track_id, _time, qobuz.seed.get_secret()).encode('utf-8')
        ).hexdigest()

        res = self.call_api(
            path='track/getFileUrl',
            args={
                'request_ts': _time,
                'request_sig': request_sig,
                'track_id': track_id,
                'format_id': quality,
                'intent': 'stream'
            })
        for restriction in res.get('restrictions', []):
            if restriction['code'] == 'TrackRestrictedByRightHolders':
                return 'TrackRestrictedByRightHolders'
        if res.get('code', 0) == 400:
            return 'Invalid Qobuz Secret'
        return qobuz.track.QobuzTrackStream.grab_or_create(
            track_id,
            raw_data=res
        )

    @authrequired
    def get_album(self, album_id) -> 'QobuzAlbum':
        # album api call only gives halve the track information
        # so on every track we call qobuz.get_track()
        # and for that we need the qobuz session
        raw_data = self.get_album_data(album_id)
        if qobuz.album.QobuzCompilation.check(raw_data):
            return qobuz.album.QobuzCompilation.grab_or_create(
                album_id,
                raw_data=raw_data,
                qobuz_session=self
            )
        return qobuz.album.QobuzAlbum.grab_or_create(
            album_id,
            raw_data=raw_data,
            qobuz_session=self
        )

    def get_album_data(self, album_id):
        res = self.call_api(
            path='album/get',
            args={'album_id': album_id}
        )
        return res

    @authrequired
    def get_playlist(self, playlist_id) -> 'QobuzPlaylist':
        args = {
            'app_id': self.app_id,
            'playlist_id': playlist_id,
            'extra': 'tracks'
        }
        results = self._get_playlist(playlist_id, args=args)
        playlist = qobuz.playlist.QobuzPlaylist(results)
        total = results['tracks']['total']
        offset = results['tracks']['offset']
        limit = 50
        tracks = []
        while results:
            for raw_track in results['tracks']['items']:
                _track = qobuz.track.QobuzTrack.grab_or_create(
                    raw_track['id'],
                    raw_data=raw_track,
                    is_playlist_track=True
                )
                if _track:
                    _track.is_playlist = True  # set playlist flag
                    _track.playlist_name = playlist.name
                    _track.playlist_index = str(len(tracks) + 1)
                    _track.playlist_length = str(playlist.song_count)
                    tracks.append(_track)
            if total <= offset + limit:
                break
            else:
                offset += limit
                args['offset'] = offset
                results = self._get_playlist(playlist_id, args)

        # append songs to playlist object
        playlist.songs = tracks
        return playlist

    def _get_playlist(self, playlist_id, args={}):
        """helper function only used for `get_playlist`"""
        return self.call_api(
            path='playlist/get',
            args=args
        )

    def get_playlist_data(self, playlist_id):
        """fast only used for api"""
        args = {
            'app_id': self.app_id,
            'playlist_id': playlist_id,
            'extra': 'tracks'
        }
        results = self._get_playlist(playlist_id, args=args)
        playlist = results
        total = results['tracks']['total']
        offset = results['tracks']['offset']
        limit = 50
        tracks = []
        while results:
            for raw_track in results['tracks']['items']:
                tracks.append(raw_track)
            if total <= offset + limit:
                break
            else:
                offset += limit
                args['offset'] = offset
                results = self._get_playlist(playlist_id, args)

        # append songs to playlist object
        playlist.pop('tracks')
        playlist['songs'] = tracks
        return playlist

    # @timeit
    @authrequired
    def search_track(self, q, limit=15):
        """fast search only returns dictionary"""
        raw_data = self.call_api(
            path='track/search',
            args={'query': q, 'limit': '15'}
        )
        track_list = []
        for track_data in raw_data['tracks']['items']:
            # remove unusable tracks, maybe some slip through because of playlist and album, => chimera.download
            if track_data['streamable'] != False or track_data['hires_streamable'] != False:
                track_list.append({
                    'id': track_data['id'],
                    'title': track_data['title'],
                    'artist': track_data['album']['artist']['name'],
                    'album': track_data['album']['title'],
                    'explicit': track_data['parental_warning'],
                    'type': 'qobuz',
                    'album_id': track_data['album']['id'],
                    'isrc': track_data['isrc'],
                    'cover': track_data['album']['image']['large']
                })
        if len(track_list) < limit:
            return track_list
        return track_list[0:limit]

    # @timeit
    @authrequired
    def search_album(self, q, limit=15):
        """doens't make much sense in creating an album object for
        each search, grab it later"""
        raw_data = self.call_api(
            path='album/search',
            args={'query': q, 'limit': '15'}
        )
        album_list = []
        for album_data in raw_data['albums']['items']:
            album_list.append({
                'id': album_data['id'],
                'title': album_data['title'],
                'artist': album_data['artist']['name'],
                'song_count': album_data['tracks_count'],
                'type': 'qobuz'
            })
        if len(album_list) < limit:
            return album_list
        return album_list[0:limit]


    @authrequired
    def get_user_playlists_data(self):
        """gets user playlists, only data mostly for api
        does not get tracks for playlist for performance use `get_playlist` for that"""
        raw_data = self.call_api(
            path='playlist/getUserPlaylists',
            args={'user_id': self.user_id})
        playlists = []
        for raw_playlist in raw_data['playlists']['items']:
            playlists.append({
                'id': raw_playlist['id'],
                'title': raw_playlist['name'],
                'description': raw_playlist.get('description', ''),
                'image': raw_playlist['images300'],
                'length': raw_playlist['tracks_count'],
                'duration': raw_playlist['duration'],
                'type': 'qobuz'

            })
        return playlists

    @authrequired
    def get_user_saved(self) -> 'QobuzPlaylist':
        results = self.get_user_saved_data(limit=500)
        tracks = []
        for raw_track in results['items']:
            tracks.append(
                self.get_track(raw_track['id'])
            )

        dummy_playlist = {
            'name': 'Qobuz Saved Tracks',
            'id': '000000',
            'tracks_count': len(tracks),
            'is_public': 'False',
            'owner': {'name': 'Me'}
        }
        playlist = qobuz.playlist.QobuzPlaylist(dummy_playlist)
        playlist.songs = tracks
        return playlist

    def get_user_saved_data(self, offset=0, limit=0, source='favorites'):

        _time = time.time()
        request_sig = hashlib.md5(
            'userLibrarygetTracksListlimit{limit}offset{offset}source{source}{time}{secret}'.format(
                limit=limit, offset=offset, source=source, time=_time, secret=qobuz.seed.get_secret()).encode('utf-8')
        ).hexdigest()

        raw_tracks = self.call_api(
            path='userLibrary/getTracksList',
            args = {
                'request_ts': _time,
                'request_sig': request_sig,
                'source': source,
                'offset': offset,
                'limit': limit
            }
        )
        return raw_tracks

    @authrequired
    def get_albums_from_artist(self, artist_id):
        limit = 25
        args = {
            'artist_id': artist_id,
            'extra': 'albums',
            'limit': limit,
            'offset': 0
        }
        results = self._get_albums_from_artist(args=args)
        total = results['albums_count']
        offset = results['albums']['offset']
        albums = []
        while results:
            for raw_album in results['albums']['items']:
                albums.append(self.get_album(raw_album['id']))
            if total <= offset + limit:
                break
            else:
                offset += limit
                args['offset'] = offset
                results = self._get_albums_from_artist(args=args)
        return albums


    def _get_albums_from_artist(self, args={}):
        """
        private function only used for `get_albums_from_artist`
        """
        return self.call_api(path='artist/get', args=args)

    def get_label(self, label_id):
        import copy
        limit = 50
        offset = 0
        args = {
            'label_id': label_id,
            'extra': 'albums',
            'limit': limit,
            'offset': offset
        }
        results = self._get_label(args)
        raw_label = copy.copy(results)
        total = results['albums']['total']
        albums = []

        if cc.cli:
            from tqdm import tqdm
            bar = tqdm(total=total, unit='Albums', ncols=100, desc='grabbing Label Metadata')

        while results:
            for raw_album in results['albums']['items']:
                albums.append(self.get_album(raw_album['id']))
                if cc.cli:
                    bar.update(1)
            if total <= offset + limit:
                break
            else:
                offset += limit
                args['offset'] = offset
                results = self._get_label(args)
        if cc.cli:
            bar.close()
        return raw_label, albums

    def _get_label(self, args):
        return self.call_api(path='label/get', args=args)
