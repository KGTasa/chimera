from generic.album import Album
import qobuz.track
import qobuz.artist
from db import cc
from config import log

from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from qobuz.track import QobuzTrack

class QobuzAlbum(Album):
    # finish when grab_album()
    def set_raw_data(self, raw_data, qobuz_session):
        if cc.qobuz_cover_size != 'max':
            cover = raw_data['image'][cc.qobuz_cover_size]
        else:
            cover = raw_data['image']['large'].replace('_600', '_max')

        return self.set_values(
            album_id=raw_data['id'],
            title=raw_data['title'],
            artists=[qobuz.artist.QobuzArtist.grab_or_create(
                raw_data['artist']['id'],
                raw_data=raw_data['artist']
            )],
            songs=list(map(lambda s: qobuz_session.get_track(s['id']), raw_data['tracks']['items'])),
            date=[
                raw_data.get('release_date_original', ''),
                raw_data.get('release_date_stream', ''),
                raw_data.get('release_date_download', '')
            ],
            cover=cover,
            label=raw_data['label']['name'],
            genre=raw_data['genre']['name'],
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
        label=None,
        genre=None,
        qobuz_session=None,
        disk_total=None,
        track_total=None,
        upc=None,
        _type=None,
        main_call=False
    ):
        if raw_data != None:
            self.set_raw_data(raw_data, qobuz_session)
            return
        self.album_id = album_id
        self.title = title
        self.artists = artists
        self.songs: List['QobuzTrack'] = songs
        self.is_full = is_full
        # possible matches: release_date_original, release_date_stream, release_date_download
        self.date = [d for d in date if d != ''][0]
        self.picture_url = cover
        self.label = label
        self.genre = genre
        self.disk_total = disk_total
        self.track_total = track_total
        self.upc = upc
        self.type = _type

        # only execute post_init if album is created from
        # main service not from track grab
        if main_call:
            self.post_init()


class QobuzCompilation(QobuzAlbum):
    """see TidalCompilation"""
    # finish when grab_album()
    def set_raw_data(self, raw_data, qobuz_session):
        if cc.qobuz_cover_size != 'max':
            cover = raw_data['image'][cc.qobuz_cover_size]
        else:
            cover = raw_data['image']['large'].replace('_600', '_max')

        return self.set_values(
            album_id=raw_data['id'],
            title=raw_data['title'],
            artists=[qobuz.artist.QobuzArtist.grab_or_create(
                raw_data['artist']['id'],
                raw_data=raw_data['artist']
            )],
            songs=raw_data['tracks']['items'],
            date=[
                raw_data.get('release_date_original', ''),
                raw_data.get('release_date_stream', ''),
                raw_data.get('release_date_download', '')
            ],
            cover=cover,
            label=raw_data['label']['name'],
            genre=raw_data['genre']['name'],
            qobuz_session=qobuz_session, # else it gets eaten
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
        label=None,
        genre=None,
        qobuz_session=None,
        disk_total=None,
        track_total=None,
        upc=None,
        _type=None,
        main_call=False
    ):
        if raw_data != None:
            self.set_raw_data(raw_data, qobuz_session)
            return
        self.album_id = album_id
        self.title = title
        self.artists = artists
        # self.songs: List['QobuzTrack'] = songs
        self.is_full = is_full
        # possible matches: release_date_original, release_date_stream, release_date_download
        self.date = [d for d in date if d != ''][0]
        self.picture_url = cover
        self.label = label
        self.genre = genre
        self.disk_total = disk_total
        self.track_total = track_total
        self.upc = upc
        self.type = _type

        self.songs = list(map(lambda s: qobuz_session.get_track(s['id'], compilation=self), songs))
        log.info('Qobuz Album {} will be downloaded as a compilation, maybe less metadata!'.format(self.album_id))

        # only execute post_init if album is created from
        # main service not from track grab
        if main_call:
            self.post_init()

    @staticmethod
    def check(raw_data):
        """check if an album is a compilation"""
        if raw_data['artist']['name'] == 'Various Artists':
            return True
        return False