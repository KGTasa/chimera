import unittest
from chimera.download import any_track
from chimera.tag import Tagger
from cli.utils import master_login
from db import cc
from napster.napster import Napster


class NapsterTest(unittest.TestCase):
    def setUp(self):
        self.napster = Napster(cc.napster_api_token)
        master_login(napster=self.napster, verbose=False)

    def test_track_download(self):
        track = self.napster.get_track(365693021)
        track.update_tags(self.napster)
        ds = any_track(track, self.napster)
        track.update_tags(ds.file_name)
        self.assertTrue(ds.failed == False)

    def test_track_metadata(self):
        track = self.napster.get_track(365693021)
        track.update_tags(self.napster)
        tagger = Tagger(track, '.m4a')

    def test_album_metadata(self):
        album = self.napster.get_album('alb.365693020')
        for track in album.songs:
            track.update_tags(self.napster)
            tagger = Tagger(track, '.m4a')
