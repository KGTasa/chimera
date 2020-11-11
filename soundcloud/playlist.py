class SoundcloudPlaylist():
    def __init__(self, raw_data):
        self.name = raw_data['title']
        self.playlist_id = raw_data['id']
        self.song_count = raw_data['track_count']
        self.description = raw_data['description']
        self.images = raw_data['artwork_url']
        self.songs = []
