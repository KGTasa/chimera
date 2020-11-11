import db.models
from db.db import create_session
from .utils import sql_retry

@sql_retry
def add(track):
    """
    Add Deezer Track to database
    Searches for existing track with track.remote_id if not found
    creates a new entry
    """
    session = create_session()
    _track = session.query(db.models.DBTrack).filter_by(remote_id=track.song_id).first()
    if _track is None:
        # track not existing, create new
        dbtrack = db.models.DBTrack(
            name=track.title,
            artist=track.artist,
            album=track.album.title,
            release_date=track.album.date,
            isrc=track.isrc,
            spotify_id=track.spotify_id if hasattr(track, 'spotify_id') else None,
            remote_id=track.song_id,
            path=track.path.full_file_name,
            remote_duration=track.duration,
            service=track.service
        )
        session.add(dbtrack)
        session.commit()
    else:
        # track exists
        _track.name = track.title
        _track.artist = track.artist
        _track.album = track.album.title
        _track.release_date = track.album.date
        _track.isrc = track.isrc
        _track.spotify_id = track.spotify_id if hasattr(track, 'spotify_id') else None
        _track.remote_id = track.song_id
        _track.path = track.path.full_file_name
        _track.remote_duration = track.duration
        _track.service = track.service
        session.commit()
