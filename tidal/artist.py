from generic.object import Object
from tidal.utils import ARTIST_IMG_URL

class TidalArtist(Object):
    def set_raw_data(self, raw_data):
        self.set_values(artist_id = raw_data['id'], name=raw_data['name'], is_full=False) # we don't have the albums yet!

    @property
    def picture_url(self, width=512, height=512):
        return ARTIST_IMG_URL.format(width=width, height=height, id=self.artist_id, id_type='artistid')

    def set_values(self, artist_id=None, name=None, albums=None, raw_data=None, is_full=False):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.artist_id = artist_id
        self.name = name
        self.albums = albums
        self.is_full = is_full
