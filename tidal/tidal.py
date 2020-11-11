

import uuid

import requests

import tidal.playlist
import tidal.video
import tidal.track
import tidal.utils

from generic.utils import authrequired, InvalidTidalToken
from db import cc # for video stream

import typing
if typing.TYPE_CHECKING:
    from tidal.track import TidalTrack

class Tidal:
    def __init__(self):
        self.session = requests.Session()
        self.session_id = None
        self.video_session_id = None
        self.country_code = 'US'
        self.user_id = None
        self.username = None
        self.proxies = tidal.utils.proxies
        self.logged_in = False

    def __repr__(self):
        return 'TIDAL'

    def call_private_api(self, path, params={}, headers={}, post=False, form=False, no_session=False):
        url = tidal.utils.PRIVATE_API_URL % path
        params['countryCode'] = self.country_code

        if self.session_id != None and no_session == False:
            headers['X-Tidal-SessionId'] = self.session_id
        headers['User-Agent'] = 'TIDAL_ANDROID/686 okhttp/3.3.1'

        args = {
            'params': params,
            'headers': headers
        }
        if form:
            args['data'] = form
        if post:
            res = self.session.post(url, **args, proxies=self.proxies)
        else:
            res = self.session.get(url, **args, proxies=self.proxies)
        return res


    def login(self, username, password, bymobile=False):
        # more info about tokens: https://github.com/arnesongit/plugin.audio.tidal2/blob/master/resources/lib/koditidal.py#L781
        # token = 'BI218mwp9ERZ3PFI' # audirvana dead
        # token = 'kgsOOmYk3zShYrNP' # android token, only 16bit
        token = 'u5qPNNYIbD0S0o36MrAiFZ56K6qMCrCmYPzZuTnV' # 24 bit encrypted
        # token = '4zx46pyr9o8qZNRw' # native encrypted streams

        data = self.call_private_api(
            path='login/username',
            params={'token': token},
            form={
                'username': username,
                'password': password,
                'clientUniqueKey': str(uuid.uuid4()).replace('-', '')[16:]
            },
            post=True
        ).json()

        if 'status' in data:
            if data['status'] == 401:
                if data['userMessage'] == 'Invalid token':
                    raise InvalidTidalToken
                raise 'username or password is wrong'
            else:
                raise 'unkown error getting session id'
        else:
            self.session_id = data['sessionId']
            self.user_id = data['userId']
            self.country_code = data['countryCode']


        # get user profile
        data = self.call_private_api('users/{}'.format(self.user_id)).json()
        if 'status' in data and not data['status'] == 200:
            raise 'unkown error getting user profile'

        self.logged_in = True
        self.username = data['username']
        return {'username': username}


    def proxy_test(self):
        url = 'https://api.ipify.org?format=json'
        res = self.session.get(url, proxies=self.proxies)
        print(res.text)


    def get_stream(self, track_id, quality):
        stream_data = self.call_private_api('tracks/%i/streamUrl' % track_id, params = {'soundQuality': quality}).json()
        if 'status' in stream_data:
            if stream_data['status'] == 401:
                if stream_data['subStatus'] == 4005:
                    return 'Asset is not ready for playback'
                return "Asset is not available in user's location"
        return tidal.track.TidalTrackStream.grab_or_create(
            track_id,
            raw_data=stream_data
        )

    @authrequired
    def get_track(self, track_id) -> 'TidalTrack':
        raw_data = self.get_track_data(track_id)
        if raw_data is None:
            return None
        else:
            return tidal.track.TidalTrack.grab_or_create(track_id, raw_data=raw_data)

    def get_track_data(self, track_id):
        res = self.call_private_api('tracks/{}'.format(track_id))
        if res.status_code == 404:
            # track was not found
            return None
        return res.json()

    def get_album_data(self, album_id):
        res = self.call_private_api('albums/{}'.format(album_id)).json()
        return res

    def get_album_tracks_data(self, album_id):
        return self.call_private_api('albums/{}/tracks'.format(album_id)).json()

    def get_album_full_data(self, album_id):
        return {**self.get_album_data(album_id),
                'songs': self.get_album_tracks_data(album_id)}

    @authrequired
    def get_album(self, album_id):
        raw_data = self.get_album_full_data(album_id)
        if 'status' in raw_data:
            if raw_data['status'] == 404:
                return None
        if tidal.album.TidalCompilation.check(raw_data):
            return tidal.album.TidalCompilation.grab_or_create(album_id, raw_data=raw_data)
        return tidal.album.TidalAlbum.grab_or_create(album_id, raw_data=raw_data)

    def get_artist_data(self, artist_id):
        return self.call_private_api('artists/{}'.format(artist_id)).json()

    @authrequired
    def get_albums_from_artist(self, artist_id):
        limit = 10
        params = {'limit': limit}
        results = self._get_albums_from_artist(artist_id, params)
        total = results['totalNumberOfItems']
        offset = results['offset']
        albums = []
        while results:
            for raw_album in results['items']:
                albums.append(self.get_album(raw_album['id']))
            if total <= offset + limit:
                break
            else:
                offset += limit
                params['offset'] = offset
                results = self._get_albums_from_artist(artist_id, params)

        # get eps and singles
        albums.extend(self.get_eps_and_singles_from_artist(artist_id))
        return albums

    @authrequired
    def get_eps_and_singles_from_artist(self, artist_id):
        results = self._get_albums_from_artist(artist_id, params={'limit': 100, 'filter': 'EPSANDSINGLES'})
        albums = [self.get_album(raw_album['id']) for raw_album in results['items']]
        return albums

    def _get_albums_from_artist(self, artist_id, params={}):
        """helper function for `get_albums_from_artist`"""
        return self.call_private_api(
            path='artists/{}/albums'.format(artist_id),
            params=params
        ).json()

    @authrequired
    def get_artist(self, artist_id):
        # TODO needs some work
        # raw_data = {**self.get_artist_data(artist_id), **self.get_albums_from_artist(artist_id)}
        raw_data = self.get_artist_data(artist_id)
        raw_epsingles = self.get_eps_and_singles_from_artist(artist_id)
        return tidal.artist.TidalArtist.grab_or_create(artist_id, raw_data=raw_data)

    # @timeit
    @authrequired
    def search_track(self, q, limit=15):
        """fast search does not return track objects"""
        raw_data = self.call_private_api(
            path='search/tracks',
            params={'query': q, 'limit': '15'}
        ).json()
        track_list = []
        for track_data in raw_data['items']:
            track_list.append({
                'id': track_data['id'],
                'title': track_data['title'],
                'artist': track_data['artist']['name'],
                'album': track_data['album']['title'],
                'explicit': track_data['explicit'],
                'type': 'tidal',
                'album_id': track_data['album']['id'],
                'isrc': track_data['isrc'],
                'cover': tidal.utils.IMG_URL.format(track_data['album']['cover'].replace('-', '/'))
            })
        if len(track_list) < limit:
            return track_list
        return track_list[0:limit]

    # @timeit
    @authrequired
    def search_album(self, q, limit=15):
        """doesn't make much sense in creating an album object for search
        just grab it later...."""
        raw_data = self.call_private_api(
            path='search/albums',
            params={'query': q, 'limit': '15'}
        ).json()
        album_list = []
        for album_data in raw_data['items']:
            album_list.append({
                'id': album_data['id'],
                'title': album_data['title'],
                'artist': album_data['artist']['name'],
                'song_count': album_data['numberOfTracks'],
                'type': 'tidal'
            })
        if len(album_list) < limit:
            return album_list
        return album_list[0:limit]


    @authrequired
    def get_playlist(self, playlist_id):
        limit = 100
        params = {'limit': limit}
        results = self._get_playlist_tracks(playlist_id, params=params)
        playlist = tidal.playlist.TidalPlaylist(self._get_playlist(playlist_id))
        total = results['totalNumberOfItems']
        offset = results['offset']
        tracks = []
        while results:
            for raw_track in results['items']:
                _track = tidal.track.TidalTrack.grab_or_create(
                    raw_track['id'],
                    raw_data=raw_track
                )
                _track.is_playlist = True  # set playlist flag
                _track.playlist_name = playlist.name
                _track.playlist_index = str(len(tracks) + 1)
                _track.playlist_length = str(playlist.song_count)
                tracks.append(_track)
            if total <= offset + limit:
                break
            else:
                offset += limit
                params['offset'] = offset
                results = self._get_playlist_tracks(playlist_id, params)

        # append songs to playlist object
        playlist.songs = tracks
        return playlist

    def _get_playlist(self, playlist_id):
        """helper for `get_playlist` gets playlist data"""
        return self.call_private_api(
            path='playlists/' + playlist_id
        ).json()

    def _get_playlist_tracks(self, playlist_id, params={}):
        """helper for `get_playlist` gets playlist tracks"""
        return self.call_private_api(
            path='playlists/' + playlist_id + '/tracks',
            params=params
        ).json()

    def get_playlist_data(self, playlist_id):
        """for api only"""
        limit = 100
        params = {'limit': limit}
        results = self._get_playlist_tracks(playlist_id, params=params)
        playlist = self._get_playlist(playlist_id)
        total = results['totalNumberOfItems']
        offset = results['offset']
        tracks = []
        while results:
            for raw_track in results['items']:
                tracks.append(raw_track)
            if total <= offset + limit:
                break
            else:
                offset += limit
                params['offset'] = offset
                results = self._get_playlist_tracks(playlist_id, params)

        # append songs to playlist object
        playlist['songs'] = tracks
        return playlist

    @authrequired
    def get_user_playlists_data(self):
        """gets user playlists, only data mostly for api
        does not get tracks for playlist for performance use `get_playlist` for that"""
        raw_data = self.call_private_api(
            path='users/{}/playlists'.format(self.user_id),
        ).json()
        playlists = []
        for raw_playlist in raw_data['items']:
            image = tidal.utils.ARTIST_IMG_URL.format(width=512, height=512, id=raw_playlist['uuid'], id_type='uuid')
            playlists.append({
                'id': raw_playlist['uuid'],
                'title': raw_playlist['title'],
                'description': raw_playlist['description'],
                'image': image,
                'length': raw_playlist['numberOfTracks'],
                'duration': raw_playlist['duration'],
                'type': 'tidal'

            })
        return playlists

    @authrequired
    def get_video(self, video_id):
        raw_data = self.call_private_api(path='videos/{}'.format(video_id)).json()
        return tidal.video.TidalVideo(raw_data)

    @authrequired
    def get_videos_from_artist(self, artist_id):
        raw_data = self.call_private_api(
            path='artists/{}/videos'.format(artist_id),
            params={'limit': 1000}
        ).json()

        videos = []
        for raw_video in raw_data['items']:
            videos.append(tidal.video.TidalVideo(raw_video))
        return videos


    @authrequired
    def search_videos(self, q):
        raw_data = self.call_private_api(path='search/videos', params={'query': q}).json()
        videos = []
        for raw_video in raw_data['items']:
            videos.append(tidal.video.TidalVideo(raw_video))
        return videos

    def get_stream_video(self, video_id, quality):
        """gets url for m3u8 file
        For full quality hls videos we use the default token
        which requires a new session"""
        def _login():
            """handle video token login"""
            token = 'wdgaB1CilGA-S_s2'
            data = self.call_private_api(
                path='login/username',
                params={'token': token},
                form={'username': cc.tidal_email, 'password': cc.tidal_password,
                      'clientUniqueKey': str(uuid.uuid4()).replace('-', '')[16:]},
                post=True,
                no_session=True
            ).json()
            self.video_session_id = data['sessionId']

        if self.video_session_id == None:
            _login()

        url = tidal.utils.PRIVATE_API_URL % 'videos/{}/streamUrl'.format(video_id)
        params = {'videoQuality': quality, 'countryCode': self.country_code}
        headers = {'X-Tidal-SessionId': self.video_session_id}
        raw_data = requests.get(url, params=params, headers=headers).json()
        return self.session.get(raw_data['url']).text
