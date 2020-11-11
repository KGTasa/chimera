
import napster.album
import napster.artist
from generic.object import Object
from generic.track import Track
from generic.utils import DownloadResult
from generic.track_path import GenericTrackPath
from napster.track_quality import NapsterTrackQuality

from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from napster.artist import NapsterArtist
    from napster.album import NapsterAlbum
    from napster.napster import Napster

class NapsterTrack(Track):
    def set_raw_data(self, song_data, napster_session=None):
        self.set_values(
            title=song_data['name'],
            song_id=song_data['id'],
            artists=[napster.artist.NapsterArtist.grab_or_create(
                song_data['artistId'], name=song_data['artistName'], artist_id=song_data['artistId']
            )],
            album=napster_session.get_album(song_data['albumId'], full=False) if napster_session != None else None,
            artist=song_data['artistName'],
            qualities=NapsterTrackQuality.from_raw_data(song_data),
            streamable=song_data['isStreamable'],
            hi_res=song_data['isAvailableInHiRes'],
            explicit=song_data['isExplicit'],
            isrc=song_data['isrc'],
            duration=song_data['playbackSeconds'],
            track_number=song_data['index'],
            disk_number=song_data['disc'],
            url='napster.com' + song_data['shortcut'],
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
        streamable=None,
        hi_res=None,
        explicit=None,
        isrc=None,
        duration=None,
        disk_number=None,
        track_number=None,
        napster_session=None,
        url=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data, napster_session)
            return
        self.title = title
        self.song_id = song_id.split('.')[1]
        self.artists: List['NapsterArtist'] = artists
        self.album: 'NapsterAlbum' = album
        self.qualities = qualities
        self.streamable = streamable
        self.artist = artist
        self.hi_res = hi_res
        self.explicit = explicit
        self.isrc = isrc
        self.duration = duration
        self.disk_number = disk_number
        self.track_number = str(track_number)
        self.url = url

        self.service = 'napster'

        self.path = GenericTrackPath(self)

    def update_tags(self, napster_session):
        # we can get all tags in grab_or_crate() function
        self.year = self.album.date.split('-')[0]
        self.bpm = ''


    def get_stream(self, napster_session, quality):
        track_id = 'tra.{}'.format(self.song_id)
        quality_formats = {
            'AAC_64': {'bitrate': 64, 'format': 'AAC PLUS', 'track': track_id},
            'AAC_192': {'bitrate': 192, 'format': 'AAC', 'track': track_id},
            'AAC_320': {'bitrate': 320, 'format': 'AAC', 'track': track_id}
        }
        return napster_session.get_stream(track_id, quality_formats[quality])

    def guess_quality(self):
        # Qualities : ['AAC_64', 'MP3_128'] and it crashes if it tries to download MP3_128
        # because mp3 isn't implemented
        if 'MP3_128' in self.qualities:
            self.qualities.remove('MP3_128')
        return self.qualities[len(self.qualities) - 1]

    def stream(self, track_stream, output_stream, task=None, dlthread=None):
        super().stream(track_stream=track_stream, output_stream=output_stream, task=task, dlthread=dlthread)

    def download(self, napster_session, folder=None, to_file=None, quality=None, task=None,
                 lower_quality=True, dlthread=None) -> DownloadResult:
        return super().download(napster_session, folder=folder, to_file=to_file, quality=quality,
                                task=task, lower_quality=lower_quality, dlthread=dlthread)

class NapsterTrackStream(Object):
    def set_raw_data(self, raw_data):
        self.set_values(
            bitrate=raw_data['format']['bitrate'],
            name=raw_data['format']['name'],
            sample_bits=raw_data['format']['sampleBits'],
            sample_rate=raw_data['format']['sampleRate'],
            url=raw_data['url']
        )

    def set_values(
        self,
        bitrate=None,
        name=None,
        sample_bits=None,
        sample_rate=None,
        url=None,
        raw_data=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.bitrate = bitrate
        self.name = name
        self.sample_bits = sample_bits
        self.sample_rate = sample_rate
        self.url = url
