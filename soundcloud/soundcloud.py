"""
Soundcloud Endpoint, currently does not need login
can only download mp3 128kbps, supports tagging
soundcloud has mostly no albums, so track data does not contain any album data
folder structure slightly different to the rest:
    ARTIST\\ARTIST - TRACK NAME.EXT

Functions:
    Track download from URL or ID
    Playlist download from URL or ID
"""

import json
import os
import re
import time
import requests

import soundcloud.playlist
import soundcloud.track

API_URL = 'https://api.soundcloud.com/{}'
API_URL_GO = 'https://api-v2.soundcloud.com/{}'

TOKEN_PATH = os.path.join('tokens', 'soundcloud.token')

class Soundcloud:
    def __init__(self, username, email=None, password=None):
        self.session = requests.Session()
        self.logged_in = True # no login required
        self.username = username
        self.email = email
        self.password = password
        self.client_id = '7OzdeoyYOqcZHL6WPjwCS3HqdkgjvKID'
        self.client_id_go = 'nU21E2bvWDf1YkhHuchdIP5ioCC2QNBU'
        self.oauth_session_id = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'
        }
        self.headers_go = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
        }


    def __repr__(self):
        return 'SOUNDCLOUD'

    def call_api(self, path, params={}):
        """
        endpoint for api.soundcloud.com
        """
        url = API_URL.format(path)
        params['client_id'] = self.client_id
        args = {'params': params, 'headers': self.headers}
        res = self.session.get(url, **args)
        return res.json()

    def call_api_go(self, path, params={}):
        # import requests
        """endpoint for go api"""
        url = API_URL_GO.format(path)
        params['client_id'] = self.client_id_go

        if not self.oauth_session_id:
            with open(TOKEN_PATH, 'r') as f:
                token_info = json.loads(f.read())
            if time.time() > token_info['expires_at']:
                print('Token may be invalid!')
            self.oauth_session_id = token_info['access_token']
            # session = get_oauth_session(self.email, self.password)
            # if session:
            #     self.oauth_session_id = session
            # else:
            #     raise ValueError('NO OAUTH SESSION FOUND!')
        self.headers_go['Authorization'] = 'OAuth ' + self.oauth_session_id

        args = {'params': params, 'headers': self.headers_go}
        res = self.session.get(url, **args)
        return res.json()


    def get(self, url, params={}, client_id=False, go=False):
        """
        basic get webpage
        """
        if go:
            self.headers_go['Authorization'] = 'OAuth ' + self.oauth_session_id
            args = {'params': params, 'headers': self.headers_go}
            return self.session.get(url, **args)

        if client_id:
            params['client_id'] = self.client_id
        args = {'headers': self.headers, 'params': params}
        res = self.session.get(url, **args)
        return res

    def resolve(self, url):
        """
        resolves soundcloud urls to usable json format
        does not work on "discover" sets
        """
        url = 'http://api.soundcloud.com/resolve?url={}&client_id={}'.format(url, self.client_id)
        resolve = self.session.get(url)
        return resolve.json()


    def get_track_from_url(self, url):
        raw_data = self.resolve(url)
        return soundcloud.track.SoundcloudTrack.grab_or_create(raw_data['id'], raw_data=raw_data)

    def get_track_go_from_url(self, url):
        raw_data = self.resolve(url)
        raw_track = self.get_track_data(str(raw_data['id']), go=True)
        return soundcloud.track.SoundcloudTrack.grab_or_create(raw_data['id'], raw_data={**raw_data, **raw_track})


    def get_track(self, track_id):
        raw_data = self.get_track_data(track_id)
        return soundcloud.track.SoundcloudTrack.grab_or_create(track_id, raw_data=raw_data)

    def get_track_data(self, track_id, go=False):
        if go:
            return self.call_api_go('tracks/' + track_id)
        else:
            return self.call_api('tracks/' + track_id)

    def get_stream(self, stream_url):
        res = self.get(stream_url, params={'client_id': self.client_id})
        return soundcloud.track.SoundCloudTrackStream(res.url)

    def get_stream_go(self, stream_url):
        res = self.get(stream_url, go=True)
        data = self.session.get(res.json()['url'])
        return soundcloud.track.SoundcloudTrackStreamHLS(data.text)

    def get_playlist(self, playlist_id=None, raw_data=None):
        """needs testing for limit"""
        if raw_data == None:
            raw_data = self.call_api('playlists/{}'.format(playlist_id))
        playlist = soundcloud.playlist.SoundcloudPlaylist(raw_data)
        tracks = []
        # find out how pagination works on soundcloud
        for raw_track in raw_data['tracks']:
            tracks.append(
                soundcloud.track.SoundcloudTrack.grab_or_create(raw_track['id'], raw_data=raw_track)
            )
        playlist.songs = tracks
        return playlist

    def get_playlist_from_url(self, url):
        """grab playlist id from playlist page called set on soundcloud"""
        resolve = self.resolve(url)
        return self.get_playlist(raw_data=resolve)

    def get_user_playlists_data(self):
        """gets user playlists, only data mostly for api
        does not get tracks for playlist for performance use `get_playlist` for that"""
        raw_data = self.call_api('users/' + self.username + '/playlists')
        playlists = []
        for raw_playlist in raw_data:
            playlists.append({
                'id': raw_playlist['id'],
                'title': raw_playlist['title'],
                'description': raw_playlist.get('description', ''),
                'image': raw_playlist['artwork_url'],
                'length': raw_playlist['track_count'],
                'duration': raw_playlist['duration'],
                'type': 'soundcloud'

            })
        return playlists

    def get_track_from_url_old(self, url):
        # TODO deletes this
        # get hls urls
        hls_urls = self._extract_urls(self.get(url).text)

        if len(hls_urls) == 0:
            print('NO HLS URLS FOUND')
            return

        # get id
        track_id = re.findall(':[0-9][^/]*', hls_urls[0])[0].replace(':', '')
        return self.get_track(track_id)

    def _extract_urls(self, webpage):
        data = re.findall('https://api-v2.soundcloud.com/media/soundcloud:tracks:[^"]*', webpage)
        return data





def get_oauth_session(email, password):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.1',
        'Referer': 'https://soundcloud.com/',
        'Origin': 'https://soundcloud.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
        'Sec-Fetch-Mode': 'cors',
        'Content-Type': 'application/json',
    }

    params = (
        ('client_id', 'nU21E2bvWDf1YkhHuchdIP5ioCC2QNBU'),
        ('app_version', '1569492506'),
        ('app_locale', 'en'),
    )

    data = dict(
        client_id='nU21E2bvWDf1YkhHuchdIP5ioCC2QNBU',
        scope='fast-connect non-expiring purchase signup upload',
        recaptcha_pubkey='6LeAxT8UAAAAAOLTfaWhndPCjGOnB54U1GEACb7N',
        recaptcha_response=None,
        credentials={
            'identifier': email,
            'password': password
        },
        signature='',
        device_id='',
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
    )

    response = requests.post('https://api-v2.soundcloud.com/sign-in/password', headers=headers, params=params, data=json.dumps(data))

    if response.status_code == 201:
        response = response.json()
        return response['session']['access_token']
