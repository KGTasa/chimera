import gpm.track

class GPMPlaylist():
    def __init__(self, raw_data, playlist_name=None):
        if playlist_name == None:
            self.name = 'GPM Playlist'
        else:
            self.name = playlist_name
        self.playlist_id = ''
        self.is_public = True
        self.description = ''
        self.owner = ''
        self.images = ''
        tracks = []
        for raw_track in raw_data:
            _track = gpm.track.GPMTrack.grab_or_create(raw_track['track']['storeId'], raw_data=raw_track['track'])
            _track.is_playlist = True
            _track.playlist_name = self.name
            _track.playlist_index = str(len(tracks) + 1)
            tracks.append(_track)
        self.songs = tracks
        self.song_count = len(self.songs)
        for track in self.songs:
            track.playlist_length = self.song_count
