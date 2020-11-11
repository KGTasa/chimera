from typing import List
from qobuz.track import QobuzTrack

class QobuzPlaylist():
    def __init__(self, raw_data):
        self.name = raw_data['name']
        self.playlist_id = raw_data['id']
        self.song_count = raw_data['tracks_count']
        self.is_public = raw_data['is_public']
        self.description = raw_data.get('description', '')
        self.owner = raw_data['owner']['name']
        self.images = raw_data.get('images150', '') # images150, images300, images (50)
        self.songs: List[QobuzTrack] = []
