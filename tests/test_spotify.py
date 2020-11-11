import unittest

import chimera.spotify




class SpotifyTest(unittest.TestCase):
    # def setUp(self):
    def test_token(self):
        self.assertTrue(chimera.spotify.create_token(open_auth_url=False))
        # bad test, if token is not created, waits forever because of flask thread