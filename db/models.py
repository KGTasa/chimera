from sqlalchemy import Column, Integer, String, Boolean
from .db import Base

#track_name;artist;album;release_date;duration_ms;isrc
class DBTrack(Base):
    __tablename__ = 'dbtracks'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    artist = Column(String)
    album = Column(String)
    release_date = Column(String)
    isrc = Column(String)
    spotify_id = Column(Integer)
    remote_id = Column(Integer)
    path = Column(String)
    remote_duration = Column(Integer)
    service = Column(String)

    def __repr__(self):
        return f'ID: {self.id} {self.name} by {self.artist}'

class ChimeraConfig(Base):
    __tablename__ = 'chimeraconfigs'
    id = Column(Integer, primary_key=True)

    workers_already_created = False
    cli = True

    # chimera
    root_path = Column(String)
    prod = Column(Boolean)
    first_run = Column(Boolean)
    m3u = Column(Boolean) # create m3u file for playlist
    path_with_service = Column(Boolean)
    auto_login = Column(String)
    api_token = Column(String)
    merge_disks = Column(Boolean)
    pad_track = Column(Boolean)
    pad_track_width = Column(String)
    workers = Column(Integer)
    concurrency = Column(Boolean)
    save_cover = Column(Boolean)
    cover_file_name = Column(String)
    force_merge_albums = Column(Boolean)

    # spotify
    spotify_default_service = Column(String)
    spotify_blacklist = Column(String)
    spotify_username = Column(String)
    spotify_client_id = Column(String)
    spotify_client_secret = Column(String)
    spotify_redirect_uri = Column(String)
    spotify_scope = Column(String)

    # deezer
    deezer_username = Column(String)
    deezer_email = Column(String)
    deezer_password = Column(String)
    deezer_quality = Column(String)
    deezer_cover_size = Column(String)
    deezer_quality_fallback = Column(Boolean)
    deezer_inline_decrypt = Column(Boolean)

    # tidal
    tidal_email = Column(String)
    tidal_password = Column(String)
    tidal_quality = Column(String)
    tidal_cover_size = Column(String)
    tidal_quality_fallback = Column(Boolean)
    tidal_video_path = Column(String)
    tidal_video_pp = Column(Boolean) # post processing -> ffmpeg

    # qobuz
    qobuz_email = Column(String)
    qobuz_password = Column(String)
    qobuz_quality = Column(String)
    qobuz_app_id = Column(String)
    qobuz_secret = Column(String)
    qobuz_seed_type = Column(String)
    qobuz_cover_size = Column(String)
    qobuz_quality_fallback = Column(Boolean)

    # napster
    napster_email = Column(String)
    napster_password = Column(String)
    napster_quality = Column(String)
    napster_cover_size = Column(String)
    napster_api_token = Column(String)
    napster_quality_fallback = Column(Boolean)

    # GPM
    gpm_enabled = Column(Boolean)
    gpm_email = Column(String)
    gpm_password = Column(String)
    gpm_quality = Column(String)
    gpm_device_id = Column(String)

    # soundcloud
    soundcloud_username = Column(String)

    # discogs
    discogs_enabled = Column(Boolean)
    discogs_token = Column(String)

    # audio fingerprinting
    audio_acr_host = Column(String)
    audio_acr_access_key = Column(String)
    audio_access_secret = Column(String)
    audio_device_id = Column(Integer)
    audio_services = Column(String)

    # download
    dl_track_overwrite = Column(Boolean)
    dl_track_add_to_db = Column(Boolean)
    dl_track_check_db = Column(Boolean)

    dl_album_overwrite = Column(Boolean)
    dl_album_add_to_db = Column(Boolean)
    dl_album_check_db = Column(Boolean)

    dl_playlist_overwrite = Column(Boolean)
    dl_playlist_add_to_db = Column(Boolean)
    dl_playlist_check_db = Column(Boolean)

    dl_discography_overwrite = Column(Boolean)
    dl_discography_add_to_db = Column(Boolean)
    dl_discography_check_db = Column(Boolean)

    # track
    naming_scheme = Column(String)
    folder_naming_scheme = Column(String)

    # discography
    discography_filter = Column(String)

    # playlist
    save_as_compilation = Column(Boolean)
    playlist_naming_scheme = Column(String)
    playlist_folder_naming_scheme = Column(String)

    # tags
    tag_title = Column(Boolean)
    tag_artist = Column(Boolean)
    tag_date = Column(Boolean)
    tag_year = Column(Boolean)
    tag_cover = Column(Boolean)
    tag_album = Column(Boolean)
    tag_tracknumber = Column(Boolean)
    tag_discnumber = Column(Boolean)
    tag_genre = Column(Boolean)
    tag_albumartist = Column(Boolean)
    tag_bpm = Column(Boolean)
    tag_length = Column(Boolean)
    tag_organization = Column(Boolean)
    tag_isrc = Column(Boolean)
    tag_gain = Column(Boolean)
    tag_comment = Column(Boolean)
    tag_comment_value = Column(String)

    tag_dummy = True

    # lyrics
    tag_lyrics = Column(Boolean)
    save_lyrics = Column(Boolean)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def enable_tags(self):
        self.tag_title = True
        self.tag_artist = True
        self.tag_date = True
        self.tag_year = True
        self.tag_cover = True
        self.tag_album = True
        self.tag_tracknumber = True
        self.tag_discnumber = True
        self.tag_genre = True
        self.tag_albumartist = True
        self.tag_bpm = True
        self.tag_length = True
        self.tag_organization = True
        self.tag_isrc = True
        self.tag_gain = True

    def set_dl_behaviour(self):
        self.dl_track_overwrite = True
        self.dl_track_add_to_db = True
        self.dl_track_check_db = False
        self.dl_album_overwrite = True
        self.dl_album_add_to_db = True
        self.dl_album_check_db = False
        self.dl_playlist_overwrite = False
        self.dl_playlist_add_to_db = True
        self.dl_playlist_check_db = True
        self.dl_discography_overwrite = False
        self.dl_discography_add_to_db = True
        self.dl_discography_check_db = True

    def save(self):
        from .db import session
        session.commit()