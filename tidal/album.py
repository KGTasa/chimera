import tidal.artist
import tidal.track
from config import log
from generic.album import Album
import tidal.utils


class TidalAlbum(Album):
    def set_raw_data(self, raw_data):
        return self.set_values(
            album_id = raw_data['id'],
            title = raw_data['title'],
            artists = list(map(lambda a: tidal.artist.TidalArtist.grab_or_create(
                a['id'], raw_data=a), raw_data['artists'])),
            songs = list(map(lambda s: tidal.track.TidalTrack.grab_or_create(s['id'], raw_data=s), raw_data['songs']['items'])),
            is_full = False,
            date=raw_data['releaseDate'],
            upc=raw_data['upc'],
            disk_total=raw_data['numberOfVolumes'],
            track_total=raw_data['numberOfTracks'],
            _type=raw_data['type'].capitalize(),
            cover=raw_data['cover'],
            main_call=True
        )

    @property
    def picture_url(self):
        # uuid replace all - with /
        return tidal.utils.IMG_URL.format(self.cover.replace('-', '/'))

    def set_values(
        self,
        album_id=None,
        title=None,
        artists=None,
        songs=None,
        is_full=False,
        raw_data=None,
        date=None,
        cover=None,
        upc=None,
        disk_total=None,
        track_total=None,
        _type=None,
        main_call=False
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.album_id = album_id
        self.title = title
        self.artists = artists
        self.songs = songs
        self.is_full = is_full
        self.date = date
        self.cover = cover
        self.upc = upc
        self.disk_total = disk_total
        self.track_total = track_total
        self.type = _type

        # only execute post_init if album is created from
        # main service not from track grab
        if main_call:
            self.post_init()

    def get_full_data(self, tidal_session):
        if not self.is_full:
            album_data = tidal_session.get_album_data(self.album_id)
            if 'status' in album_data and album_data['status'] == 404:
                # failed to get data
                log.info(f'Failed to get album data for {self.album_id} TIDAL')
                return False

            # temporary #52
            try:
                self.date = album_data['releaseDate']
                self.disk_total = album_data['numberOfVolumes']
                self.track_total = album_data['numberOfTracks']
                self.type = album_data['type'].capitalize()
                self.upc = album_data['upc']
                self.is_full = True
            except KeyError as e:
                log.info(album_data)
                log.info(e)
                return False



class TidalCompilation(TidalAlbum):
    """Theoretically this could be merged with TidalAlbum
    But I want to separate Compilation and Albums
    If a compilation Track is in a playlist this doesn't work.
    """

    def set_raw_data(self, raw_data):
        return self.set_values(
            album_id = raw_data['id'],
            title = raw_data['title'],
            artists = list(map(lambda a: tidal.artist.TidalArtist.grab_or_create(
                a['id'], raw_data=a), raw_data['artists'])),
            songs = raw_data['songs']['items'],
            is_full = True,
            date=raw_data['releaseDate'],
            upc=raw_data['upc'],
            disk_total=raw_data['numberOfVolumes'],
            track_total=raw_data['numberOfTracks'],
            _type=raw_data['type'].capitalize(),
            cover=raw_data['cover'],
            main_call=True
        )

    def set_values(
        self,
        album_id=None,
        title=None,
        artists=None,
        songs=None,
        is_full=False,
        raw_data=None,
        date=None,
        cover=None,
        upc=None,
        disk_total=None,
        track_total=None,
        _type=None,
        main_call=False
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.album_id = album_id
        self.title = title
        self.artists = artists
        # self.songs = songs
        self.is_full = is_full
        self.date = date
        self.cover = cover
        self.upc = upc
        self.disk_total = disk_total
        self.track_total = track_total
        self.type = _type

        # create songs after compilation to set song.album
        self.songs = list(map(lambda s: tidal.track.TidalTrack.grab_or_create(s['id'], raw_data=s, compilation=self), songs))
        log.info('Tidal Album {} will be downloaded as a compilation, maybe less metadata!'.format(self.album_id))

        if main_call:
            self.post_init()

    @staticmethod
    def check(raw_data):
        """checks if an album is a compilation"""
        if raw_data['artist']['name'] == 'Various Artists':
            return True
        return False