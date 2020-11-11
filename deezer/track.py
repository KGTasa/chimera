import binascii
import hashlib
import os
import urllib.request
from typing import TYPE_CHECKING, List
from urllib.request import urlopen

import pyaes

import deezer.album
import deezer.artist
import deezer.track_quality
import deezer.utils
from db import cc
from generic.track import Track
from generic.track_path import GenericTrackPath
from generic.utils import DownloadResult

if TYPE_CHECKING:
    from deezer.artist import DeezerArtist
    from deezer.album import DeezerAlbum
    from deezer.deezer import Deezer


class DeezerTrack(Track):
    def set_raw_data(self, song_data, compilation=None):
        try:
            date_value = song_data['PHYSICAL_RELEASE_DATE']
        except:
            date_value = '2000-01-01'


        if 'FALLBACK' in song_data:
            return self.set_raw_data(song_data=song_data['FALLBACK'])

        # check if mobile
        if 'PUID' in song_data:
            md5_origin = song_data['PUID']
        else:
            md5_origin = song_data['MD5_ORIGIN']

        # composer
        composer = None
        if 'composer' in song_data.get('SNG_CONTRIBUTORS', ''):  # playlist
            composer = '/ '.join(song_data['SNG_CONTRIBUTORS']['composer'])

        # compilation arg is only set if deezer.get_album is called
        is_compilation = False
        if compilation is None:
            album = deezer.album.DeezerAlbum.grab_or_create(
                song_data['ALB_ID'],
                album_id=song_data['ALB_ID'],
                title=song_data['ALB_TITLE'],
                date=date_value,
                picture_url=deezer.utils.ALBUM_PICTURES_URL % song_data['ALB_PICTURE'],
                picture_thumbnail_url=deezer.utils.ALBUM_PICTURES_URL_THUMBNAIL % song_data['ALB_PICTURE']
            )
        else:
            album = compilation
            is_compilation = True

        self.set_values(
            title=song_data['SNG_TITLE'],
            song_id=song_data['SNG_ID'],
            artists=list(map(lambda a: deezer.artist.DeezerArtist.grab_or_create(
                a['ART_ID'],
                artist_id=a['ART_ID'],
                name=a['ART_NAME'],
                picture_url=deezer.utils.ARTIST_PICTURES_URL % a['ART_PICTURE']
            ), song_data['ARTISTS']
            )),
            album=album,
            md5_origin=md5_origin,
            media_version=song_data['MEDIA_VERSION'],
            qualities=deezer.track_quality.DeezerTrackQuality.from_raw_data(song_data),
            disk_number=song_data.get('DISK_NUMBER', '1'), # because of playlists
            track_number=song_data.get('TRACK_NUMBER', '0'), # mobile no track_nr
            isrc=song_data['ISRC'],
            duration=song_data['DURATION'],
            version=song_data.get('VERSION', None),
            explicit=bool(int(song_data.get('EXPLICIT_LYRICS', 0))), # playlist different key EXPLICIT_TRACK_CONTENT
            _copyright=song_data.get('COPYRIGHT', None), # none if grab album
            composer=composer,
            is_compilation=is_compilation
        )


    def set_values(
        self,
        song_id=None,
        title=None,
        artists=None,
        album=None,
        md5_origin=None,
        media_version=None,
        qualities=None,
        disk_number=None,
        track_number=None,
        isrc=None,
        raw_data=None,
        duration=None,
        version=None,
        explicit=None,
        _copyright=None,
        composer=None,
        compilation=None,
        is_compilation=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data, compilation)
            return
        self.song_id = song_id
        self.title = f'{title} {version}'  # maybe config
        self.title = self.title.strip() # remove space if no version
        self.artists: List['DeezerArtist'] = artists
        self.album: 'DeezerAlbum' = album
        self.md5_origin = md5_origin
        self.media_version = media_version
        self.qualities = qualities
        self.disk_number = disk_number
        self.track_number = track_number
        self.isrc = isrc
        self.is_full = False
        self.spotify_id = None
        self.duration = int(duration)
        self.version = version
        self.explicit = explicit
        self.service = 'deezer'
        self.copyright = _copyright
        self.composer = composer
        self.is_compilation = is_compilation

        # set artist value = main artist
        self.artist = self.artists[0].name

        self.path = GenericTrackPath(self)

    def get_full_data(self, deezer_instance: 'Deezer'):
        if not self.is_full:
            track_data = deezer_instance.get_track_data_public(self.song_id)
            if track_data:
                self.bpm = track_data.get('bpm', None)
                self.available_countries = track_data['available_countries']
                self.gain = track_data['gain']
                self.disk_number = track_data['disk_number']
                self.url = track_data['album']['link']

                self.is_full = True

    def update_tags(self, deezer_instance: 'Deezer'):
        """adds bpm info to track"""
        # get all metadata
        self.get_full_data(deezer_instance)
        self.album.get_full_data(deezer_instance)

        # track_data['readable'] boolean true if the track is readable in the player for the current user
        # check if date is 0000-00-00
        if self.album.date == '0000-00-00':
            self.album.date = '2000-01-01'

        self.year = self.album.date.split('-')[0]

        super().update_tags()

    def guess_quality(self, selected_quality):
        """different from the other tracks, because it has two
        audio formats, normal: mp3, flac; and 360 surround mp4
        """
        normal = []
        surround = []
        for q in self.qualities:
            if q in ['MP3_128', 'MP3_320', 'FLAC']:
                normal.append(q)
            else:
                surround.append(q)

        normal_audio = 'MP3_128', 'MP3_320', 'FLAC'
        surround_audio = '360_RA3', '360_RA2', '360_RA1'
        if selected_quality in normal_audio:
            return normal[len(normal) - 1]
        else:
            return surround[len(surround) - 1]


    def get_stream(self, quality):
        quality_to_number = {
            'MP3_128': '1',
            'MP3_320': '3',
            'FLAC': '9',
            '360_RA3': '15',
            '360_RA2': '14',
            '360_RA1': '13',
        }
        quality = quality_to_number[quality]

        # get track url
        # step 1: put a bunch of info together and hash it
        step1 = b'\xa4'.join(map(lambda s: s.encode(), [
            self.md5_origin,
            quality,
            str(self.song_id),
            self.media_version
        ]
        ))

        hash = hashlib.new('md5')
        hash.update(step1)
        step1_hash = hash.hexdigest()

        #  - step 2: hash + info + add padding
        step2 = str.encode(step1_hash) + b'\xa4' + step1 + b'\xa4'
        while len(step2) % 16 > 0:
            step2 += b'.'

        #  - step 3: AES encryption to get url
        # it will encrypt in parts of 16
        step3 = b''
        aes = pyaes.AESModeOfOperationECB(b'jo6aey6haid2Teih')
        for index in range(int(len(step2) / 16)):
            block = step2[(index * 16):(index * 16) + 16]
            step3 += binascii.hexlify(aes.encrypt(block))

        #  - step 4: make url
        url = 'http://e-cdn-proxy-{}.deezer.com/mobile/1/{}'.format(
            self.md5_origin[0],  # first char of md5origin is cdn to use
            step3.decode('utf-8')
        )

        try:
            response = urlopen(url)
        except urllib.error.HTTPError as e:
            return False
        except ConnectionResetError as e:
            print(e)
            raise NotImplementedError('Error getting deezer track url')

        output_stream = bytearray()
        return DeezerTrackStream(url)


    def stream(self, stream, track_stream, task=None, dlthread=None):
        """
        1. Download encrypted bytearray from deezer with self.stream_encrypted()
        2. check if 403 Error
        3. get size of encrypted file, create start stop index for workers with deezer.utils.worker_blocks
        4. uses 4 workers with mutliprocessing to decrypt the bytearray
        5. `stream` write to file
        """
        if cc.deezer_inline_decrypt:
            # slow stream
            from generic.utils import print_progress_callback
            self.stream_inline(stream, track_stream.url, progress_callback=print_progress_callback)
            return

        # default fast, uses multiprocessing
        in_bytes = self.stream_encrypted(track_stream, task=task, dlthread=dlthread)

        if type(in_bytes) is str:
            if 'HTTP Error' in in_bytes:
                return in_bytes

        out_bytes = bytearray()

        out_bytes = self.decrypt(in_bytes)

        # write to stream
        stream.write(out_bytes)

    def decrypt(self, bytes_in):
        """
        decrypts chunk of bytes or complete audiofile
        Args:
            `w_block` tuple (INDEX, BYTES_IN)
        """
        bytes_out = bytearray()

        # get blowfish key
        h = deezer.utils.md5hex(b'%d' % int(self.song_id))
        key = ''.join(chr(h[i] ^ h[i + 16] ^ deezer.utils.BLOWFISH_SECRET[i]) for i in range(16)).encode('UTF8')

        length = len(bytes_in)
        i = 0

        while True:
            # check if length is reached
            if len(bytes_out) == length:
                break

            # end reached read last bytes which are not a full 2048 stack
            if (i + 1) * 2048 > length:
                chunk = bytes_in[i * 2048::]
            else:
                # read 2048 bytes each cycle = i * 2048
                chunk = bytes_in[i * 2048: (i + 1) * 2048]

            # decrypt chunk
            if (i % 3) == 0 and len(chunk) == 2048:
                chunk = deezer.utils.decrypt_chunk(chunk, key)

            # add chunk to outbytes
            bytes_out += chunk

            # increase index
            i += 1

        # return bytearray
        return bytes_out


    def stream_encrypted(self, track_stream, task=None, dlthread=None):
        """download encrypted audiofile in bytearray format
        Args:
            `task` if self.download is called from DownloadThread
            for status updates
        """
        super().stream(track_stream=track_stream, output_stream=track_stream, task=task, dlthread=dlthread)
        return track_stream.output_stream

    def download(self, to_file=None, quality=None, folder=None, task=None, lower_quality=False, dlthread=None) -> DownloadResult:
        status_code = 0
        status_text = ''
        selected_quality = None
        if quality not in self.qualities:
            if lower_quality:
                selected_quality = quality
                quality = None
                status_code = 101
            else:
                return DownloadResult('', 201, 'Track has not requested quality!')
        if quality == None:
            quality = self.guess_quality(selected_quality)
            status_text = quality # code 101
            # file format could be different now
            to_file = self.path.file_name_quality(quality)

        track_stream = self.get_stream(quality)
        if track_stream == False:
            return DownloadResult('', 202, 'deezer quality error')
        file_name = os.path.join(folder, to_file)

        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception:
            pass  # race condition in multithreaded

        with open(file_name, 'wb') as stream:
            self.stream(stream, track_stream, task=task, dlthread=dlthread)
        return DownloadResult(file_name, status_code, status_text)

    def get_lyrics(self, deezer):
        self.lyrics = deezer.get_lyrics(self.song_id)

    def stream_inline(self, stream, url, progress_callback=None):
        """
        old implementation of track stream, downloads 2048 bytes then decrypts it and writes it to stream object (directly to file)
        """

        # get blowfish key
        h = deezer.utils.md5hex(b'%d' % int(self.song_id))
        key = ''.join(chr(h[i] ^ h[i + 16] ^ deezer.utils.BLOWFISH_SECRET[i]) for i in range(16)).encode('UTF8')

        response = urlopen(url)
        length = int(response.getheader('Content-Length'))

        i = 0
        while True:
            chunk = response.read(2048)
            if progress_callback != None:
                if (i * 2048) > length:
                    progress_callback(1)
                else:
                    progress_callback((i * 2048) / length)
            if not chunk:
                break
            if (i % 3) == 0 and len(chunk) == 2048:
                chunk = deezer.utils.decrypt_chunk(chunk, key)
            stream.write(chunk)
            i += 1

class DeezerTrackLyrics:
    def __init__(self, raw_data):
        """init with raw_data from `deezer.get_lyrics`"""
        self.lyrics_writers = raw_data['results'].get('LYRICS_WRITERS', '')
        self.lyrics_text = raw_data['results'].get('LYRICS_TEXT', '')
        raw_lyrics_synced = raw_data['results'].get('LYRICS_SYNC_JSON', '')
        self.lyrics_synced = ''
        for entry in raw_lyrics_synced:
           if entry['line'] != '':
            self.lyrics_synced += '{} {}\r\n'.format(entry['lrc_timestamp'], entry['line'])

class DeezerTrackStream:
    """small helper for generic.track.stream"""
    def __init__(self, url):
        self.url = url
        self.output_stream = bytearray()
    def write(self, _bytes):
        """trickery for deezer track, because
        it's a byte array"""
        self.output_stream += _bytes
