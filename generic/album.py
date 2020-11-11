from .object import Object
from db import cc

class Album(Object):
    def __init__(self, *args, **kwargs):
        self.genre = None
        self.upc = None
        self.track_total = None
        self.disk_total = None
        self.label = None
        self.type = None
        self.disks = None
        self.set_values(*args, **kwargs)

    def post_init(self):
        # fix songs so album.songs[0].album.songs works
        if self.songs != None:
            for song in self.songs:
                song.album = self


        #calc disks: calculates how many disks there are
        # and how many tracks in each disk
        track_total = 0
        disks = {}
        i = 1
        if self.songs == None:
            return
        while track_total != len(self.songs):
            tr_total_disk = len(list(filter(lambda x: int(x.disk_number) == i, self.songs)))
            disks[i] = tr_total_disk
            track_total += tr_total_disk
            i += 1
        self.disks = disks

        # get first track, lets assume it is correct
        # this adds the song artist to every track if it isn't the same
        # should fix problems with albums that have some tracks from different artists
        # for more information see #44
        if cc.force_merge_albums:
            correct_artist = self.songs[0].artist
            correct_artists = None
            for track in self.songs:
                if track.artists[0].name == correct_artist:
                    correct_artists = track.artists[0]
                    break
            for track in self.songs:
                if not track.artist == correct_artist:
                    track.artist = correct_artist
                if not track.artists[0] == correct_artists:
                    track.artists = [correct_artists, *track.artists]

    def set_values(self, title=None, picture_url=None, artists=None, songs=None, raw_data=None, date=None):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.title = title
        self.date = date
        self.picture_url = picture_url
        self.artists = artists
        self.songs = songs


    @property
    def is_single(self):
        """only works if album is grabbed is wrong with deezer albums
        if single track is grabbed"""
        if self.songs != None and len(self.songs) == 1:
            return True
        else:
            return False

    def __repr__(self):
        # return f'ID {self.album_id}, Title: {self.title}, Artist: {self.artists[0].name}, Date: {self.date}, Song Count: {len(self.songs)}'
        # problem in api mode, artists none, songs none
        return f'ID {self.album_id}, Title: {self.title}'

    @property
    def quality(self):
        """looks through all tracks and selects the quality which is most common"""
        d = {}
        if self.songs:
            for track in self.songs:
                q = track.qualities[-1]
                if q in d:
                    d[q] += 1
                else:
                    d[q] = 1
            return max(d, key=str)
        return None
