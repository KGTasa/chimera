import deezer.utils
from generic.object import Object
import deezer.album

instances = {}


class DeezerArtist(Object):
    def set_raw_data(self, raw_data):
        artist_data = raw_data["DATA"]
        albums_data = raw_data["ALBUMS"]["data"]
        return self.set_values(
            artist_id=artist_data["ART_ID"],
            name=artist_data["ART_NAME"],
            picture_url=deezer.utils.ARTIST_PICTURES_URL % artist_data["ART_PICTURE"],
            albums=list(map(
                lambda a: deezer.album.DeezerAlbum.grab_or_create(
                    a["ALB_ID"], raw_data=a
                ),
                albums_data
            )),
            is_full=True
        )

    def set_values(
        self,
        artist_id=None,
        name=None,
        picture_url=None,
        albums=None,
        is_full=False,  # if the album is fully loaded
        raw_data=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.artist_id = artist_id
        self.name = name
        self.picture_url = picture_url
        self.albums = albums
        self.is_full = is_full

    def get_full_data(self, deezer_instance):
        if not self.is_full:
            raw_data = deezer_instance.get_artist_data(self.album_id)
            self.set_raw_data(raw_data)
        if self.albums != None:
            for album in self.albums:
                if not album.is_full:
                    album.get_full_data(deezer_instance)
