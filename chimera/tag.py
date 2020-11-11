from __future__ import annotations
from typing import List

from db import cc
from config import log
class TagObject:
    def __init__(self, raw_data, format):
        self.value = raw_data['value']
        self.config = raw_data['config']
        self.key = raw_data[format]

    def __repr__(self):
        return f'< TagObject: {self.value} - {self.config} - {self.key} >'

class Tagger:
    def __init__(self, track, format):
        """format -> .flac, .mp3, .m4a"""

        self.tag_map = Tagger.generate_track_map(track, format)


        removed_keys_nonetype = [t for t in self.tag_map if t.value is None]
        self.tag_map[:] = [t for t in self.tag_map if t.value]
        if removed_keys_nonetype:
            log.debug('Keys removed because NoneType: {}'.format(', '.join([x.config for x in removed_keys_nonetype])))

        removed_keys_config = [t for t in self.tag_map if getattr(cc, t.config) is False]
        self.tag_map[:] = [t for t in self.tag_map if getattr(cc, t.config)]
        if removed_keys_config:
            log.debug('Keys removed because config: {}'.format(', '.join([x.config for x in removed_keys_config])))

        removed_keys_format = [t for t in self.tag_map if t.key is None]
        self.tag_map[:] = [t for t in self.tag_map if t.key]
        if removed_keys_format:
            log.debug('Keys removed because format does not support: {}'.format(', '.join([x.config for x in removed_keys_format])))

        self.removed_nonteype = removed_keys_nonetype
        self.removed_config = removed_keys_config
        self.removed_format = removed_keys_format

    @staticmethod
    def _flac_map(track):
        track_number = track.track_number
        track_total = track.album.track_total
        if track.is_playlist and cc.save_as_compilation:
            track_number = track.playlist_index
            track_total = track.playlist_length

        return [
            {'value': track_number,            'config': 'tag_tracknumber', '.flac': 'tracknumber'},
            {'value': track_total,             'config': 'tag_dummy',       '.flac': 'totaltracks'},
            {'value': track.album.disk_total,  'config': 'tag_dummy',       '.flac': 'totaldiscs'},

        ]

    @staticmethod
    def _mp3_map(track):
        if track.is_playlist and cc.save_as_compilation:
            track_number = f'{track.playlist_index}/{track.playlist_length}'
        else:
            track_number = f'{track.track_number}/{track.album.track_total if track.album.track_total else 0}'

        return [
            {'value': track_number, 'config': 'tag_tracknumber', '.mp3': 'tracknumber'}
        ]

    @staticmethod
    def _m4a_map(track):
        if track.is_playlist and cc.save_as_compilation:
            track_number = f'{track.playlist_index}/{track.playlist_length}'
        else:
            track_number = f'{track.track_number}/{track.album.track_total if track.album.track_total else 0}'

        return [
            {'value': track_number, 'config': 'tag_tracknumber', '.m4a': 'trkn'}
        ]

    @staticmethod
    def generate_track_map(track, format) -> List[TagObject]:
        artist = ', '.join(map(lambda a: a.name, track.artists))
        album_artist = track.artist
        album = track.playlist_name if track.is_playlist and cc.save_as_compilation else track.album.title
        lyrics = track.lyrics.lyrics_text if track.lyrics else None

        # album as compilation
        comp = None
        if track.is_compilation:
            comp = track.album.title
            album_artist = ', '.join(map(lambda a: a.name, track.album.artists))


        default_map = [
            {'value': artist,                  'config': 'tag_artist',       '.flac': 'artist',                '.mp3': 'artist',                '.m4a': '\xa9ART'},
            {'value': track.title,             'config': 'tag_title',        '.flac': 'title',                 '.mp3': 'title',                 '.m4a': '\xa9nam'},
            {'value': track.album.date,        'config': 'tag_date',         '.flac': 'date',                  '.mp3': 'date',                  '.m4a': None},
            {'value': track.year,              'config': 'tag_year',         '.flac': 'year',                  '.mp3': None,                    '.m4a': '\xa9day'},
            {'value': album,                   'config': 'tag_album',        '.flac': 'album',                 '.mp3': 'album',                 '.m4a': '\xa9alb'},
            {'value': track.disk_number,       'config': 'tag_discnumber',   '.flac': 'discnumber',            '.mp3': 'discnumber',            '.m4a': 'disk'},
            {'value': track.album.genre,       'config': 'tag_genre',        '.flac': 'genre',                 '.mp3': 'genre',                 '.m4a': '\xa9gen'},
            {'value': album_artist,            'config': 'tag_albumartist',  '.flac': 'albumartist',           '.mp3': 'albumartist',           '.m4a': 'aART'},
            {'value': track.bpm,               'config': 'tag_bpm',          '.flac': 'bpm',                   '.mp3': 'bpm',                   '.m4a': 'tmpo'},
            {'value': track.duration,          'config': 'tag_length',       '.flac': 'length',                '.mp3': 'length',                '.m4a': None},
            {'value': track.album.label,       'config': 'tag_organization', '.flac': 'organization',          '.mp3': 'organization',          '.m4a': 'cprt'},
            {'value': track.isrc,              'config': 'tag_isrc',         '.flac': 'isrc',                  '.mp3': 'isrc',                  '.m4a': None},
            {'value': track.gain,              'config': 'tag_gain',         '.flac': 'replaygain_track_gain', '.mp3': 'replaygain_track_gain', '.m4a': None},
            {'value': lyrics,                  'config': 'tag_lyrics',       '.flac': 'lyrics',                '.mp3': None,                    '.m4a': None}, # mp3 lyrics=true
            {'value': track.url,               'config': 'tag_dummy',        '.flac': 'url',                   '.mp3': None,                    '.m4a': None},
            {'value': track.explicit,          'config': 'tag_dummy',        '.flac': 'explicit',              '.mp3': None,                    '.m4a': None},
            {'value': track.copyright,         'config': 'tag_dummy',        '.flac': 'copyright',             '.mp3': 'copyright',             '.m4a': None},
            {'value': track.album.upc,         'config': 'tag_dummy',        '.flac': 'upc',                   '.mp3': None,                    '.m4a': None},
            {'value': track.composer,          'config': 'tag_dummy',        '.flac': 'composer',              '.mp3': 'composer',              '.m4a': '\xa9wrt'},
            {'value': comp,                    'config': 'tag_dummy',        '.flac': 'compilation',           '.mp3': 'compilation',           '.m4a': 'cpil'},
            {'value': cc.tag_comment_value,    'config': 'tag_comment',      '.flac': 'comment',               '.mp3': 'comment',               '.m4a': '\xa9cmt'}
        ]

        format_map_dict = {
            '.flac': Tagger._flac_map,
            '.mp3': Tagger._mp3_map,
            '.m4a': Tagger._m4a_map
        }
        format_map = format_map_dict[format]
        return [TagObject(x, format) for x in [*default_map, *format_map(track)]]
