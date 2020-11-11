"""
Downloads a complete Qobuz Label
"""

import os
import pickle
import time

import chimera.download
import chimera.concurrency

from config import log
from db import cc

import_path = 'import'
cache_path = 'cache'
cache_label = os.path.join(import_path, cache_path, 'label_{}.pkl')

LAYOUT_VERSION = 1

def get_label(label_id, qobuz, ignore_cache=False):

    label = None
    if not ignore_cache and os.path.exists(cache_label.format(label_id)):
        # load file
        with open(cache_label.format(label_id), 'rb') as f:
            label = pickle.load(f)

        # check timestamp
        tstamp = os.path.getmtime(cache_label.format(label_id))
        if time.time() > tstamp + 8 * 24 * 60 * 60: # 8 days
            discography = None
            log.info('Removed Label cache because it expired.')

        # check layout
        if label.version < LAYOUT_VERSION:
            discography = None
            log.info('Removed Label cache because older layout version.')

    if label is None:
        raw_label, albums = qobuz.get_label(label_id)
        label = Label(raw_label, albums)
        with open(cache_label.format(label_id), 'wb') as f:
            pickle.dump(label, f)

    return label

class Label:
    def __init__(self, raw_data, albums):
        """Basic infos about a label"""
        self.service = 'qobuz'
        self.label = raw_data['name']
        self.label_id = raw_data['id']
        self.albums_count = raw_data['albums_count']
        self.version = 1

        # update track infos that they are in a label
        for album in albums:
            for track in album.songs:
                track.label_member = True
        self.albums = albums
        self.track_count = sum(list(map(lambda x: len(x.songs), albums)))

    def download(self, qobuz, concurrency=False):
        import cli.utils
        print(f'Donwloading Label: {self.label} with {self.albums_count} Albums and {self.track_count} Tracks')

        if not concurrency:
            for album in self.albums:
                print('grabbing qobuz album %s' % album.title)
                for track in album.songs:
                    ds = chimera.download.any_track(track, qobuz, overwrite=cc.dl_album_overwrite,
                                                    add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db)
                    cli.utils.parse_ds(ds)
        else:
            for album in self.albums:
                chimera.concurrency.blackhole(album, 'album')
