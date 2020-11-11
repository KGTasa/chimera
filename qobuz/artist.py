from generic.object import Object
from typing import List

class QobuzArtist(Object):
    def set_raw_data(self, raw_data):
        self.set_values(
            artist_id=raw_data['id'],
            name=raw_data['name'],
            albums=raw_data['albums_count']
        )

    def set_values(
        self,
        artist_id=None,
        name=None,
        albums=None,
        is_full=False,
        raw_data=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.artist_id = artist_id
        self.name = name.strip()
        self.albums: List = albums
        self.is_full = is_full

class QobuzPerformer:
    def __init__(self, name, job):
        self.name = name
        self.job = job

    @staticmethod
    def from_raw_data(raw_data):
        # ignore job = MainArtist
        artists = raw_data.split('-')
        performers = []
        for raw_artist in artists:
            art = raw_artist.split(',')
            job = ', '.join([x.strip() for x in art[1:]])
            if 'MainArtist' not in job:
                if 'Author' in job:
                    performers.append(QobuzPerformer(art[0].strip(), job))
        return performers
