from typing import List
from tidal.track import TidalTrack

class TidalPlaylist():
    def __init__(self, raw_data):
        self.name = raw_data['title']
        self.playlist_id = raw_data['uuid']
        self.song_count = raw_data['numberOfTracks']
        self.description = raw_data.get('description', '')
        self.images = raw_data['image'] # image or squareImage
        self.songs: List[TidalTrack] = []
