import unittest

from chimera.tag import Tagger
from cli.utils import master_login
from db import cc
from gpm.gpm import GPM


class GPMTest(unittest.TestCase):
    def setUp(self):
        self.gpm = GPM(cc.gpm_device_id)
        master_login(gpm=self.gpm, verbose=False)

    def test_track_grab(self):
        track = self.gpm.get_track('Tswhyxgv4dkxo5ikcwrz7qrtmiy')
        track.update_tags(self.gpm)
        tagger = Tagger(track, '.m4a')
    def test_album_grab(self):
        album = self.gpm.get_album('Btak6x6jwqxkgo6b5w4gr4vuhzi')
        for track in album.songs:
            track.update_tags(self.gpm)
            tagger = Tagger(track, '.m4a')
