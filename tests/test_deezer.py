import unittest

from chimera.download import any_track
from chimera.tag import Tagger
from cli.utils import master_login
from db import cc
from deezer.deezer import Deezer
from generic.utils import cover_tester

class DeezerTest(unittest.TestCase):
    def setUp(self):
        self.deezer = Deezer()
        master_login(deezer=self.deezer, verbose=False)

        # change config for tests
        # cc.deezer_quality = 'FLAC'
        # cc.root_path = 'D:\\temp\\Musik_test'


    def test_login(self):
        self.assertTrue(self.deezer.login_with_cookie(cc.deezer_username))

    def test_track_download(self):
        track = self.deezer.get_track(698905582)
        track.update_tags(self.deezer)
        ds = any_track(track, self.deezer)
        track.update_tags(ds.file_name)
        self.assertTrue(ds.failed == False)

    def test_track_metadata(self):
        track = self.deezer.get_track(698905582)
        track.update_tags(self.deezer)
        tagger = Tagger(track, '.flac')

    def test_album_metadata(self):
        album = self.deezer.get_album(7463461)
        for track in album.songs:
            track.update_tags(self.deezer)
            tagger = Tagger(track, '.flac')

    def test_playlist_metadata(self):
        for id in ['37i9dQZF1DXc9orRugI29r', '4365127622']:
            playlist = self.deezer.get_playlist(id)
            for track in playlist.songs:
                track.update_tags(self.deezer)
                tagger = Tagger(track, '.flac')
                self.assertTrue(cover_tester(track.album.picture_url))

    def test_various_artists_album(self):
        album = self.deezer.get_album(86790432)
        flag = True
        for track in album.songs:
            if 'Various Artists' not in track.path.full_file_name:
                flag = False
        self.assertTrue(flag)