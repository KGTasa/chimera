import chimera.dtq

from cli.utils import ptable


def search_track(deezer=None, tidal=None, qobuz=None, napster=None, gpm=None, limit=5, q=None, dtq_tracks=None):
    from cli import deezer_cli, qobuz_cli, tidal_cli, napster_cli, gpm_cli
    """Use for displaying and selection results
    Limit is for each service so result is x3"""

    if dtq_tracks == None:
        if q == None:
            q = input('Chimera search track: ')
        # get active services
        services = [s for s in [deezer, tidal, qobuz, napster, gpm] if s]

        # limit for each service
        limit = 5
        dtq_tracks = []
        for service in services:
            dtq_tracks += service.search_track(q, limit=limit)
        # dtq_tracks = chimera.dtq.dtq_search_track(q, deezer, tidal, qobuz, limit=limit)
    ptable(dtq_tracks, blacklist=['album_id', 'isrc', 'cover'], truncated=False)
    selection = input("Select ('q' to exit): ")
    if selection == 'q':
        return
    try:
        selection = int(selection)
    except ValueError as e:
        return
    if not selection > len(dtq_tracks):
        dtq_track = dtq_tracks[selection]
        if dtq_track['type'] == 'deezer':
            deezer_cli.grab_track(dtq_track['id'], deezer)
        elif dtq_track['type'] == 'tidal':
            tidal_cli.grab_track(dtq_track['id'], tidal)
        elif dtq_track['type'] == 'qobuz':
            qobuz_cli.grab_track(dtq_track['id'], qobuz)
        elif dtq_track['type'] == 'napster':
            napster_cli.grab_track(dtq_track['id'], napster)
        elif dtq_track['type'] == 'gpm':
            gpm_cli.grab_track(dtq_track['id'], gpm)


def search_album(deezer=None, tidal=None, qobuz=None, napster=None, gpm=None, limit=5, q=None, dtq_albums=None):
    from cli import deezer_cli, qobuz_cli, tidal_cli, napster_cli, gpm_cli
    """Use for displaying and selection results
    Limit is for each service so result is x3"""

    if dtq_albums == None:
        if q == None:
            q = input('DTQ Search album: ')
        dtq_albums = chimera.dtq.dtq_search_album(q, deezer, tidal, qobuz)
    ptable(dtq_albums)
    selection = input("Select ('q' to exit): ")
    if selection == 'q':
        return
    try:
        selection = int(selection)
    except ValueError as e:
        return
    if not selection > len(dtq_albums):
        dtq_album = dtq_albums[selection]
        if dtq_album['type'] == 'deezer':
            deezer_cli.grab_album(dtq_album['id'], deezer)
        elif dtq_album['type'] == 'tidal':
            tidal_cli.grab_album(dtq_album['id'], tidal)
        elif dtq_album['type'] == 'qobuz':
            qobuz_cli.grab_album(dtq_album['id'], qobuz)
        elif dtq_album['type'] == 'napster':
            napster_cli.grab_album(dtq_album['id'], napster)
        elif dtq_album['type'] == 'gpm':
            gpm_cli.grab_album(dtq_album['id'], gpm)

def show_playlists(deezer, tidal, qobuz):
    playlists = chimera.dtq.dtq_get_user_playlists(deezer, tidal, qobuz)
    ptable(playlists, blacklist=['image', 'description'])
