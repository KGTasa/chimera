import gpm.album
import gpm.artist
from generic.utils import DownloadResult
from generic.track import Track
from generic.track_path import GenericTrackPath


class GPMTrack(Track):
    def set_raw_data(self, song_data):
        if song_data['artist'] == 'Various Artists':
            artists = [gpm.artist.GPMArtist.grab_or_create(
                '000000', artist_id='000000', name=song_data['artist']
            )]
        else:
            artists = [gpm.artist.GPMArtist.grab_or_create(
                song_data['artistId'][0], artist_id=song_data['artistId'][0], name=song_data['artist']
            )]

        self.set_values(
            song_id=song_data['storeId'],
            title=song_data['title'],
            artists=artists,
            artist=song_data['artist'],
            album=gpm.album.GPMAlbum.grab_or_create(
                song_data['albumId'],
                album_id=song_data['albumId'],
                title=song_data['album'],
                artists=artists,
                date=song_data.get('year', None),
                cover=song_data['albumArtRef'][0]['url'],
                genre=song_data.get('genre', '')
            ),
            qualities=['low', 'med', 'hi'],
            duration=int(song_data['durationMillis']) // 1000,
            disk_number=song_data['discNumber'],
            track_number=song_data['trackNumber']


        )

    def set_values(
        self,
        title=None,
        song_id=None,
        artists=None,
        artist=None,
        album=None,
        qualities=None,
        raw_data=None,
        explicit=None,
        duration=None,
        disk_number=None,
        track_number=None,
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.title = title
        self.song_id = song_id
        self.artists = artists
        self.album = album
        self.qualities = qualities
        self.artist = artist
        self.explicit = explicit
        self.duration = duration
        self.disk_number = disk_number
        self.track_number = str(track_number)
        self.service = 'gpm'
        self.path = GenericTrackPath(self)


    def update_tags(self, gpm_session=None):
        self.year = self.album.date


    def get_stream(self, gpm, quality):
        return GPMTrackStream(gpm.get_stream(self.song_id, quality))

    def stream(self, track_stream, output_stream, task=None, dlthread=None):
        super().stream(track_stream=track_stream, output_stream=output_stream, task=task, dlthread=dlthread)

    def download(self, gpm_session, quality=None, folder=None, to_file=None, task=None,
                 lower_quality=False, dlthread=None) -> DownloadResult:
        """no lower_quality"""
        return super().download(gpm_session, folder=folder, to_file=to_file, quality=quality,
                                task=task, lower_quality=lower_quality, dlthread=dlthread)

class GPMTrackStream:
    def __init__(self, url):
        self.url = url