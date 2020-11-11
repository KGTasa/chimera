from typing import List
from napster.track import NapsterTrack

class NapsterPlaylist():
    def __init__(self, raw_data):
        self.name = raw_data['name']
        self.playlist_id = raw_data['id']
        self.song_count = raw_data['trackCount']
        self.is_public = False if raw_data['privacy'] == 'private' else True
        self.description = raw_data['description']
        self.owner = raw_data['links']['members']
        self.images = raw_data['images'][0]
        self.songs: List[NapsterTrack] = []