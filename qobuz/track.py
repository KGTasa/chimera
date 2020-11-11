from datetime import datetime


import qobuz.album
import qobuz.artist
import qobuz.track_quality
from db import cc
from generic.object import Object
from generic.track import Track
from generic.track_path import GenericTrackPath
from generic.utils import DownloadResult
from config import log

from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from qobuz.artist import QobuzArtist
    from qobuz.album import QobuzAlbum
    from qobuz.qobuz import Qobuz

class QobuzTrack(Track):
    def set_raw_data(self, song_data, is_playlist_track=False, compilation=None):
        # tracks from playlist have date as unix date format
        # needs testing if date is correct
        if is_playlist_track:
            date = [
                get_time(song_data['album'].get('released_at', '')),
                get_time(song_data['album'].get('purchasable_at', '')),
                get_time(song_data['album'].get('streamable_at', ''))
            ]
        else:
            date = [
                song_data['album'].get('release_date_original', ''),
                song_data['album'].get('release_date_stream', ''),
                song_data['album'].get('release_date_download', '')
            ]
        if cc.qobuz_cover_size != 'max':
            cover = song_data['album']['image'][cc.qobuz_cover_size]
        else:
            cover = song_data['album']['image']['large'].replace('_600', '_max')

        # compilation
        is_compilation = False
        if compilation is None:
            album = qobuz.album.QobuzAlbum.grab_or_create(
                song_data['album']['id'],
                album_id=song_data['album']['id'],
                title=song_data['album']['title'],
                is_full=False if is_playlist_track else True,
                date=date,
                cover=cover,
                label=song_data['album']['label']['name'],
                artists=song_data['album']['artist'],
                genre=song_data['album']['genre']['name'],
                disk_total=song_data['album']['media_count'],
                track_total=song_data['album']['tracks_count'],
                upc=song_data['album']['upc'],
                _type=song_data['album'].get('product_type', '') # maybe wrong, not in playlist
            )

            artists = [qobuz.artist.QobuzArtist.grab_or_create(
                song_data['album']['artist']['id'],
                raw_data=song_data['album']['artist']
            )]
        else:
            album = compilation
            # use performer for Various Artists
            artists = [qobuz.artist.QobuzArtist.grab_or_create(
                song_data['performer']['id'],
                artist_id =song_data['performer']['id'],
                name=song_data['performer']['name']
            )]
            is_compilation = True

        self.set_values(
            title=song_data['title'],
            song_id=song_data['id'],
            artists=artists,
            performers=song_data.get('performers', None),
            streamable=song_data['streamable'],
            hires=song_data['hires'],
            hires_streamable=song_data['hires_streamable'],
            album=album,
            track_number=song_data['track_number'],
            duration=song_data['duration'],
            version=song_data.get('version', ''),
            articles=song_data.get('articles'), # not avail on playlist_tracks
            isrc=song_data['isrc'],
            disk_number=song_data['media_number'],
            qualities=qobuz.track_quality.QobuzTrackQuality.from_raw_data(song_data), # dictionary pretty and usable
            explicit=song_data['parental_warning'], # not sure
            url=song_data['album'].get('url', None), # playlist
            _copyright=song_data['album'].get('copyright', None), # playlist
            is_full=False if is_playlist_track else True,
            composer=song_data['composer']['name'] if 'composer' in song_data else None,
            is_compilation=is_compilation
        )


    def set_values(
        self,
        title=None,
        song_id=None,
        artists=None,
        performers=None,
        album=None,
        qualities=None,
        raw_data=None,
        isrc=None,
        streamable=None,
        hires=None,
        hires_streamable=None,
        track_number=None,
        duration=None,
        version=None,
        articles=None,
        is_playlist_track=False,
        disk_number=None,
        explicit=None,
        url=None,
        _copyright=None,
        is_full=None,
        compilation=None,
        composer=None,
        is_compilation=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data, is_playlist_track=is_playlist_track, compilation=compilation)
            return
        self.title = title
        self.song_id = song_id
        self.artists: List['QobuzArtist'] = artists
        self.album: 'QobuzAlbum' = album
        self.qualities = qualities['qualities']
        self.quality_pretty = qualities['pretty']
        self.is_full = is_full
        self.isrc = isrc
        self.streamable = streamable
        self.hires = hires
        self.hires_streamable = hires_streamable
        self.track_number = str(track_number)
        self.duration = duration
        self.version = version
        self.articles = articles
        self.explicit = explicit
        self.disk_number = disk_number
        self.url = url
        self.copyright = _copyright
        self.composer = composer
        self.is_compilation = is_compilation
        # set artist value = main artist
        self.artist = self.artists[0].name

        # self.artists list of QobuzArtists
        # this is just one object because the rest are
        # in key `performers` => so custom Object for these
        if performers != None:
            self.artists.extend(qobuz.artist.QobuzPerformer.from_raw_data(performers))

        self.service = 'qobuz'

        self.path = GenericTrackPath(self)

    def get_full_data(self, qobuz_session: 'Qobuz'):
        if not self.is_full:
            # we need some album data in the track so album data request
            # is here and not in the album class
            album_data = qobuz_session.get_album_data(self.album.album_id)
            if 'code' in album_data:
                if album_data['code'] == 404:
                    log.info(f'No album_data for track {self}')
                    self.album.is_full = False
                    self.is_full = False
                    return

            self.album.type = album_data['product_type']
            self.album.is_full = True

            #track
            self.copyright = album_data['copyright']
            self.url = album_data['url']
            self.is_full = True


    def get_stream(self, qobuz_session: 'Qobuz', quality):
        quality_to_number = {
            'MP3_320': '5',
            '16-bit 44.1kHz': '6',
            '24-bit 44.1kHz': '7',
            '24-bit 96kHz': '27',
            '24-bit 192kHz': '27'
        }
        return qobuz_session.get_stream(self.song_id, quality_to_number[quality])


    def stream(self, track_stream, output_stream, task=None, dlthread=None):
        """
        download track from qobuz
        Args:
            `task` callback object for DownloadThread for status updates
        """
        # headers
        album_url = qobuz.utils.ALBUM_URL.format(self.album.album_id)
        headers = {
            'range': 'bytes=0-',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
            'referer': album_url
        }
        super().stream(track_stream=track_stream, output_stream=output_stream, task=task, headers=headers, dlthread=dlthread)

    def download(self, qobuz_session, folder=None, to_file=None, quality=None, task=None,
                 lower_quality=False, truncate_filename=False, dlthread=None) -> DownloadResult:
        return super().download(qobuz_session, folder=folder, to_file=to_file, quality=quality, task=task,
                                lower_quality=lower_quality, truncate_filename=truncate_filename, dlthread=dlthread)


    def update_tags(self, qobuz_session):
        self.get_full_data(qobuz_session)
        self.year = self.album.date.split('-')[0]
        super().update_tags()


class QobuzTrackStream(Object):
    #38773596 restricted got track via playlist 1423255 restrictedbyrightsholder
    def set_raw_data(self, raw_data):
        self.set_values(
            bit_depth=raw_data['bit_depth'],
            format_id=raw_data['format_id'],
            mime_type=raw_data['mime_type'],
            sampling_rate=raw_data['sampling_rate'],
            url=raw_data['url']
        )

    def set_values(
        self,
        bit_depth=None,
        format_id=None,
        mime_type=None,
        sampling_rate=None,
        url=None,
        raw_data=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.bit_depth = bit_depth
        self.format_id = format_id
        self.mime_type = mime_type
        self.sampling_rate = sampling_rate
        self.url = url


def get_time(unix):
    if unix is not None and unix > 0:
        return datetime.fromtimestamp(int(unix)).strftime('%Y-%m-%d')
    else:
        return ''
