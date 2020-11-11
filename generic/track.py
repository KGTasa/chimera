import os
from urllib.error import HTTPError

import requests
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3, USLT
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3, EasyMP3
from mutagen.mp4 import MP4, MP4Cover
from tqdm import tqdm

from chimera.tag import Tagger
from config import log
from db import cc
from .object import Object
from .utils import remove_illegal_characters, DownloadResult


def guess_file_name(track):
    return ', '.join(map(lambda a: a.name, track.artists)) + ' - ' + track.title


def generate_map(track, is_folder=False):
    # Various Artist album fix
    artist = track.artist
    if is_folder and track.is_compilation:
        artist = ', '.join(list(map(lambda x: x.name, track.album.artists)))

    track_nr = track.track_number
    if cc.pad_track:
        track_nr = str(track_nr).zfill(int(cc.pad_track_width))
        if track.playlist_index:
            track.playlist_index = str(track.playlist_index).zfill(int(cc.pad_track_width))


    return {
        'TITLE': track.title,
        'ARTIST': artist,
        'ALBUM': track.album.title,
        'TRACK': track_nr,
        'PLAYLIST': track.playlist_name, # could be None
        'PLNR': track.playlist_index,
        'LABEL': track.album.label,
        'YEAR': track.year if track.year else '0000', # year tag only gets updated after track.update_tags() is called
        'DISCNUMBER': track.disk_number,
        'DATE': track.album.date,
        'EXPLICIT': 'E' if track.explicit else ''
    }

class Track(Object):
    def __init__(self, *args, **kwargs):
        self.bpm = None
        self.lyrics = None
        self.is_playlist = False
        self.playlist_name = None
        self.playlist_index = None
        self.playlist_length = None
        self.lyrics = None
        self.year = None
        self.copyright = None
        self.url = None
        self.gain = None
        self.isrc = None
        self.composer = None
        self.is_compilation = None
        self.label_member = None # only used for qobuz
        self.set_values(*args, **kwargs)


    def set_values(self, title=None, artists=None, album=None, qualities=None, raw_data=None, disk_number=None, track_number=None, isrc=None, duration=None):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.title = title
        self.artists = artists
        self.album = album
        self.qualities = qualities
        self.disk_number = disk_number
        self.track_number = track_number
        self.isrc = isrc
        self.spotify_id = None
        self.duration = None
        self.version = None

    def update_tags(self):
        """gets called after track updates tags
        used for generic stuff like discogs or track nr fix
        """
        if cc.merge_disks:
            if self.album.disks is None:
                return
            new_trnr = 0
            for i in range(int(self.disk_number) - 1, 0, -1):
                new_trnr += self.album.disks[i]
            new_trnr += int(self.track_number)

            self.track_number = new_trnr
            self.disk_number = 1



    def guess_file_name(self):
        return guess_file_name(self)

    def guess_quality(self):
        return self.qualities[len(self.qualities) - 1]

    def generate_file_name(self, ext, scheme=None):
        """generates file name for track
        Artist - TR# - Track Name
        Arg:
            ext -> .mp3, .flac
            `scheme` how track name should be formatted"""
        if scheme == None:
            scheme = 'ARTIST - TRACK - TITLE'

        _map = generate_map(self)
        for var, val in _map.items():
            scheme = scheme.replace(var, str(val))
        return remove_illegal_characters(scheme).strip() + ext

    def generate_folder_path(self, with_service=False, scheme=None):
        """Generates folder struction without track name
        Args:
            `with_service` adds a root folder with the service name
                           before artist
            `scheme` used for playlist folder generation
        """

        if scheme == None:
            scheme = ['ARTIST', 'ALBUM']

        _map = generate_map(self, is_folder=True)
        for var, val in _map.items():
            for i, _ in enumerate(scheme):
                scheme[i] = scheme[i].replace(var, str(val))

        if with_service:
            scheme.insert(0, self.service.capitalize())
        return os.path.join(*[remove_illegal_characters(path).strip() for path in scheme])

    def generate_full_path(self, ext, scheme=None, folder_scheme=None, with_service=False, gen_type=None):
        """generates full path, Artist\\Album\\Artist - Track NR# - Track Name.ext)
        Args:
            `gen_type` if None default generation
        """
        if scheme == None:
            scheme = 'ARTIST - TRACK - TITLE'

        if folder_scheme == None:
            folder_scheme = ['ARTIST', 'ALBUM']

        return os.path.join(self.generate_folder_path(with_service=with_service, scheme=folder_scheme),
                            self.generate_file_name(ext, scheme=scheme))


    def save_lyrics(self, full_file_path):
        if self.lyrics != None:
            try:
                with open(full_file_path, 'w') as f:
                    f.write(self.lyrics.lyrics_synced)
            except UnicodeEncodeError as e:
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    f.write(self.lyrics.lyrics_synced)

    def stream(self, track_stream, output_stream, task=None, headers=None, dlthread=None):
        """generic download method for each track"""

        response = requests.get(track_stream.url, headers=headers, stream=True)
        length = int(response.headers.get('content-length'))

        if task:
            task.length = length

        if cc.cli and dlthread is None:
            bar = tqdm(total=length, unit='B', unit_scale=True, ncols=100, desc='downloading')

        chunk_size = 2048
        for chunk in response.iter_content(chunk_size=chunk_size):
            if task:
                task.downloaded += chunk_size
            if cc.cli and dlthread is None:
                bar.update(chunk_size)
            if not chunk:
                break
            output_stream.write(chunk)
        if cc.cli and dlthread is None:
            bar.close()
        if task:
            task.downloaded = length
        return


    def download(self, session, folder=None, to_file=None, quality=None, task=None,
                 lower_quality=False, truncate_filename=False, dlthread=None) -> DownloadResult:
        """used to got get stream, with error handling
        Used for: Tidal, Qobuz, Napster
        Deezer has it's own function maybe implement that here
        """
        status_code = 0
        status_text = ''
        if quality not in self.qualities:
            if lower_quality:
                quality = None
                status_code = 101
            else:
                return DownloadResult('', 201, 'Track has not requested quality!')
        if quality == None:
            quality = self.guess_quality()
            status_text = quality # code 101
            # get new file_format, problem different to_file is specified
            to_file = self.path.file_name_quality(quality)

        track_stream = self.get_stream(session, quality)

        # handle track_stream errors
        if type(track_stream) is str:
            if track_stream == 'TrackRestrictedByRightHolders':
                return DownloadResult('', 203, track_stream)
            if track_stream == 'Invalid Qobuz Secret':
                return DownloadResult('', 204, track_stream)
            if track_stream == "Asset is not available in user's location":
                return DownloadResult('', 205, track_stream)
            if track_stream == 'Asset is not ready for playback':
                return DownloadResult('', 207, track_stream)
            if track_stream == 'NapsterNoTrackStream':
                return DownloadResult('', 208, track_stream)

        file_name = os.path.join(folder, to_file)

        if truncate_filename:
            file_format = '.' + file_name.split('.')[-1]
            file_name = file_name[:250] + file_format
            status_code = 104
            status_text = 'File name too long, truncated.'

        try:
            if not os.path.exists(folder):
                os.makedirs(folder)
        except Exception:
            pass  # race condition in multithreaded

        try:
            with open(file_name, 'wb') as stream:
                try:
                    self.stream(track_stream, stream, task=task, dlthread=dlthread)
                except HTTPError as e:
                    return DownloadResult('', 206, str(e))
        except FileNotFoundError as e:
            # file name too long
            return self.download(session, folder=folder, to_file=to_file, quality=quality, task=task,
                                 lower_quality=lower_quality, truncate_filename=True, dlthread=dlthread)

        # check if tidal track is encrypted
        if self.service == 'tidal':
            if track_stream.encryption_key != '':
                self.decrypt(track_stream, file_name)
        return DownloadResult(file_name, status_code, status_text)

    def get_cover_data(self):
        """gets self.album.picture_url and returns it as bytearray
        """
        r = requests.get(self.album.picture_url)
        if r.status_code == 200:
            return r.content
        else:
            return False

    def tag(self, file):
        """
        Wraper function to create file tags
        Args:
            `file` full path to .mp3 or .flac file
        """
        if file.endswith('.mp3'):
            self._tag_mp3(file)
        if file.endswith('.flac'):
            self._tag_flac(file)
        if file.endswith(('.m4a', '.mp4')):
            self._tag_m4a(file)


    def _tag_mp3(self, file):
        """
        Tag Mp3 file only called from `track.tag()`
        """
        tagger = Tagger(self, '.mp3')
        tag = EasyMP3(file)
        EasyID3.RegisterTextKey('comment', 'COMM')
        tag.delete()

        for tag_obj in tagger.tag_map:
            tag[tag_obj.key] = str(tag_obj.value)
        tag.save()

        # image
        if cc.tag_cover and self.album.picture_url is not None:
            cover_data = self.get_cover_data()
            if cover_data:
                audio = MP3(file, ID3=ID3)
                audio.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=cover_data))
                audio.save()
            else:
                log.warning(f'No Cover for {self}')

        # lyrics
        if cc.tag_lyrics:
            if self.lyrics != None:
                tag = ID3(file)
                tag[u"USLT::'eng'"] = (USLT(encoding=3, lang=u'eng', desc=u'desc', text=self.lyrics.lyrics_text))
                tag.save()


    def _tag_flac(self, file):
        """
        Tag Flac file only called from `track.tag()`
        """
        tagger = Tagger(self, '.flac')
        tag = FLAC(file)
        tag.delete()

        for tag_obj in tagger.tag_map:
            tag[tag_obj.key] = str(tag_obj.value)

        # image
        if cc.tag_cover and self.album.picture_url is not None:
            cover_data = self.get_cover_data()
            if cover_data:
                img = Picture()
                img.type = 3
                img.data = cover_data
                tag.clear_pictures()
                tag.add_picture(img)
            else:
                log.warning(f'No Cover for {self}')
        tag.save()

    def _tag_m4a(self, file):
        tagger = Tagger(self, '.m4a')
        tag = MP4(file)

        for tag_obj in tagger.tag_map:
            if tag_obj.key in ['trkn']:
                tnr, dnr = tag_obj.value.split('/')
                tag[tag_obj.key] = [(int(tnr), int(dnr))]
            elif tag_obj.key in ['disk']:
                tag[tag_obj.key] = [(int(tag_obj.value), 0)]
            elif tag_obj.key in ['tmpo']:
                tag[tag_obj.key] = [int(tag_obj.value)]
            else:
                tag[tag_obj.key] = str(tag_obj.value)


        if cc.tag_cover and self.album.picture_url is not None:
            cover_data = self.get_cover_data()
            if cover_data:
                tag['covr'] = [MP4Cover(
                    cover_data, imageformat=MP4Cover.FORMAT_JPEG
                )]
            else:
                log.warning(f'No Cover for {self}')
        tag.save()

    def save_cover(self, path=None):
        if self.is_playlist and cc.save_as_compilation:
            return
        if self.album.picture_url is None:
            return
        if path == None:
            path = os.path.join(self.path.full_folder, cc.cover_file_name + '.jpg')
        req = requests.get(self.album.picture_url)
        with open(path, 'wb') as f:
            f.write(req.content)


    def get_lyrics(self, session):
        """Placeholder look into deezer.track"""
        return None


    def __repr__(self):
        artist_string = ', '.join(map(lambda a: a.name, self.artists))
        return f'ID {self.song_id} Track: {self.title}, Artist: {artist_string}, Album: {self.album.title}'
