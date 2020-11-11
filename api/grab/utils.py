def create_deezer_tracks(raw_data):
    track_list = []
    for track_data in raw_data:
        track_list.append({
            'song_id': track_data['SNG_ID'],
            'title': track_data['SNG_TITLE'],
            'artist': track_data['ART_NAME'],
            'album': track_data['ALB_TITLE'],
            'type': 'deezer',
            'album_id': track_data['ALB_ID']
        })
    return track_list

def create_deezer_tracks_playlist(raw_data):
    track_list = []
    for track_data in raw_data:
        track_list.append({
            'song_id': track_data['id'],
            'title': track_data['title'],
            'artist': track_data['artist']['name'],
            'album': track_data['album']['title'],
            'type': 'deezer'
        })
    return track_list


def create_tidal_tracks(raw_data):
    track_list = []
    for track_data in raw_data:
        track_list.append({
            'song_id': track_data['id'],
            'title': track_data['title'],
            'artist': track_data['artist']['name'],
            'album': track_data['album']['title'],
            'type': 'tidal',
            'album_id': track_data['album']['id']
        })
    return track_list


def create_qobuz_tracks(raw_data):
    track_list = []
    for track_data in raw_data['tracks']['items']:
        track_list.append({
            'song_id': track_data['id'],
            'title': track_data['title'],
            'artist': track_data['performer']['name'],
            'album': raw_data['title'],
            'type': 'qobuz',
            'album_id': raw_data['id']
        })
    return track_list

def create_qobuz_tracks_playlist(raw_data):
    track_list = []
    for track_data in raw_data:
        track_list.append({
            'song_id': track_data['id'],
            'title': track_data['title'],
            'artist': track_data['performer']['name'],
            'album': track_data['album']['title'],
            'type': 'qobuz'
        })
    return track_list