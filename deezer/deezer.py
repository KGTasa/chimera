import json
import os
import pickle
from typing import TYPE_CHECKING, List
from urllib.parse import urlencode
import random
import requests
import requests.cookies
from ratelimit import limits, sleep_and_retry

import deezer.album
import deezer.artist
import deezer.episode
import deezer.playlist
import deezer.show
import deezer.track
import deezer.utils
from config import log
from generic.utils import authrequired, retry_and_reauth, ValidTokenRequired
FIVE_MINUTES = 300
FIVE_SECONDS = 5
TOKEN_PATH = os.path.join('tokens', 'deezer.token')

if TYPE_CHECKING:
    from deezer.track import DeezerTrack
    from deezer.album import DeezerAlbum
    from deezer.playlist import DeezerPlaylist

class Deezer:
    def __init__(self):
        self.session = requests.Session()
        self.http_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
            'Content-Language': 'en-US',
            'Cache-Control': 'max-age=0',
            'Accept': '*/*',
            'Accept-Charset': 'utf-8,ISO-8859-1;q=0.7,*;q=0.3',
            'Accept-Language': 'en-US,en;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive'
        }
        self.user = None
        self.logged_in = False

    def __repr__(self):
        return 'DEEZER'

    @sleep_and_retry
    @limits(calls=50, period=FIVE_SECONDS)
    def call_private_api(self, method, args={}):
        query_string = {
            'api_version': '1.0',
            'api_token': 'null',
            'input': '3',
            'method': method,
            'cid': int(random.random() * 1e9)
        }

        if method != 'deezer.getUserData':
            query_string['api_token'] = self.get_api_token()

        res = self.session.post(
            deezer.utils.PRIVATE_API_URL % urlencode(query_string),
            data=args,
            headers=self.http_headers
        ).json()
        if res['error']:
            query_string.pop('api_token')
            dump = {**res['error'], **query_string, 'args': args}
            log.info(json.dumps(dump))
        return res


    @sleep_and_retry
    @retry_and_reauth
    @limits(calls=50, period=FIVE_SECONDS)
    def call_public_api(self, path, args={}):
        """
        Calls public api from Deezer
        https://developers.deezer.com/api/explorer?url=search/track%3Fq%3Deminem
        Args:
          path = /search/track
          args = {'q':'Eminem'}
        Returns:
          json
        """
        res = self.session.get(
            deezer.utils.PUBLIC_API_URL + path + '?' + urlencode(args)
        )
        data = res.json()
        if 'error' in data:
            if 'code' in data['error']:
                if data['error']['code'] == 800:
                    return None
        return data


    def get_api_token(self):
        json = self.call_private_api('deezer.getUserData')
        if 'checkFormLogin' in json['results']:
            return json['results']['checkFormLogin']
        elif 'checkForm' in json['results']:
            return json['results']['checkForm']
        else:
            raise "couldn't get api_token"


    def _post_login(self):
        """The function to call after login cookies have been set.
        It will make sure all cookies are set, and returns the user profile.
        It's not supposed to be called on normal usage."""
        result = self.session.get(
            'https://www.deezer.com/', headers=self.http_headers)
        if result.status_code != 200:
            raise "couldn't load deezer.com"

        result = self.call_private_api('deezer.getUserData')
        user_data = result['results']['USER']
        # self.user = {
        #     'id': user_data['USER_ID'],
        #     'name': user_data['BLOG_NAME'],
        # }
        # if 'USER_PICTURE' in user_data:
        #     self.user['picture_url'] = deezer.utils.USER_PICTURES_URL % user_data['USER_PICTURE']
        self.logged_in = True
        return True


    def login_with_cookie(self, username):
        cookies = self.load_cookies(username)
        self.session.cookies = cookies
        return self._post_login()


    def login_with_arl(self, arl):
        arl_cookie = requests.cookies.create_cookie(domain='.deezer.com', name='arl', path='/', value=arl)
        self.session.cookies.set_cookie(arl_cookie)
        return self._post_login()

    def login(self, mail, password, reCaptchaToken):
        login_token = self.get_api_token()
        json = {
            'type': 'login',
            'mail': mail,
            'password': password,
            'checkFormLogin': login_token,
            'reCaptchaToken': reCaptchaToken
        }
        headers = {
            **self.http_headers,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        result = self.session.post(
            'https://www.deezer.com/ajax/action.php?',
            data=json,
            headers=headers,
        )
        if result.text != 'success':
            #raise 'wrong email or password'
            return result
        return self._post_login()


    def get_track_data(self, track_id):
        if track_id < 0:
            return self.call_private_api(
                'song.getData',
                args='{"SNG_ID": %i}' % track_id
            )
        else:
            raw_data = self.call_private_api(
                'deezer.pageTrack',
                args='{"SNG_ID": %i}' % track_id
            )
            if 'error' in raw_data:
                if 'DATA_ERROR' in raw_data['error']:
                    return None
                if 'VALID_TOKEN_REQUIRED' in raw_data['error']:
                    raise ValidTokenRequired()
            return raw_data

    def get_track_data_mobile(self, track_id):
        mobile_api_key = '4VCYIJUCDLOUELGD1V8WBVYBNVDYOXEWSLLZDONGBBDFVXTZJRXPR29JRLQFO6ZE'
        args = {
            'api_version': '1.0',
            'api_token': 'null',
            # 'input': '3',
            'method': 'deezer.ping'
        }

        session = requests.Session()
        r = session.get(deezer.utils.PRIVATE_API_URL % urlencode(args))
        sid = r.json()['results']['SESSION']
        args['api_key'] = mobile_api_key
        args['method'] = 'song_getData'
        args['output'] = '3'
        args['input'] = '3'
        args['sid'] = sid
        data = '{"SNG_ID": %i}' % track_id
        path = '1.0/gateway.php?'
        raw_data = session.post(deezer.utils.PUBLIC_API_URL + path + urlencode(args), data=data, headers=self.http_headers)
        return raw_data.json()


    # @authrequired
    def get_track(self, track_id, mobile=False) -> 'DeezerTrack':
        track_id = int(track_id)
        if mobile:
            raw_data = self.get_track_data_mobile(track_id)
            raw_data = raw_data['results']
        else:
            raw_data = self.get_track_data(track_id)
            if raw_data is None:
                return None
            if 'DATA' in raw_data['results']:
                raw_data = raw_data['results']['DATA']
        return deezer.track.DeezerTrack.grab_or_create(
            track_id,
            raw_data=raw_data
        )

    @authrequired
    def get_tracks_data(self, track_ids) -> List['Deezertrack']:
        raw_data = self.call_private_api('song.getListData', args=json.dumps({'SNG_IDS': track_ids}))
        if raw_data['error'] != None:
            return raw_data['results']['data']
        return None

    def get_lyrics(self, track_id):
        raw_data = self.call_private_api('song.getLyrics', args='{"SNG_ID": %s}' % track_id)
        if 'DATA_ERROR' in raw_data['error']:
            return None
        return deezer.track.DeezerTrackLyrics(raw_data)

    def get_artist_data(self, artist_id):
        return self.call_private_api(
            'deezer.pageArtist',
            args='{"ART_ID": %i, "LANG": "EN"}' % artist_id
        )

    @authrequired
    def get_artist(self, artist_id):
        return deezer.artist.DeezerArtist.grab_or_create(
            artist_id,
            raw_data=self.get_artist_data(artist_id)['results']
        )


    def get_album_data(self, album_id):
        return self.call_private_api(
            'deezer.pageAlbum',
            args='{"ALB_ID": %i, "LANG": "EN"}' % int(album_id)
        )


    def get_album_data_public(self, album_id):
        raw_data = self.call_public_api('album/' + album_id, args={})
        return raw_data


    @authrequired
    def get_album(self, album_id) -> 'DeezerAlbum':
        raw_data = self.get_album_data(album_id)['results']
        if deezer.album.DeezerCompilation.check(raw_data):
            return deezer.album.DeezerCompilation.grab_or_create(album_id, raw_data=raw_data)
        return deezer.album.DeezerAlbum.grab_or_create(album_id, raw_data=raw_data)


    @authrequired
    def search_isrc(self, isrc):
        """
        Searches deezer.com for isrc number
        Args:
          isrc : https://isrcsearch.ifpi.org/#!/search
        Return:
          Track Object
        """
        data = self.session.get(
            deezer.utils.PUBLIC_API_URL + '/track/isrc:' + isrc).json()
        if 'error' in data:
            return None
        return self.get_track(data['id'])


    # @timeit
    @authrequired
    def search_track(self, q, limit=15):
        # join([search_track.title, artist_string, search_track.album.title])
        raw_data = self.call_public_api('/search/track', args={'q': q})
        track_list = []
        for track_data in raw_data['data']:
            track_list.append({
                'id': track_data['id'],
                'title': track_data['title'],
                'artist': track_data['artist']['name'],
                'album': track_data['album']['title'],
                'explicit': bool(track_data.get('explicit_lyrics', None)),
                'type': 'deezer',
                'album_id': track_data['album']['id'],
                'isrc': '', # no data use isrc lookup
                'cover': track_data['album']['cover_big']
            })
            # track_list.append(self.get_track(track_data['id']))
        if len(track_list) < limit:
            return track_list
        return track_list[0:limit]


    @authrequired
    def search_track_adv(self, title, artist, album):
        """
        Advanced Deezer Search with Key Support
        Args:
            `title` track title
            `artist` artist name
            `album` album name
        Returns:
            `deezer.track` List
        """
        q = f'track:"{title}" artist:"{artist}" album:"{album}"'
        raw_data = self.call_public_api('/search', args={'q': q})
        track_list = []
        for track_data in raw_data['data']:
            track_list.append(self.get_track(track_data['id']))
        return track_list

    # @timeit
    @authrequired
    def search_album(self, album, limit=15):
        """
        Search Album string on Deezer
        Args:
            `q` album name
        """
        q = f'album:"{album}"'
        raw_data = self.call_public_api('/search/album', args={'q': album})
        albums = []
        for raw_album in raw_data['data']:
            albums.append({
                'id': raw_album['id'],
                'title': raw_album['title'],
                'artist': raw_album['artist']['name'],
                'song_count': raw_album['nb_tracks'],
                'type': 'deezer'
            })

        if len(albums) < limit:
            return albums
        return albums[0:limit]


    def get_track_data_public(self, track_id):
        raw_data = self.call_public_api('/track/' + track_id, args={})
        return raw_data


    @authrequired
    def get_albums_from_artist(self, artist_id):
        """
        Gets all Albums from artist_id
        Only 25 Albums per Request use `next` for all
        Args:
            `artist_id` str Artist id from deezer
        Return:
            deezer album with full track list
        """
        results = self._get_album_public(artist_id)
        albums = []
        while results:
            for raw_album_data in results['data']:
                albums.append(self.get_album(int(raw_album_data['id'])))
            try:
                if results['next']:
                    index = results['next'].split('=')[1]
                    results = self._get_album_public(artist_id, args={'index': index})
            except KeyError as e:
                results = None
        return albums


    def _get_album_public(self, artist_id, args={}):
        """
        private function only used for `get_albums_from_artist`
        """
        return self.call_public_api('/artist/' + artist_id + '/albums', args=args)


    @authrequired
    def get_playlist(self, playlist_id) -> 'DeezerPlaylist':
        """REALLY SLOW"""
        limit = 100
        index = 0
        args = {
            'limit': limit,
            'index': index
        }
        results = self._get_playlist(playlist_id, args=args)
        playlist = deezer.playlist.DeezerPlaylist(results)
        tracks = []

        while results:
            # get all track ids
            track_ids = list(map(lambda x: str(x['id']), results['tracks']['data']))
            raw_tracks = self.get_tracks_data(track_ids)
            for raw_track in raw_tracks:
                _track = deezer.track.DeezerTrack.grab_or_create(raw_track['SNG_ID'], raw_data=raw_track)
                _track.is_playlist = True  # set playlist flag
                _track.playlist_name = playlist.name
                _track.playlist_index = str(len(tracks) + 1)
                _track.playlist_length = str(playlist.song_count)
                tracks.append(_track)
            if playlist.song_count <= index + limit:
                break
            else:
                index += limit
                args['index'] = index
                results = self._get_playlist(playlist_id, args)

        # append songs to playlist object
        playlist.songs = tracks
        return playlist

    def _get_playlist(self, playlist_id, args={}):
        """helper for `get_playlist`"""
        return self.call_public_api(
            path='playlist/' + playlist_id,
            args=args)

    def get_playlist_data(self, playlist_id):
        """get data from playlist id for api, fast"""
        return self.call_public_api(path='playlist/' + playlist_id)

    @authrequired
    def get_user_playlists(self):
        """get playlists from current logged in user, they have to be public"""
        # TODO return object with tracklist
        # maybe just use `get_user_playlist_data`
        raw_data = self.call_public_api('user/' + str(self.user['id']) + '/playlists', args={})
        return raw_data

    @authrequired
    def get_user_playlists_data(self):
        """gets user playlists, only data mostly for api
        does not get tracks for playlist for performance use `get_playlist` for that"""
        raw_data = self.call_public_api('user/' + str(self.user['id']) + '/playlists', args={})
        playlists = []
        for raw_playlist in raw_data['data']:
            playlists.append({
                'id': raw_playlist['id'],
                'title': raw_playlist['title'],
                'description': raw_playlist.get('description', ''),
                'image': raw_playlist['picture_xl'],
                'length': raw_playlist['nb_tracks'],
                'duration': raw_playlist['duration'],
                'type': 'deezer'

            })
        return playlists

    def get_show(self, show_id):
        raw_data = self.call_private_api('show.getData', args='{"SHOW_ID": %s}' % show_id)
        # if error NB -1
        raw_episodes = self.call_private_api('deezer.pageShow', args='{"SHOW_ID": %s, "NB": "1000", "START": "0"}' % show_id)
        show = deezer.show.DeezerShow.grab_or_create(raw_data['results']['SHOW_ID'], raw_data=raw_data['results'])
        episodes = []
        for raw_episode in raw_episodes['results']['EPISODES']['data']:
            episodes.append(self.get_episode(raw_episode['EPISODE_ID']))
        show.episodes = episodes
        return show

    def get_episode(self, epsiode_id):
        raw_data = self.call_private_api('episode.getData', args='{"EPISODE_ID": %s}' % epsiode_id)
        return deezer.episode.DeezerEpisode.grab_or_create(
            raw_data['results']['EPISODE_ID'], raw_data=raw_data['results'])

    def save_cookies(self):
        with open(TOKEN_PATH, 'wb') as f:
            f.truncate()
            pickle.dump(self.session.cookies._cookies, f)
            print('Cookies saved!')


    def load_cookies(self, filename):
        # old method remove 15-10-2019
        token_path = os.path.join('tokens', filename)
        if os.path.exists(token_path):
            os.rename(token_path, TOKEN_PATH)
        with open(TOKEN_PATH, 'rb') as f:
            cookies = pickle.load(f)
            if cookies:
                jar = requests.cookies.RequestsCookieJar()
                jar._cookies = cookies
                return jar
            else:
                return False
