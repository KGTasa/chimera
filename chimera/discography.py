import os
import pickle
import re
import time

import chimera
import chimera.concurrency
from config import log
from db import cc

import_path = 'import'
cache_path = 'cache'
cache_artist = os.path.join(import_path, cache_path, '{}.pkl')

# RE_VERSION = re.compile('[^[a-zA-Z]live[^[a-zA-Z]|rmx|remix', re.IGNORECASE)
RE_VERSION = re.compile(cc.discography_filter, re.IGNORECASE)

LAYOUT_VERSION = 1

def check_dir():
    if os.path.exists(os.path.join(import_path, cache_path)) is False:
        os.makedirs(os.path.join(import_path, cache_path))


def get_discography(artist_id, session, ignore_cache=False):
    """get all albums and singles from artist id"""
    check_dir()

    discography = None
    # check if artist is cached
    if ignore_cache == False and os.path.exists(cache_artist.format(artist_id)):
            # load with pickle
            with open(cache_artist.format(artist_id), 'rb') as f:
                discography = pickle.load(f)

            # check if older than 24hours
            tstamp = os.path.getmtime(cache_artist.format(artist_id))
            if time.time() > tstamp + 24 * 60 * 60:
                discography = None
                log.info('Removed discography cache because it expired.')

            # check version
            if discography.version < LAYOUT_VERSION:
                discography = None
                log.info('Removed discography cache because older layout version.')

    if discography is None:
        # get albums and save
        albums = session.get_albums_from_artist(artist_id)
        discography = Discography(str(session).lower(), albums[0].artists[0].name, artist_id, albums)
        with open(cache_artist.format(artist_id), 'wb') as f:
            pickle.dump(discography, f)

    return discography



class Discography():
    def __init__(self, service, artist, artist_id, albums):
        """Init Discography with basic informations
        Args:
            `service` string of the service, e.g. `deezer`
            `artist` string of the artist name not the complete object
            `artist_id` self explanatory
            `albums` all albums
        """
        self.service = service
        self.artist = artist
        self.artist_id = artist_id
        self.albums = albums
        self.version = 1 # bump version number if track or album layout changes!


    def check(self):
        for album in self.albums:
            if cc.discography_filter != '':
                album = check_album(album)
            else:
                for track in album.songs:
                    track.discography_allowed = True


    def download(self, session):
        if cc.concurrency:
            chimera.concurrency.blackhole(self, 'discography')
            return

        song_counter = 0
        for album in self.albums:
            print('Album: {}, Songs: {}, Single: {}'.format(album.title, len(album.songs), album.is_single))
            for track in album.songs:
                if track.discography_allowed:
                    chimera.download.any_track(
                        track,
                        session,
                        track_type=track.service,
                        overwrite=cc.dl_discography_overwrite,
                        add_to_db=cc.dl_discography_add_to_db,
                        check_db=cc.dl_discography_check_db
                    )
                    song_counter += 1
        print(f'Total Songs: {song_counter}')
        print(f'Total Albums: {len(self.albums)}')


    def write_report(self):
        """writes a csv file with allowed songs"""
        from chimera.csv import discography_report
        discography_report(
            file_path=os.path.join(import_path, cache_path, 'discography_report_{}_{}.csv'.format(self.artist, self.service)),
            discography=self
        )

    # for album in albums:
    #     album = check_album(album)
def check_album(album):
    """
    loops through all songs of an album and checks if it's allowed to download
    does not change the size of the album only adds a true or false flag
    """
    tracks_clean = []
    for i, track in enumerate(album.songs):
        # blacklist = ['LIVE']
        song_is_clean = None
        if track.version:
            song_is_clean = RE_VERSION.search(track.version)
        song_is_clean = RE_VERSION.search(track.title)
        if song_is_clean is None:
            # tracks_clean.append(track)
            track.discography_allowed = True
        else:
            track.discography_allowed = False

    # album.songs = tracks_clean
    if RE_VERSION.search(album.title):
        for track in album.songs:
            track.discography_allowed = False
    # if len(album.songs) == 0:
    #     print('Album {} has no songs'.format(album.title))
    return album
