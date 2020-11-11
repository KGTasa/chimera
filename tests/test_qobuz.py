import unittest

from chimera.download import any_track
from chimera.tag import Tagger
from cli.utils import master_login
from db import cc
from qobuz.qobuz import Qobuz


class QobuzTest(unittest.TestCase):
    def setUp(self):
        self.qobuz = Qobuz()
        master_login(qobuz=self.qobuz, verbose=False)

    def test_track_download(self):
        track = self.qobuz.get_track(64366361)
        track.update_tags(self.qobuz)
        ds = any_track(track, self.qobuz)
        track.update_tags(ds.file_name)
        self.assertTrue(ds.failed == False)

    def test_track_metadata(self):
        track = self.qobuz.get_track(64366361)
        status = track.update_tags(self.qobuz)
        tagger = Tagger(track, '.flac')

    def test_album_metadata(self):
        album = self.qobuz.get_album('wu7uac4147csc')
        for track in album.songs:
            track.update_tags(self.qobuz)
            tagger = Tagger(track, '.flac')

    def test_playlist_metadata(self):
        playlist = self.qobuz.get_playlist(1784198)
        for track in playlist.songs:
            track.update_tags(self.qobuz)
            tagger = Tagger(track, '.flac')
