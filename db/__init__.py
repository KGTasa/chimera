import os
import sys

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base

from .db import Base, engine, session
from .models import ChimeraConfig

def create_api_token():
    import uuid
    uid = uuid.uuid4()
    return uid.hex

def create_default_config():
    # create default configuration
    session.query(ChimeraConfig).delete()
    cc = ChimeraConfig()
    cc.naming_scheme = 'ARTIST - TRACK - TITLE'
    cc.folder_naming_scheme = '["ARTIST", "ALBUM"]'
    cc.spotify_redirect_uri = 'http://127.0.0.1:5000/callback'
    cc.spotify_scope = 'playlist-modify-public playlist-modify-private playlist-read-private user-read-recently-played user-top-read user-library-read'
    cc.enable_tags()
    cc.set_dl_behaviour()
    cc.gpm_device_id = 'CHANGEME'
    #covers
    cc.deezer_cover_size = '1200x1200'
    cc.tidal_cover_size = '1280x1280'
    cc.qobuz_cover_size = 'large'
    cc.napster_cover_size = 'MAX'
    # fallback
    cc.deezer_quality_fallback = True
    cc.tidal_quality_fallback = True
    cc.qobuz_quality_fallback = True
    cc.napster_quality_fallback = True
    # chimera
    cc.first_run = True
    cc.auto_login = ''
    cc.prod = True
    cc.api_token = create_api_token()
    cc.pad_track = True
    cc.pad_track_width = '2'
    cc.concurrency = False
    cc.workers = 8
    cc.spotify_default_service = 'deezer'
    cc.save_cover = False
    cc.cover_file_name = 'cover'

    # playlist
    cc.playlist_naming_scheme = 'PLNR - TITLE - ARTIST'
    cc.playlist_folder_naming_scheme = '["PLAYLIST"]'

    # discography
    cc.discography_filter = ''

    # fin
    session.add(cc)
    session.commit()


basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'db.sqlite')


if os.path.exists(db_path) == False:
    # Create DB File
    Base.metadata.create_all(engine)

    # set revision number
    from alembic.config import Config
    from alembic import command
    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
    command.stamp(alembic_cfg, 'head')

    create_default_config()

try:
    cc = session.query(ChimeraConfig).first()
    # updates
    # 21-10-2019
    if cc.folder_naming_scheme == None:
        cc.folder_naming_scheme = '["ARTIST", "ALBUM"]'
    # 10-10-2019
    if cc.cover_file_name == None:
        cc.cover_file_name = 'cover'
    if cc.spotify_default_service == None:
        cc.spotify_default_service = 'deezer'
    # 07-10-2019
    if cc.workers == None:
        cc.workers = 8
    if cc.concurrency == None:
        cc.concurrency = False
    # 06-10-2019
    if cc.qobuz_seed_type == None:
        cc.qobuz_seed_type = ''
    # 29-09-2019
    if cc.pad_track_width == None:
        cc.pad_track_width = '2'
    # 22-09-2019
    if cc.discography_filter == None:
        cc.discography_filter = ''
    if cc.playlist_naming_scheme == None:
        cc.playlist_naming_scheme = 'PLNR - TITLE - ARTIST'
    if cc.playlist_folder_naming_scheme == None:
        cc.playlist_folder_naming_scheme = '["PLAYLIST"]'
    session.commit()
except:
    print("Update your db scheme with 'python update.py'")
    sys.exit()
