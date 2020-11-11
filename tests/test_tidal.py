import unittest

from chimera.download import any_track
from chimera.tag import Tagger
from cli.utils import master_login
from db import cc
from tidal.tidal import Tidal


class TidalTest(unittest.TestCase):
    def setUp(self):
        self.tidal = Tidal()
        master_login(tidal=self.tidal, verbose=False)

    def test_track_download(self):
        track = self.tidal.get_track(113297575)
        track.update_tags(self.tidal)
        ds = any_track(track, self.tidal)
        track.update_tags(ds.file_name)
        self.assertTrue(ds.failed == False)

    def test_track_metadata(self):
        track = self.tidal.get_track(113297575)
        status = track.update_tags(self.tidal)
        tagger = Tagger(track, '.flac')

    def test_album_metadata(self):
        album = self.tidal.get_album(26531974)
        for track in album.songs:
            track.update_tags(self.tidal)
            tagger = Tagger(track, '.flac')

    def test_playlist_metadata(self):
        playlist = self.tidal.get_playlist('ee210a7d-ffba-4fdf-a0b1-31c763b2c6d1')
        for track in playlist.songs:
            track.update_tags(self.tidal)
            tagger = Tagger(track, '.flac')

    def test_various_artists_album(self):
        album = self.tidal.get_album(109547366)
        flag = True
        for track in album.songs:
            if 'Various Artists' not in track.path.full_file_name:
                flag = False
        self.assertTrue(flag)