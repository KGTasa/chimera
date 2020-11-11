from generic.object import Object

class NapsterArtist(Object):
    def set_raw_data(self, raw_data):
        self.set_values()

    def set_values(self, artist_id=None, name=None, raw_data=None):
        if raw_data != None:
            return self.set_raw_data(raw_data)
        self.artist_id = artist_id
        self.name = name 