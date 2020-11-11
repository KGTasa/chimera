"""chimera_config_part_3

Revision ID: 7a9e937e36aa
Revises: 87d168a8b2b5
Create Date: 2019-08-28 08:42:33.876705

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a9e937e36aa'
down_revision = '87d168a8b2b5'
branch_labels = None
depends_on = None


def upgrade():
    # chimera
    op.add_column('chimeraconfigs', sa.Column('root_path', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('prod', sa.Boolean()))

    # spotify
    op.add_column('chimeraconfigs', sa.Column('spotify_default_service', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('spotify_blacklist', sa.Text()))
    op.add_column('chimeraconfigs', sa.Column('spotify_username', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('spotify_client_id', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('spotify_client_secret', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('spotify_redirect_uri', sa.String()))

    # deezer
    op.add_column('chimeraconfigs', sa.Column('deezer_username', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('deezer_email', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('deezer_password', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('deezer_quality', sa.String()))

    # tidal
    op.add_column('chimeraconfigs', sa.Column('tidal_email', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('tidal_password', sa.String()))

    # qobuz
    op.add_column('chimeraconfigs', sa.Column('qobuz_email', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('qobuz_password', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('qobuz_quality', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('qobuz_app_id', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('qobuz_secret', sa.String()))

    # soundcloud
    op.add_column('chimeraconfigs', sa.Column('soundcloud_username', sa.String()))

    # discogs
    op.add_column('chimeraconfigs', sa.Column('discogs_enabled', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('discogs_token', sa.String()))

    # audio fingerprinting
    op.add_column('chimeraconfigs', sa.Column('audio_acr_host', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('audio_acr_access_key', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('audio_access_secret', sa.String()))
    op.add_column('chimeraconfigs', sa.Column('audio_device_id', sa.Integer()))
    op.add_column('chimeraconfigs', sa.Column('audio_services', sa.String()))

    # download
    op.add_column('chimeraconfigs', sa.Column('dl_track_overwrite', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_track_add_to_db', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_track_check_db', sa.Boolean()))

    op.add_column('chimeraconfigs', sa.Column('dl_album_overwrite', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_album_add_to_db', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_album_check_db', sa.Boolean()))

    op.add_column('chimeraconfigs', sa.Column('dl_playlist_overwrite', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_playlist_add_to_db', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_playlist_check_db', sa.Boolean()))

    op.add_column('chimeraconfigs', sa.Column('dl_discography_overwrite', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_discography_add_to_db', sa.Boolean()))
    op.add_column('chimeraconfigs', sa.Column('dl_discography_check_db', sa.Boolean()))


def downgrade():
    pass
