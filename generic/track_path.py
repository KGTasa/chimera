import json
import os

from db import cc
from deezer.track_quality import DeezerTrackQuality
from napster.track_quality import NapsterTrackQuality
from qobuz.track_quality import QobuzTrackQuality
from tidal.track_quality import TidalTrackQuality


class GenericTrackPath:
    """Helper class to access different paths for a track
    Main function are still in the track Object for generating
    trackname and folder structure
    """
    def __init__(self, track):
        self.__track = track
        self.track_type = track.service

    def _get_scheme(self):
        """returns scheme objects for this track"""

        track_scheme = cc.naming_scheme
        folder_scheme = json.loads(cc.folder_naming_scheme)

        if self.__track.is_playlist and cc.save_as_compilation:
            folder_scheme = json.loads(cc.playlist_folder_naming_scheme)
            track_scheme = cc.playlist_naming_scheme
        if self.__track.label_member:
            folder_scheme = ['LABEL', 'ARTIST', 'ALBUM']
        return track_scheme, folder_scheme

    @property
    def file_name(self):
        """default file names based on config quality profile"""
        file_format = self._get_format()
        scheme, _ = self._get_scheme()
        return self.__track.generate_file_name(file_format, scheme=scheme)

    def file_name_quality(self, quality):
        """create new file names for fallback quality"""
        if self.track_type == 'deezer':
            file_format = DeezerTrackQuality.get_file_format(quality)
        elif self.track_type == 'tidal':
            file_format = TidalTrackQuality.get_file_format(quality)
        elif self.track_type == 'qobuz':
            file_format = QobuzTrackQuality.get_file_format(quality)
        elif self.track_type == 'napster':
            file_format = NapsterTrackQuality.get_file_format(quality)
        elif self.track_type == 'gpm':
            file_format = '.mp3'

        scheme, _ = self._get_scheme()
        return self.__track.generate_file_name(file_format, scheme=scheme)

    @property
    def folder(self):
        _, folder_scheme = self._get_scheme()
        return self.__track.generate_folder_path(with_service=cc.path_with_service, scheme=folder_scheme)

    @property
    def full_folder(self):
        """complete path to folder"""
        return os.path.join(cc.root_path, self.folder)


    def _full_file_name(self, file_format):
        track_scheme, folder_scheme = self._get_scheme()
        return self.__track.generate_full_path(file_format, scheme=track_scheme, folder_scheme=folder_scheme,
                                               with_service=cc.path_with_service)

    @property
    def full_file_name(self):
        """with folder and file_name"""
        file_format = self._get_format()
        return self._full_file_name(file_format)

    @property
    def full_path(self):
        """complete path to file"""
        return os.path.join(cc.root_path, self.full_file_name)


    def full_path_ext(self, file_format):
        return os.path.join(cc.root_path, self._full_file_name(file_format))

    def _get_format(self):
        if self.track_type == 'deezer':
            file_format = DeezerTrackQuality.get_file_format(cc.deezer_quality)
        elif self.track_type == 'tidal':
            file_format = TidalTrackQuality.get_file_format(cc.tidal_quality)
        elif self.track_type == 'qobuz':
            file_format = QobuzTrackQuality.get_file_format(cc.qobuz_quality)
        elif self.track_type == 'napster':
            file_format = NapsterTrackQuality.get_file_format(cc.napster_quality)
        elif self.track_type == 'gpm':
            file_format = '.mp3'
        return file_format

    def __getstate__(self):
        """used for api jsonpickle"""
        state = self.__dict__.copy()
        state['file_name'] = self.file_name
        state['folder'] = self.folder
        state['full_folder'] = self.full_folder
        state['full_file_name'] = self.full_file_name
        state['full_path'] = self.full_path
        return state
