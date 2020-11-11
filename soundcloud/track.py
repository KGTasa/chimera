import os
import urllib.request

from mutagen.id3 import APIC, ID3
from mutagen.mp3 import MP3, EasyMP3
from db import cc
from generic.track import Track
from generic.utils import remove_illegal_characters

class SoundcloudTrack(Track):
    def set_raw_data(self, song_data):
        self.set_values(
            title=song_data['title'],
            song_id=song_data['id'],
            artists=song_data['user'],
            artist=song_data['user']['username'],
            streamable=song_data['streamable'],
            duration=song_data['duration'],
            downloadable=song_data['downloadable'],
            genre=song_data['genre'],
            isrc=song_data.get('isrc', None),
            kind=song_data['kind'],
            original_content_size=song_data['original_content_size'],
            original_format=song_data['original_format'],
            permalink_url=song_data['permalink_url'],
            date=song_data['release_year'], # album
            stream_url=song_data['stream_url'],
            cover=song_data['artwork_url'],
            streams=list(map(lambda x: SoundCloudTrackStream(x), song_data['media']['transcodings'])) if 'media' in song_data else None
        )

    def set_values(
        self,
        title=None,
        song_id=None,
        artists=None,
        artist=None,
        streamable=None,
        duration=None,
        downloadable=None,
        genre=None,
        isrc=None,
        kind=None,
        original_content_size=None,
        original_format=None,
        permalink_url=None,
        date=None,
        stream_url=None,
        cover=None,
        raw_data=None,
        streams=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.song_id = song_id
        self.title = title
        self.artists = artists
        self.artist = artist
        self.streamable = streamable
        self.duration = duration
        self.downloadable = downloadable
        self.genre = genre # needs to be in SoundCloud.album
        self.isrc = isrc
        self.kind = kind
        self.original_content_size = original_content_size
        self.original_format = original_format
        self.permalink_url = permalink_url
        self.date = date
        self.stream_url = stream_url  # needs testing if hls is needed
        self.cover = cover  # album if -large change it to -t500x500
        self.lyrics = None
        self.streams = streams # soundcloud gives all needed infos in grabtrack

        if cover and 'large' in cover:
            self.cover = cover.replace('large', 't500x500')


        self.track_number = ''
        self.gain = ''
        self.disk_number = ''
        self.bpm = ''

        self.service = 'soundcloud'

    def get_stream(self, soundcloud):
        # go tracks return stream object
        if self.streams != None:
            stream_url = next(filter(lambda x: x.preset == 'aac_hq',
                              list(filter(lambda x: x.quality == 'hq', self.streams))
            )).url
            return soundcloud.get_stream_go(stream_url)
        else:
            return soundcloud.get_stream(self.stream_url)

    def stream(self, track_stream, output_stream, task=None):
        if type(track_stream) is SoundcloudTrackStreamHLS:
            size = self.original_content_size / float(2 ** 20)
            from chimera.grabber import fetch_snd
            streams = fetch_snd(size, track_stream.streams)
            for stream in streams:
                output_stream.write(stream.data)

            # for tstream in track_stream.streams:
            #     super().stream(track_stream=tstream, output_stream=output_stream, task=task)
        else:
            super().stream(track_stream=track_stream, output_stream=output_stream, task=task)

    def download(self, soundcloud, folder=None, to_file=None, task=None):
        """
        download track
        Args:
            `folder` Complete folder structure until Track
            `to_file` File name with extension, if None, gets created
        """
        track_stream = self.get_stream(soundcloud)
        if type(track_stream) is SoundcloudTrackStreamHLS:
            file_format = track_stream.format
        else:
            file_format = '.mp3' # TODO

        if to_file == None:
            to_file = self.generate_file_name(file_format)

        file_name = os.path.join(folder, to_file)

        # create folder
        if not os.path.exists(folder):
            os.makedirs(folder)

        with open(file_name, 'wb') as stream:
            res = self.stream(track_stream, stream, task=task)

        if res is False:
            return False

        return file_name


    def generate_file_name(self, ext):
        """generates file name for track
        Artist - TR# - Track Name
        Arg:
          ext -> .mp3, .flac"""

        track_name = '{} - {}'.format(self.artist, self.title)
        return remove_illegal_characters(track_name) + ext

    def generate_folder_path(self, with_album=False):
        """Generates folder struction without track name"""
        if with_album:
            return os.path.join(remove_illegal_characters(self.artist), remove_illegal_characters(self.album.title))
        else:
            return remove_illegal_characters(self.artist)

    def generate_full_path(self, ext):
        """generates full path, Artist\\Artist - Track Name.ext)"""
        return os.path.join(self.generate_folder_path(), self.generate_file_name(ext))


    def tag(self, file):
        """
        Soundcloud does not always have an album, so has it's own tag function
        because why not
        Keys from Soundcloud track are also different
        """
        tag = EasyMP3(file)
        tag.delete()
        if cc.tag_artist:
            tag['artist'] = self.artist
        if cc.tag_title:
            tag['title'] = self.title
        if cc.tag_date:
            tag['date'] = str(self.date)
        if cc.tag_genre:
            tag['genre'] = self.genre
        if cc.tag_albumartist:
            tag['albumartist'] = self.artist
        if cc.tag_bpm:
            tag['bpm'] = str(self.bpm)
        if cc.tag_length:
            tag['length'] = str(self.duration)
        if cc.tag_isrc:
            if self.isrc:
                tag['isrc'] = self.isrc
        if cc.tag_gain:
            if self.gain:
                tag['replaygain_*_gain'] = str(self.gain)
        tag.save()

        # image
        if cc.tag_cover:
            if self.cover:
                try:
                    audio = MP3(file, ID3=ID3)
                    res = urllib.request.urlopen(self.cover)
                    audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=res.read()))
                    res.close()
                    audio.save()
                except urllib.error.HTTPError as e:
                    pass
                    # log.warning(f'No Cover for {self}')

class SoundCloudTrackStream:
    def __init__(self, raw_data):
        if type(raw_data) is str:
            self.url = raw_data
        else:
            self.duration = raw_data['duration']
            self.mime_type = raw_data['format']['mime_type']
            self.protocol = raw_data['format']['protocol']
            self.preset = raw_data['preset']
            self.quality = raw_data['quality']
            self.url = raw_data['url']

class SoundcloudTrackStreamHLS:
    def __init__(self, raw_data):
        lines = raw_data.split('\n')
        headers = ['#EXTM3U', '#EXT-X-VERSION:6', '#EXT-X-PLAYLIST-TYPE:VOD', '#EXT-X-TARGETDURATION:10', '#EXT-X-MEDIA-SEQUENCE:0']
        lines = list(filter(lambda x: x not in headers, lines)) # first line #EXT-X-MAP:URI="
        first = lines.pop(0).replace('#EXT-X-MAP:URI=', '').replace('"', '')
        urls = []
        for line in lines:
            if line.startswith('http'):
                urls.append(line)
        self.streams = [SndHlsStream(x, i) for i, x in enumerate(urls)]
        self.format = '.m4a' if 'm4a' in first else '.mp3'

class SndHlsStream():
    def __init__(self, url, pos):
        self.url = url
        self.pos = pos
        self.data = bytearray()

    def write(self, _bytes):
        self.data += _bytes
