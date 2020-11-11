import os
import platform
import sys
import time
from colorama import Fore

import chimera.discography
import chimera.label
import chimera.utils
from cli import chimera_cli, deezer_cli, tidal_cli
# from cli import chimera_cli
from cli.utils import check_auth, master_login
from db import cc
from main import ci


def print_help():
    print("""
Commands:
  To switch service, enter the desired service name, currently available are [deezer | tidal | qobuz | dtq | soundcloud | napster | gpm | spotify]
        dtq is to search albums or tracks over all three services at once
        Soundcloud currently supports (no login required):
            grab track [full track url from webpage]
            grab playlist [id | full playlist url from webpage]
            show playlists
        spotify: select which conversion service should be active by adding it after spotify:
            `spotify qobuz` => SPOTIFY (qobuz) ->
            `spotify deezer` => SPOTIFY (deezer) ->
            defaults to deezer

  setup [chimera | audio | api | reset-gpm]
        `setup chimera` Webpage opens to configure chimera (http://localhost:5000/configure)
        `setup audio` list of audio devices gets printed, used for audio fingerprinting
        `setup api` creates a new api token -> does not add it to your config!
        `reset-gpm` resets gpm device id

  config [export | import | default]
        `config default` sets default configuration
        change configuration with `setup chimera`

  login
        login into service with credentials from config
        Has to be executed to be able to download anything!

  grab [album | track | discography | playlist] id
        download complete album or track with id
        `grab album 9688352 false` downloads album
        discography download id is artist id
        `grab discography 5646`
        spotify only:
            grab playlist all => downloads all playlists
            grab track [id] any spotify track id will do => searches on active service

  smart cli: for some services (deezer, tidal, qobuz) there is a smart cli for tracks, albums and playlists
        Just enter the complete url and it will grab it, current active services does not matter
        >>> DEEZER -> https://www.deezer.com/track/737967312
        >>> DEEZER -> https://play.qobuz.com/album/x88yammbh9rta

  search [isrc id | track | adv]
        search for track with isrc number or trackname, artist
        `search isrc ATN261558101` searchs isrc number (deezer only)
        `search track` new input for track_name
        `search adv` advanced search with ratios, searches on all currently logged in services

  show [track | status | queue]
        shows informations about selected object
        `show status` only useful when concurrency is enabled, displays current progress of downloads
        `show queue` only useful when concurrency is enabled, displays how many tracks are in the queue

  track quality [id]
        downloads all avaiable quality profiles of a track, quality profile
        name will be prepended at the track name, downloads from lowest to highest quality

  csv
        download tracks from csv file, format: Title, Artist, Album, Release Date (opt), Duration_ms (opt), ISRC, spotify_id (opt)

  db [update]
        `db update` updates db (Takes a long time!)

  validate
        validates all downloaded tracks, which are added in the db.
        Checks if downloaded mp3 file is the correct length in seconds
        Creates txt file with wrong tracks, add `True` to delete while validating: `validate True`

  proxy
        checks proxy configuration in tidal session [proxy support for track download not implemented, only search]

  appid
        gets appid and secret for qobuz, add them to your config file first one is app_id

  help
        display this help-page

  exit
        close the app
    """)

def login():
    ci.cli.login(ci.service)

def login_all():
    master_login(deezer=ci.deezer, tidal=ci.tidal, qobuz=ci.qobuz,
                 napster=ci.napster, gpm=ci.gpm)

@check_auth
def grab_track(song_id):
    ci.cli.grab_track(song_id, ci.service)

@check_auth
def grab_album(album_id):
    ci.cli.grab_album(album_id, ci.service)

@check_auth
def grab_discography(artist_id):
    discography = chimera.discography.get_discography(artist_id, ci.service)
    discography.check()
    print('1) Download discography from {}\n2) Write a report of allowed tracks (import/cache/discographyXXX.csv)'.format(discography.artist))
    selection = input("Select ('q' to exit): ")
    if selection == 'q':
        return
    selection = int(selection)
    if selection == 1:
        discography.download(ci.service)
    if selection == 2:
        discography.write_report()

@check_auth
def grab_label(label_id):
    """only qobuz"""
    label = chimera.label.get_label(label_id, ci.qobuz)
    label.download(ci.qobuz, concurrency=cc.concurrency)

@check_auth
def grab_playlist(playlist_id):
    ci.cli.grab_playlist(playlist_id, ci.service)

@check_auth
def grab_saved():
    ci.cli.grab_saved(ci.service)

@check_auth
def grab_show(show_id):
    deezer_cli.grab_show(show_id, ci.deezer)

@check_auth
def grab_episode(episode_id):
    deezer_cli.grab_episode(episode_id, ci.deezer)

@check_auth
def grab_video(video_id):
    tidal_cli.grab_video(video_id, ci.tidal) # tidal only

@check_auth
def grab_videos_from_artist(artist_id):
    tidal_cli.grab_videos_from_artist(artist_id, ci.tidal)

@check_auth
def search_track():
    if ci.active == ci.a_dtq:
        ci.cli.search_track(ci.deezer, ci.tidal, ci.qobuz)
        return
    ci.cli.search_track(ci.service)

@check_auth
def search_album():
    if ci.active == ci.a_dtq:
        ci.cli.search_album(ci.deezer, ci.tidal, ci.qobuz)
        return
    ci.cli.search_album(ci.service)

@check_auth
def search_isrc(isrc):
    if ci.active == ci.a_deezer:
        deezer_cli.search_isrc(ci.deezer, isrc)

@check_auth
def search_video():
    tidal_cli.search_video(ci.tidal)

@check_auth
def show_track(id):
    if ci.active == ci.a_gpm:
        track = ci.service.get_track(id)
    else:
        track = ci.service.get_track(int(id))
    header = '{} from {}'.format(track.title, track.artist)
    print('\n' + header)
    print(len(header) * '-')
    print('Title    : {}'.format(track.title))
    print('Album    : {} ({})'.format(track.album.title, track.album.album_id))
    print('Track Nr : {}'.format(track.track_number))
    print('Artist   : {} ({})'.format(track.artist, track.artists[0].artist_id))
    print('Duration : {}'.format(track.duration))
    if track.service == 'qobuz':
        print('Qualities : {}'.format(track.quality_pretty))
    else:
        print('Qualities : {}'.format(track.qualities))

@check_auth
def show_playlists():
    if ci.active == ci.a_dtq:
        ci.cli.show_playlists(ci.deezer, ci.tidal, ci.qobuz)
        return
    ci.cli.show_playlists(ci.service)

@check_auth
def show_video(video_id):
    video = ci.tidal.get_video(video_id)
    video.get_qualities(ci.tidal)
    header = '{} from {}'.format(video.title, video.artist)
    print('\n' + header)
    print(len(header) * '-')
    print('Video            : {}'.format(video.title))
    print('Duration:        : {}'.format(video.duration))
    print('Qualities:       : {}'.format(', '.join([q.resolution for q in video.qualities])))

@check_auth
def test_track_quality(song_id):
    chimera_cli.test_track_quality(song_id, ci.service)

@check_auth
def read_csv():
    if ci.active == ci.a_deezer:
        deezer_cli.read_csv(ci.deezer)

@check_auth
def tag_mp3_with_search(file, deezer_id):
    track = ci.gpm.get_track(deezer_id)
    track.update_tags(ci.gpm)
    track.tag(file)

def sync():
    """for the sync argument"""
    import cli.spotify_cli
    import threading
    cli.spotify_cli.grab_all_playlists(ci.deezer)
    cli.spotify_cli.grab_saved(ci.deezer)

    print('Downloading...')
    # Wait until everything is downloaded
    while [x for x in threading.enumerate() if x.name == 'playlist_watchdog']:
        time.sleep(5)
    import chimera.download
    print('Downloaded {} new tracks.'.format(chimera.download.download_count))
    sys.exit()

def listen():
    """has auto login feature"""
    import chimera.audio
    chimera.audio.id_and_search()

def setup_audio():
    import chimera.audio
    chimera.audio.print_audio_devices()

def setup_chimera():
    """custom configuration"""
    from api import create_app
    import webbrowser
    import threading

    def start_flask():
        app = create_app(chimera_config=True)
        app.run(host='0.0.0.0', port=5000)

    print('open http://localhost:5000/configure to configure Chimera')
    app_t = threading.Thread(target=start_flask, daemon=True)
    app_t.start()
    webbrowser.open('http://localhost:5000/configure')

def setup_reset_gpm():
    """resets gpm device id"""
    cc.gpm_device_id = 'CHANGEME'
    cc.save()
    print('GPM device id reset\nRestart required!')

def chimera_search():
    chimera_cli.search(**ci.services_logged_in())

def test():
    album = ci.qobuz.get_album(3614598106890)
    for track in album.songs:
        print(track.path.full_folder)

def test2():
    track = ci.soundcloud.get_track_go_from_url('https://soundcloud.com/marlon-94072/madonna')
    track.download(ci.soundcloud, folder='D:/temp')
    pass

def test3():
    track = ci.deezer.get_track(15392959)
    track.guess_quality('FLAC')


    track2 = ci.deezer.get_track(59640451)
    track2.guess_quality('FLAC')

    track3 = ci.deezer.get_track(720599342)
    track3.guess_quality('FLAC')

def test4():
    pass


def write_active():
    if ci.active == ci.a_deezer:
        sys.stdout.write(Fore.GREEN + 'DEEZER ')
        sys.stdout.flush()
    elif ci.active == ci.a_tidal:
        sys.stdout.write(Fore.YELLOW + 'TIDAL ')
        sys.stdout.flush()
    elif ci.active == ci.a_qobuz:
        sys.stdout.write(Fore.MAGENTA + 'QOBUZ ')
        sys.stdout.flush()
    elif ci.active == ci.a_dtq:
        sys.stdout.write(Fore.GREEN + 'D' + Fore.YELLOW + 'T' + Fore.MAGENTA + 'Q ')
        sys.stdout.flush()
    elif ci.active == ci.a_soundcloud:
        sys.stdout.write(Fore.CYAN + 'SOUNDCLOUD ')
        sys.stdout.flush()
    elif ci.active == ci.a_napster:
        sys.stdout.write(Fore.LIGHTBLUE_EX + 'NAPSTER ')
        sys.stdout.flush()
    elif ci.active == ci.a_gpm:
        sys.stdout.write(Fore.LIGHTRED_EX + 'GPM ')
        sys.stdout.flush()
    elif ci.active == ci.a_spotify:
        sys.stdout.write(Fore.GREEN + 'SPOTIFY ')
        sys.stdout.write('({}) '.format(ci.spotify_conversion).lower())
        sys.stdout.flush()

def main(args, start):
    if cc.prod:
        opsystem = platform.system()
        if opsystem == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
    end = time.time()
    if cc.prod == False:
        print(f'STARTUP TOOK: {end - start}')
    print('''
  _____   __ __   ____   __  ___   ____   ___    ___
 / ___/  / // /  /  _/  /  |/  /  / __/  / _ \\  / _ |
/ /__   / _  /  _/ /   / /|_/ /  / _/   / , _/ / __ |
\\___/  /_//_/  /___/  /_/  /_/  /___/  /_/|_| /_/ |_|

        h for help page
        ''')


    # get services in list from config
    if cc.auto_login != '' and cc.auto_login != None and args.noautologin == False:
        aservices = ci.map_service(cc.auto_login, _format='dict', check_login=False)
        master_login(**aservices)

    if args.sync:
        sync()

    if args.url:
        chimera_cli.guess_cmd(args.url, ci.deezer, ci.tidal, ci.qobuz, ci.soundcloud, ci.napster, ci.spotify_conversion)
        # won't work in concurrent mode
        sys.exit()

    while True:
        write_active()
        command = input('-> ').split(' ')

        if command[0].startswith('http'):
            chimera_cli.guess_cmd(command[0], ci.deezer, ci.tidal, ci.qobuz, ci.soundcloud, ci.napster, ci.spotify_conversion)

        # handel service switching
        elif command[0] == 'tidal':
            ci.active = ci.a_tidal
        elif command[0] == 'deezer':
            ci.active = ci.a_deezer
        elif command[0] == 'qobuz':
            ci.active = ci.a_qobuz
        elif command[0] == 'dtq':
            ci.active = ci.a_dtq
        elif command[0] == 'soundcloud':
            ci.active = ci.a_soundcloud
        elif command[0] == 'napster':
            ci.active = ci.a_napster
        elif command[0] == 'gpm':
            ci.active = ci.a_gpm
        elif command[0] == 'login':
            login()
        elif command[0] == 'loginall':
            login_all()
        elif command[0] == 'grab':
            if len(command) <= 1:
                print("missing argument for 'grab'")
                continue
            if command[1] == 'album':
                grab_album(command[2])
            elif command[1] == 'track':
                grab_track(command[2])
            elif command[1] == 'data':
                print(ci.deezer.get_track_data_public(command[2]))
            elif command[1] == 'discography':
                grab_discography(command[2])
            elif command[1] == 'playlist':
                grab_playlist(command[2])
            elif command[1] == 'saved':
                grab_saved()
            elif command[1] == 'video':
                grab_video(command[2])
            elif command[1] == 'videos':
                grab_videos_from_artist(command[2])
            elif command[1] == 'show':
                grab_show(command[2])
            elif command[1] == 'episode':
                grab_episode(command[2])
            elif command[1] == 'label':
                grab_label(command[2])
        elif command[0] == 'search':
            if len(command) <= 1:
                print("missing argument for 'search'")
                continue
            if command[1] == 'isrc':
                search_isrc(command[2])
            elif command[1] == 'track':
                search_track()
            elif command[1] == 'album':
                search_album()
            elif command[1] == 'video':
                search_video()
            elif command[1] == 'adv':
                chimera_search()
        elif command[0] == 'show':
            if len(command) <= 1:
                print("missing argument for 'show'")
                continue
            if command[1] == 'track':
                show_track(command[2])
            elif command[1] == 'playlists':
                show_playlists()
            elif command[1] == 'video':
                show_video(command[2])
            elif command[1] == 'status':
                chimera_cli.show_status()
            elif command[1] == 'queue':
                chimera_cli.show_queue(ci)
        elif command[0] == 'csv':
            read_csv()
        elif command[0] == 'config':
            if len(command) <= 1:
                print("missing argument for 'config'")
                continue
            if command[1] == 'show':
                chimera_cli.config_show()
            elif command[1] == 'export':
                chimera_cli.config_export()
            elif command[1] == 'import':
                chimera_cli.config_import()
            elif command[1] == 'default':
                chimera_cli.set_default()
        elif command[0] == 'spotify':
            if len(command) == 1:
                ci.active = ci.a_spotify
            else:
                if command[1] == ci.a_deezer:
                    ci.spotify_conversion = ci.deezer
                    ci.active = ci.a_spotify
                elif command[1] == ci.a_tidal:
                    ci.spotify_conversion = ci.tidal
                    ci.active = ci.a_spotify
                elif command[1] == ci.a_qobuz:
                    ci.spotify_conversion = ci.qobuz
                    ci.active = ci.a_spotify
        elif command[0] == 'h':
            print_help()
        elif command[0] == 'tag':
            tag_mp3_with_search(r"D:\temp\Musik_notabug\Eminem\Rap God\Eminem - 1 - Rap God.m4a", 'Tswhyxgv4dkxo5ikcwrz7qrtmiy')
        elif command[0] == 'test':
            test()
        elif command[0] == 'test2':
            test2()
        elif command[0] == 'test3':
            test3()
        elif command[0] == 'test4':
            test4()
        elif command[0] == 'exit':
            break
        elif command[0] == 'db':
            if command[1] == 'update':
                chimera.utils.update_tracks_in_db(ci.deezer)
        elif command[0] == 'validate':
            if len(command) == 2:
                chimera.utils.validate_music_archive(delete=True)
            else:
                chimera.utils.validate_music_archive()

        elif command[0] == 'proxy':
            ci.tidal.proxy_test()
        elif command[0] == 'appid':
            ci.qobuz.get_appid_and_secret()
        elif command[0] == 'seed':
            print(ci.qobuz.get_type_seed())
        elif command[0] == 'listen':
            listen()
        elif command[0] == 'setup':
            if len(command) <= 1:
                print("missing argument for 'setup'")
                continue
            if command[1] == 'audio':
                setup_audio()
            elif command[1] == 'chimera':
                setup_chimera()
            elif command[1] == 'api':
                from db import create_api_token
                print('Add this token to your config: ' + create_api_token())
            elif command[1] == 'reset-gpm':
                setup_reset_gpm()
        elif command[0] == 'track':
            if len(command) <= 1:
                print("missing argument for 'track'")
                continue
            if command[1] == 'quality':
                if len(command) > 2:
                    test_track_quality(command[2])
        else:
            print('unknown command...')
