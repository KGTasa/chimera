from generic.album import Album
import napster.track

from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from napster.track import NapsterTrack

class NapsterAlbum(Album):
    def set_raw_data(self, raw_data):
        songs = None
        if 'tracks' in raw_data:
            songs = [napster.track.NapsterTrack.grab_or_create(
                song['id'], raw_data=song) for song in raw_data['tracks']]
        return self.set_values(
            album_id=raw_data['album']['id'],
            title=raw_data['album']['name'],
            artists=raw_data['album']['contributingArtists']['primaryArtist'],
            songs=songs,
            date=raw_data['album']['originallyReleased'], # fix pls
            cover=max(raw_data['images'], key=lambda f: f['height'])['url'] if len(raw_data['images']) != 0 else None,
            label=raw_data['album']['label'],
            upc=raw_data['album']['upc'],
            disk_total=raw_data['album']['discCount'],
            track_total=raw_data['album']['trackCount'],
            _type='Single' if raw_data['album']['isSingle'] else 'Album',
            is_full=True
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
        genre=None, # fix
        upc=None,
        disk_total=None,
        track_total=None,
        _type=None,
        is_full=False
    ):
        if raw_data != None:
            return self.set_raw_data(raw_data)
        self.album_id = album_id
        self.title = title
        self.artists = artists
        self.songs: List['NapsterTrack'] = songs
        self.is_full = is_full
        self.picture_url = cover
        self.label = label
        self.type = _type
        self.date = date.split('T')[0]
        self.upc = upc
        self.disk_total = disk_total
        self.track_total = track_total
        if self.songs:
            for track in self.songs:
                track.album = self