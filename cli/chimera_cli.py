import json
import os
import re
from db import cc
from db.db import session
from db.models import ChimeraConfig
from cli.utils import check_auth, ptable, master_login
from chimera.dtq import adv_search



import_path = 'import'
sub_dir = 'config'
config_path = os.path.join(import_path, sub_dir, 'chimera_config.json')


def check_dir():
    if os.path.exists(os.path.join(import_path, sub_dir)) is False:
        os.makedirs(os.path.join(import_path, sub_dir))

def config_show():
    # cc = session.query(ChimeraConfig).first()
    print('Chimera Config\n--------------')
    print('Naming Scheme    : {}'.format(cc.naming_scheme))
    print('Tag Title        : {}'.format(cc.tag_title))
    print('Tag Artist       : {}'.format(cc.tag_artist))
    print('Tag Date         : {}'.format(cc.tag_date))
    print('Tag Year         : {}'.format(cc.tag_year))
    print('Tag Cover        : {}'.format(cc.tag_cover))
    print('Tag Album        : {}'.format(cc.tag_album))
    print('Tag Tracknumber  : {}'.format(cc.tag_tracknumber))
    print('Tag Discnumber   : {}'.format(cc.tag_discnumber))
    print('Tag Genre        : {}'.format(cc.tag_genre))
    print('Tag Albumartist  : {}'.format(cc.tag_albumartist))
    print('Tag bpm          : {}'.format(cc.tag_bpm))
    print('Tag Length       : {}'.format(cc.tag_length))
    print('Tag Organization : {}'.format(cc.tag_organization))
    print('Tag isrc         : {}'.format(cc.tag_isrc))
    print('Tag gain         : {}'.format(cc.tag_gain))


def config_export():
    check_dir()
    cc = session.query(ChimeraConfig).first()
    with open(config_path, 'w') as f:
        json.dump(cc.as_dict(), f, indent=2)
        print('Config exported to: {}'.format(config_path))

def config_import():
    with open(config_path, 'r') as f:
        cc_json = json.load(f)
    cc = ChimeraConfig()
    for key, value in cc_json.items():
        setattr(cc, key, value)
    session.query(ChimeraConfig).delete()
    session.add(cc)
    session.commit()
    print('Config imported, restart chimera!')

def set_default():
    from db import create_default_config
    create_default_config()
    print('Default config applied, restart chimera!')



def show_status():
    from api.models import store
    for ttype in store.keys():
        for id, task in list(store[ttype].items()):
            if ttype == 'track' and task.ttype == 'track':
                print(f'{ttype}: {task.show_status()}')
            if ttype in ['album', 'playlist', 'discography']:
                print(f'{ttype}: {task.show_status()}')

def show_queue(ci):
    print(f'Queue: {ci.queue.qsize()}')
    # just some fancy two lines
    lines = {0: '', 1: ''}
    for i, worker in enumerate(ci.download_workers):
        if i % 2:
            lines[1] += str(worker) + '\t'
        else:
            lines[0] += str(worker) + '\t'
    for _, v in lines.items():
        print(v)

def test_track_quality(song_id, session):
    """download all qualities of a track with
    quality prepended at the name
    """
    from deezer.track_quality import DeezerTrackQuality
    from tidal.track_quality import TidalTrackQuality
    from qobuz.track_quality import QobuzTrackQuality
    from napster.track_quality import NapsterTrackQuality
    # no need for gpmTrackQuality it's always mp3

    if str(session) == 'GPM':
        track = session.get_track(song_id) # not an int
    else:
        track = session.get_track(int(song_id))
    if track.service == 'qobuz':
        for i, quality in enumerate(track.qualities):
            file_format = QobuzTrackQuality.get_file_format(quality)
            scheme = f'{track.qualities[i]} ARTIST - TRACK - TITLE'
            print('{}\t{}'.format(track.qualities[i], track))
            track.update_tags(session)
            res = track.download(
                session,
                quality=quality,
                folder=track.path.full_folder,
                to_file=track.generate_file_name(file_format, scheme=scheme)
            )
            track.tag(res.file_name)
    if track.service == 'tidal':
        for quality in track.qualities:
            file_format = TidalTrackQuality.get_file_format(quality)
            scheme = f'{quality} ARTIST - TRACK - TITLE'
            print('{}\t{}'.format(quality, track))
            track.update_tags(session)
            res = track.download(
                session,
                quality=quality,
                folder=track.path.full_folder,
                to_file=track.generate_file_name(file_format, scheme=scheme)
            )
            track.tag(res.file_name)
    if track.service == 'deezer':
        for quality in track.qualities:
            file_format = DeezerTrackQuality.get_file_format(quality)
            scheme = f'{quality} ARTIST - TRACK - TITLE'
            print('{}\t{}'.format(quality, track))
            track.update_tags(session)
            res = track.download(
                quality=quality,
                folder=track.path.full_folder,
                to_file=track.generate_file_name(file_format, scheme=scheme)
            )
            track.tag(res.file_name)
    if track.service == 'napster':
        for quality in track.qualities:
            file_format = NapsterTrackQuality.get_file_format(quality)
            scheme = f'{quality} ARTIST - TRACK - TITLE'
            print('{}\t{}'.format(quality, track))
            track.update_tags(session)
            res = track.download(
                session,
                quality=quality,
                folder=track.path.full_folder,
                to_file=track.generate_file_name(file_format, scheme=scheme)
            )
            track.tag(res.file_name)
    if track.service == 'gpm':
        for quality in track.qualities:
            file_format = '.mp3'
            scheme = f'{quality} ARTIST - TRACK - TITLE'
            print('{}\t{}'.format(quality, track))
            track.update_tags(session)
            res = track.download(
                session,
                quality=quality,
                folder=track.path.full_folder,
                to_file=track.generate_file_name(file_format, scheme=scheme)
            )
            track.tag(res.file_name)

@check_auth
def guess_cmd(url, deezer, tidal, qobuz, soundcloud, napster, spotify):
    import cli.deezer_cli
    import cli.tidal_cli
    import cli.qobuz_cli
    import cli.soundcloud_cli
    import cli.napster_cli
    import cli.spotify_cli

    RE_DE_ALBUM = r'deezer\..*/\w{2,}/album/(?P<id>\d{1,})'
    RE_DE_TRACK = r'deezer\..*/track/(?P<id>\d{1,})'
    RE_DE_PLAYLIST = r'deezer\..*\w{2,}/playlist/(?P<id>\d{1,})'

    RE_QO_ALBUM = r'(play|open).qobuz\..*/album/(?P<id>\w{1,})'
    RE_QO_TRACK = r'(play|open).qobuz\..*/track/(?P<id>\d{1,})'
    RE_QO_PLAYLIST = r'(play|open).qobuz\..*/playlist/(?P<id>\d{1,})'

    RE_TI_ALBUM = r'listen.tidal\..*/album/(?P<id>\d{1,})'
    RE_TI_TRACK = r'tidal\..*/browse/track/(?P<id>\d{1,})'
    RE_TI_PLAYLIST = r'(listen.)?tidal\..*/playlist/(?P<id>[a-z0-9-]{1,})'

    RE_SP_TRACK = r'open.spotify.com/track/(?P<id>\w{1,})?'

    smart_cli = {
        'deezer_album': [RE_DE_ALBUM, cli.deezer_cli.grab_album, deezer],
        'deezer_track': [RE_DE_TRACK, cli.deezer_cli.grab_track, deezer],
        'deezer_playlist': [RE_DE_PLAYLIST, cli.deezer_cli.grab_playlist, deezer],
        'qobuz_album': [RE_QO_ALBUM, cli.qobuz_cli.grab_album, qobuz],
        'qobuz_track': [RE_QO_TRACK, cli.qobuz_cli.grab_track, qobuz],
        'qobuz_playlist': [RE_QO_PLAYLIST, cli.qobuz_cli.grab_playlist, qobuz],
        'tidal_album': [RE_TI_ALBUM, cli.tidal_cli.grab_album, tidal],
        'tidal_track': [RE_TI_TRACK, cli.tidal_cli.grab_track, tidal],
        'tidal_playlist': [RE_TI_PLAYLIST, cli.tidal_cli.grab_playlist, tidal],
        'spotify_track': [RE_SP_TRACK, cli.spotify_cli.grab_track, spotify]
    }

    # maybe add regex for napster
    if 'napster' in url:
        # check track first => napster.com/artist/name/album/name/track/name
        if 'track' in url:
            _login_napster(napster)
            cli.napster_cli.grab_track_from_url(url, napster)
        elif 'album' in url:
            _login_napster(napster)
            cli.napster_cli.grab_album_from_url(url, napster)

    for name, group in smart_cli.items():
        reg, func, session = group
        re_search = re.search(reg, url)

        if re_search:
            re_search = re_search.groupdict()
            if not session.logged_in:
                master_login(**{str(session).lower(): session})
            func(re_search['id'], session)

def _login_napster(napster):
    if not napster.logged_in:
        master_login(napster=napster)
        # cli.napster_cli.login(napster)


# def search(deezer=None, tidal=None, qobuz=None, napster=None, gpm=None):
def search(**kwargs):
    """advanced search with ratio filtering
    args:
        deezer=deezer, etc -> chimera.dtq.adv_search"""
    # artist = 'Eminem'
    # title = 'Berzerk'
    # album = 'The Marshall Mathers LP2 (Deluxe)'
    # isrc = ''
    print('Advanced Search')
    title = input('Title: ')
    artist = input('Artist: ')
    album = input('Album: ')
    isrc = ''

    tracks = adv_search(**kwargs, title=title, artist=artist, album=album, isrc=isrc)

    ptable(tracks)
