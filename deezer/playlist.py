from typing import List
from deezer.track import DeezerTrack

class DeezerPlaylist():
    def __init__(self, raw_data):
        self.name = raw_data['title']
        self.playlist_id = raw_data['id']
        self.song_count = raw_data['nb_tracks']
        self.is_public = raw_data['public']
        self.description = raw_data.get('description', '')
        self.owner = raw_data['creator']['name']
        self.images = raw_data['picture_xl'] # 1000px cover 4x4 albums
        self.songs: List[DeezerTrack] = []
