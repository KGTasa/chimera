from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, SelectField, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.widgets import PasswordInput

class ChimeraConfigForm(FlaskForm):

    # chimera
    root_path = StringField('Root Path for Music')
    prod = BooleanField('Prod (less debug information, default=ON)', render_kw={'class': 'custom-control-input'})
    save_lyrics = BooleanField('Save synced .lrc file next to the audio file (deezer only)', render_kw={'class': 'custom-control-input'})
    m3u = BooleanField('Create m3u file for playlists', render_kw={'class': 'custom-control-input'})
    path_with_service = BooleanField('Add service root folder under "music root"', render_kw={'class': 'custom-control-input'})
    auto_login = StringField('Auto-Login Services', render_kw={'placeholder': 'deezer, tidal, qobuz'})
    merge_disks = BooleanField('Merges multiple disks into one (example: Disk 1; 13 Tracks, Track Nr 2 on Disk 2 would be Track Nr 15) (Deezer, Tidal and Qobuz)', render_kw={'class': 'custom-control-input'})
    force_merge_albums = BooleanField('Force merge main album artist. (See https://notabug.org/Aesir/chimera/issues/44)', render_kw={'class': 'custom-control-input'})
    pad_track = BooleanField('Pad Tracks with leading zeros', render_kw={'class': 'custom-control-input'})
    pad_track_width = StringField('Padding width (default 2)')
    concurrency = BooleanField("Concurrency, background download with multiple workers (use 'show status' and 'show queue' for progress updates)",
                               render_kw={'class': 'custom-control-input'})
    workers = IntegerField('How many workers to use for concurrency (default 8)')
    save_cover = BooleanField('Save album cover in album folder', render_kw={'class': 'custom-control-input'})
    cover_file_name = StringField('Filename for cover (without extension!)')
    api_token = StringField('API Token for Chimera')


    # spotify
    services = [('deezer', 'DEEZER'), ('tidal', 'TIDAL'), ('qobuz', 'QOBUZ')]
    spotify_default_service = SelectField('Service which Spotify Tracks should be downloaded from', choices=services, default=(services[0]))
    spotify_blacklist = StringField("Blacklisted Playlist ID's (comma separated)")
    spotify_username = StringField('Username')
    spotify_client_id = StringField('Client ID')
    spotify_client_secret = StringField('Client Secret')
    spotify_redirect_uri = StringField('Redirect URI', default='http://127.0.0.1:5000/callback', render_kw={'readonly': True})


    # deezer
    deezer_username = StringField('Username')
    deezer_email = EmailField('E-Mail Address')
    deezer_password = StringField('Password', widget=PasswordInput(hide_value=False))
    deezer_qualities = [('FLAC', 'FLAC'), ('MP3_320', 'MP3_320'), ('MP3_128', 'MP3_128'), ('360_RA3', '360_RA3'), ('360_RA2', '360_RA2'), ('360_RA1', '360_RA1')]
    deezer_quality = SelectField('Quality', choices=deezer_qualities)
    deezer_cover_sizes = [('2000x2000', '2000x2000'), ('1400x1400', '1400x1400'), ('1200x1200', '1200x1200'), ('1000x1000', '1000x1000'),
                          ('800x800', '800x800'), ('500x500', '500x500'), ('250x250', '250x250')]
    deezer_cover_size = SelectField('Cover Size (fallback to 1200x1200 if requested is not available)', choices=deezer_cover_sizes)
    deezer_quality_fallback = BooleanField('Fallback to lower quality', render_kw={'class': 'custom-control-input'})
    deezer_inline_decrypt = BooleanField('Inline decrypt', render_kw={'class': 'custom-control-input'})

    # tidal
    tidal_email = EmailField('E-Mail Address')
    tidal_password = StringField('Password', widget=PasswordInput(hide_value=False))
    tidal_qualities = [('HI_RES', 'HI_RES (FLAC)'), ('LOSSLESS', 'LOSSLESS (FLAC)'), ('HIGH', 'HIGH (m4a 320kbps)'), ('LOW', 'LOW (m4a 96kbps)')]
    tidal_quality = SelectField('Quality', choices=tidal_qualities)
    tidal_cover_sizes = [('1280x1280', '1280x1280'), ('640x640', '640x640'), ('320x320', '320x320'), ('160x160', '160x160')]
    tidal_cover_size = SelectField('Cover Size', choices=tidal_cover_sizes)
    tidal_quality_fallback = BooleanField('Fallback to lower quality', render_kw={'class': 'custom-control-input'})
    tidal_video_path = StringField('Video Path')
    tidal_video_pp = BooleanField('Postprocessing with ffmpeg (ffpmeg has to be installed an accessible in the PATH variable)', render_kw={'class': 'custom-control-input'})

    # qobuz
    qobuz_email = EmailField('E-Mail Address')
    qobuz_password = StringField('Password (MD5 Hash)', widget=PasswordInput(hide_value=False))
    qobuz_qualities = [('24-bit 96kHz', '24-bit >96kHz & =< 192kHz'), ('24-bit 44.1kHz', '24-bit 44.1kHz'),
                       ('16-bit 44.1kHz', '16-bit 44.1kHz'), ('MP3_320', 'MP3_320')]
    qobuz_quality = SelectField('Quality', choices=qobuz_qualities, default=qobuz_qualities[0])
    qobuz_app_id = StringField('App ID')
    qobuz_secret = StringField('Secret')
    # seed or secret
    qobuz_seed_types = [('dublin', 'Dublin'), ('london', 'London'), ('paris', 'Paris'), ('berlin', 'Berlin')]
    qobuz_seed_type = SelectField("Seed Timezone (select a different one if it doesn't work)", choices=qobuz_seed_types)
    qobuz_cover_sizes = [('max', 'max (up to 1400x1400)'), ('large', 'large (600x600)'), ('small', 'small (230x230)')]
    qobuz_cover_size = SelectField('Cover Size', choices=qobuz_cover_sizes)
    qobuz_quality_fallback = BooleanField('Fallback to lower quality', render_kw={'class': 'custom-control-input'})

    # napster
    napster_email = EmailField('E-Mail Address')
    napster_password = StringField('Password', widget=PasswordInput(hide_value=False))
    napster_api_token = StringField('API Token')
    napster_qualities = [('AAC_320', 'M4A_320'), ('AAC_192', 'M4A_192'), ('AAC_64', 'M4A_64')]
    napster_quality = SelectField('Quality', choices=napster_qualities, default=napster_qualities[0])
    napster_cover_sizes = [('MAX', 'MAX')]
    napster_cover_size = SelectField('Cover Size', choices=napster_cover_sizes)
    napster_quality_fallback = BooleanField('Fallback to lower quality', render_kw={'class': 'custom-control-input'})

    # gpm
    gpm_enabled = BooleanField('GPM Enabled', render_kw={'class': 'custom-control-input'})
    gpm_email = EmailField('E-Mail Address')
    gpm_password = StringField('Password', widget=PasswordInput(hide_value=False))
    gpm_qualities = [('hi', 'hi (MP3_320)'), ('med', 'med (MP3_160)'), ('low', 'low (MP3_128)')]
    gpm_quality = SelectField('Quality', choices=gpm_qualities, default=gpm_qualities[0])
    gpm_device_id = StringField('Device ID', render_kw={'readonly': True})


    #soundcloud
    soundcloud_username = StringField('Username')

    #discogs
    discogs_enabled = BooleanField('Enabled', render_kw={'class': 'custom-control-input'})
    discogs_token = StringField('Token')



    # audio fingerprinting
    audio_acr_host = StringField('Host')
    audio_acr_access_key = StringField('Access Key')
    audio_access_secret = StringField('Access Secret')
    audio_device_id = IntegerField('Device ID (use `setup audio` to get a list of your devices)')
    audio_services = StringField('Services (servicename comma separated)', render_kw={'placeholder': 'deezer, tidal, qobuz'})

    # Download
    dl_track_overwrite = BooleanField('Overwrite', render_kw={'class': 'custom-control-input'})
    dl_track_add_to_db = BooleanField('Add to db', render_kw={'class': 'custom-control-input'})
    dl_track_check_db = BooleanField('Check db', render_kw={'class': 'custom-control-input'})

    dl_album_overwrite = BooleanField('Overwrite', render_kw={'class': 'custom-control-input'})
    dl_album_add_to_db = BooleanField('Add to db', render_kw={'class': 'custom-control-input'})
    dl_album_check_db = BooleanField('Check db', render_kw={'class': 'custom-control-input'})

    dl_playlist_overwrite = BooleanField('Overwrite', render_kw={'class': 'custom-control-input'})
    dl_playlist_add_to_db = BooleanField('Add to db', render_kw={'class': 'custom-control-input'})
    dl_playlist_check_db = BooleanField('Check db', render_kw={'class': 'custom-control-input'})

    dl_discography_overwrite = BooleanField('Overwrite', render_kw={'class': 'custom-control-input'})
    dl_discography_add_to_db = BooleanField('Add to db', render_kw={'class': 'custom-control-input'})
    dl_discography_check_db = BooleanField('Check db', render_kw={'class': 'custom-control-input'})

    # track
    naming_scheme = StringField('Naming Scheme')
    folder_naming_scheme = StringField('Folder Naming Scheme (in JSON Array format)')

    # discography
    discography_filter = StringField('Regex Filter')

    # playlist
    save_as_compilation = BooleanField('Save Playlist as compilation', render_kw={'class': 'custom-control-input'})
    playlist_naming_scheme = StringField('Track Naming Scheme', render_kw={'placeholder': ''})
    playlist_folder_naming_scheme = StringField('Folder Naming Scheme (in JSON Array format)', render_kw={'placeholder': '["PLAYLIST"]'})

    # Tags
    tag_title = BooleanField('Title (TITLE)', render_kw={'class': 'custom-control-input'})
    tag_artist = BooleanField('Artist (ARTIST)', render_kw={'class': 'custom-control-input'})
    tag_date = BooleanField('Date (DATE)', render_kw={'class': 'custom-control-input'})
    tag_year = BooleanField('Year (YEAR)', render_kw={'class': 'custom-control-input'})
    tag_cover = BooleanField('Embedd Album Cover', render_kw={'class': 'custom-control-input'})
    tag_album = BooleanField('Album (ALBUM)', render_kw={'class': 'custom-control-input'})
    tag_tracknumber = BooleanField('Tracknumber (TRACK)', render_kw={'class': 'custom-control-input'})
    tag_discnumber = BooleanField('Discnumber (DISCNUMBER)', render_kw={'class': 'custom-control-input'})
    tag_genre = BooleanField('Genre', render_kw={'class': 'custom-control-input'})
    tag_albumartist = BooleanField('Album Artist', render_kw={'class': 'custom-control-input'})
    tag_bpm = BooleanField('BPM', render_kw={'class': 'custom-control-input'})
    tag_length = BooleanField('Length (in seconds)', render_kw={'class': 'custom-control-input'})
    tag_organization = BooleanField('Label', render_kw={'class': 'custom-control-input'})
    tag_isrc = BooleanField('ISRC', render_kw={'class': 'custom-control-input'})
    tag_gain = BooleanField('Replay Gain', render_kw={'class': 'custom-control-input'})
    tag_lyrics = BooleanField('Unsynced Lyrics (deezer only)', render_kw={'class': 'custom-control-input'})
    tag_comment = BooleanField('Custom Comment', render_kw={'class': 'custom-control-input'})
    tag_comment_value = StringField(render_kw={'style': 'display:inline;'})

    # Button
    submit = SubmitField('Save')
