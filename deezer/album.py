import deezer.artist
import deezer.track
import deezer.utils
from generic.album import Album
from config import log
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from deezer.track import DeezerTrack

class DeezerAlbum(Album):
    def set_raw_data(self, raw_data):
        is_page = "ALB_ID" not in raw_data
        album_data = raw_data["DATA"] if is_page else raw_data
        songs_data = raw_data["SONGS"]["data"] if is_page else album_data["SONGS"]["data"]
        return self.set_values(
            album_id=album_data["ALB_ID"],
            title=album_data["ALB_TITLE"],
            date=album_data["PHYSICAL_RELEASE_DATE"],
            picture_url=deezer.utils.ALBUM_PICTURES_URL % album_data["ALB_PICTURE"],
            picture_thumbnail_url=deezer.utils.ALBUM_PICTURES_URL_THUMBNAIL % album_data["ALB_PICTURE"],
            artists=list(map(lambda a: deezer.artist.DeezerArtist.grab_or_create(
                a["ART_ID"],
                artist_id=a["ART_ID"],
                name=a["ART_NAME"],
                picture_url=deezer.utils.ARTIST_PICTURES_URL % a["ART_PICTURE"]
            ),
                album_data["ARTISTS"]
            )),
            songs=list(map(lambda s: deezer.track.DeezerTrack.grab_or_create(s["SNG_ID"], raw_data=s), songs_data)),
            main_call=True
        )

    def set_values(
        self,
        album_id=None,
        title=None,
        date=None,
        picture_url=None,
        picture_thumbnail_url=None,
        artists=None,
        songs = None,
        raw_data=None,
        main_call=False
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.album_id = album_id
        self.title = title
        self.date = date
        self.picture_url = picture_url
        self.picture_thumbnail_url = picture_thumbnail_url
        self.artists = artists
        self.songs: List['DeezerTrack'] = songs
        self.is_full = False



        # if self.songs != None and len(self.songs) == 1:
        #     self.is_single = True
        # else:
        #     self.is_single = False

        # STRING SUBSTITUTION HERE
        # there are albums, where the album title ends with an ' ', windows does not like folders with an empty spaces at the end
        if self.title[-1] == ' ':
            self.title = self.title[:-1]

        # only execute post_init if album is created from
        # main service not from track grab
        if main_call:
            self.post_init()

    def get_full_data(self, deezer_instance):
        if not self.is_full:
            album_data = deezer_instance.get_album_data_public(self.album_id)
            if album_data:
                if 'genres' in album_data:
                    genre_string = ', '.join(map(lambda a: a['name'], album_data['genres']['data']))
                    self.genre = genre_string
                else:
                    self.genre = None

                self.upc = album_data.get('upc', None)
                self.track_total = album_data['nb_tracks']
                # self.disk_total = get data from tracks?
                self.label = album_data.get('label', None)
                self.type = album_data['record_type']
                self.is_full = True


class DeezerCompilation(DeezerAlbum):
    """See TidalCompilation"""

    def set_raw_data(self, raw_data):
        is_page = "ALB_ID" not in raw_data
        album_data = raw_data["DATA"] if is_page else raw_data
        songs_data = raw_data["SONGS"]["data"] if is_page else album_data["SONGS"]["data"]
        return self.set_values(
            album_id=album_data["ALB_ID"],
            title=album_data["ALB_TITLE"],
            date=album_data["PHYSICAL_RELEASE_DATE"],
            picture_url=deezer.utils.ALBUM_PICTURES_URL % album_data["ALB_PICTURE"],
            picture_thumbnail_url=deezer.utils.ALBUM_PICTURES_URL_THUMBNAIL % album_data["ALB_PICTURE"],
            artists=list(map(lambda a: deezer.artist.DeezerArtist.grab_or_create(
                a["ART_ID"],
                artist_id=a["ART_ID"],
                name=a["ART_NAME"],
                picture_url=deezer.utils.ARTIST_PICTURES_URL % a["ART_PICTURE"]
            ),
                album_data["ARTISTS"]
            )),
            songs=songs_data,
            main_call=True
        )

    def set_values(
        self,
        album_id=None,
        title=None,
        date=None,
        picture_url=None,
        picture_thumbnail_url=None,
        artists=None,
        songs = None,
        raw_data=None,
        main_call=False
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.album_id = album_id
        self.title = title
        self.date = date
        self.picture_url = picture_url
        self.picture_thumbnail_url = picture_thumbnail_url
        self.artists = artists
        self.songs: List['DeezerTrack'] = songs
        self.is_full = False

        self.songs = list(map(lambda s: deezer.track.DeezerTrack.grab_or_create(s["SNG_ID"], raw_data=s, compilation=self), songs))
        log.info('Deezer Album {} will be downloaded as a compilation, maybe less metadata!'.format(self.album_id))

        if self.title[-1] == ' ':
            self.title = self.title[:-1]

        if main_call:
            self.post_init()

    @staticmethod
    def check(raw_data):
        """checks if an album is a compilation"""
        if raw_data['DATA']['ART_NAME'] == 'Various Artists':
            return True
        return False