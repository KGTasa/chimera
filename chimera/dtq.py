"""file of shared functions for deezer, tidal, qobuz"""
from chimera.download import MatchTracks

def adv_search(deezer=None, tidal=None, qobuz=None, napster=None, gpm=None,
               spotify=None, title='', artist='', album='', isrc=''):
    """spotify argument is dummy because ci.services"""

    q_all = ' '.join([title, artist, album])
    q = ' '.join([title, artist])

    services = [s for s in [deezer, tidal, qobuz, napster, gpm] if s]

    limit = 5
    q_tracks = []
    for service in services:
        q_tracks += service.search_track(q, limit=limit)

    matches = MatchTracks(q_all, q, q_tracks, isrc=isrc)
    readable = []
    for t in matches.matches:
        raw = {**t['track'], 'ratio': t['ratio']}
        t = raw.pop('type')
        raw['type'] = t
        readable.append(raw)
    return readable