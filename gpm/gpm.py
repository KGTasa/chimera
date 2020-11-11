import gmusicapi

import gpm.track
import gpm.playlist
from db import cc
import os
from generic.utils import authrequired

TOKEN_PATH = os.path.join('tokens', 'gpm.token')

class GPM:
    token_path = os.path.join('tokens', 'token.gpm')

    def __init__(self, device_id):
        self.user = None
        self.logged_in = False
        self.api = gmusicapi.Mobileclient()
        self.device_id = device_id

    def __repr__(self):
        return 'GPM'

    def login(self):
         # remove me
        if os.path.exists(self.token_path):
            os.rename(self.token_path, TOKEN_PATH)

        if os.path.isfile(TOKEN_PATH) == False:
            self.api.perform_oauth(storage_filepath=TOKEN_PATH, open_browser=True)
        if self.device_id == 'CHANGEME':
            self.device_id = self.get_device_id()
            cc.gpm_device_id = self.device_id
            cc.save()
        if self.device_id == 'MAC_ADDRESS':
            self.device_id = self.api.FROM_MAC_ADDRESS

        status = self.api.oauth_login(self.device_id, oauth_credentials=TOKEN_PATH)
        self.logged_in = True
        return status

    def get_device_id(self):
        device_id = self.api.FROM_MAC_ADDRESS
        self.api.oauth_login(device_id, oauth_credentials=TOKEN_PATH)
        devices = self.api.get_registered_devices()
        self.api.logout()
        valid_devices = ['ANDROID', 'IOS']
        for device in devices:
            if device['type'] in valid_devices:
                if device['type'] == 'ANDROID':
                    return device['id'][2:]
                else:
                    return device['id']
        # no mobile device found fallback to mac_address
        # can't return api.FROM_MAC_ADDRESS because can't save that
        # in the sqlite db
        return 'MAC_ADDRESS'
        # raise ValueError('NO MOBILE DEVICE FOUND!')

    @authrequired
    def get_track(self, track_id):
        raw_data = self.api.get_track_info(track_id)
        return gpm.track.GPMTrack.grab_or_create(raw_data['storeId'], raw_data=raw_data)

    def get_stream(self, track_id, quality):
        return self.api.get_stream_url(track_id, quality=quality)

    @authrequired
    def get_album(self, album_id):
        raw_data = self.api.get_album_info(album_id)
        return gpm.album.GPMAlbum.grab_or_create(raw_data['albumId'], raw_data=raw_data)

    @authrequired
    def get_playlist(self, playlist_id, playlist_name):
        raw_data = self.api.get_shared_playlist_contents(playlist_id.replace('%3D', '='))
        return gpm.playlist.GPMPlaylist(raw_data, playlist_name)

    @authrequired
    def search_track(self, q, limit=15):
        raw_data = self.api.search(q, max_results=limit)
        track_list = []
        for data in raw_data['song_hits']:
            track_list.append({
                'id': data['track']['storeId'],
                'title': data['track']['title'],
                'artist': data['track']['artist'],
                'album': data['track']['album'],
                'type': 'gpm',
                'album_id': data['track']['albumId'],
                'isrc': '' # no data
            })
        if len(track_list) < limit:
            return track_list
        return track_list[0:limit]

    @authrequired
    def search_album(self, q, limit=15):
        raw_data = self.api.search(q, max_results=limit)
        album_list = []
        for raw_album in raw_data['album_hits']:
            album_list.append({
                'id': raw_album['album']['albumId'],
                'title': raw_album['album']['name'],
                'artist': raw_album['album']['albumArtist'],
                'song_count': 'no data',
                'type': 'gpm'
            })
        if len(album_list) < limit:
            return album_list
        return album_list[0:limit]

    @authrequired
    def get_user_playlists_data(self):
        raw_data = self.api.get_all_playlists()
        playlists = []
        for raw_playlist in raw_data:
            playlists.append({
                'id': raw_playlist['id'],
                'title': raw_playlist['name'],
                'description': raw_playlist.get('description', ''),
                'image': '',
                'length': 'no data',
                'duration': 'no data',
                'type': 'gpm'

            })
        return playlists
