from generic.album import Album
import gpm.track
import gpm.artist

class GPMAlbum(Album):
    def set_raw_data(self, raw_data):
        return self.set_values(
            album_id=raw_data['albumId'],
            title=raw_data['name'],
            artists=[gpm.artist.GPMArtist.grab_or_create(
                raw_data['artistId'][0], artist_id=raw_data['artistId'][0], name=raw_data['artist']
            )],
            songs=list(map(lambda a: gpm.track.GPMTrack.grab_or_create(
                a['storeId'], raw_data=a), raw_data['tracks'])),
            date=raw_data['year'],
            cover=raw_data['albumArtRef']
        )


    def set_values(
        self,
        album_id=None,
        title=None,
        artists=None,
        songs=None,
        raw_data=None,
        date=None,
        cover=None,
        label=None,
        genre=None
    ):
        if raw_data != None:
            return self.set_raw_data(raw_data)
        self.album_id = album_id
        self.title = title
        self.artists = artists
        self.songs = songs
        self.picture_url = cover
        self.label = None
        self.genre = None
        self.upc = None
        self.disk_total = None
        self.track_total = None
        self.date = str(date)
