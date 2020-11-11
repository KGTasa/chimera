# 1. standard
import difflib
import os

import chimera.csv
import chimera.db
from chimera.utils import DownloadResponse, pred, pyel, write_m3u_file
from config import log
from db import cc
# from db.db import session as db_session
from db.db import create_session
from db.models import DBTrack
from generic.utils import remove_illegal_characters, DownloadResult
from chimera.spotify import SpotifyTrack
from typing import List, Dict

download_count = 0


_status_codes = {
    000: 'everything ok',
    101: 'track downloaded in lower quality',
    102: 'track already in db',
    103: 'track already on disk',
    104: 'file name too long',
    201: 'track has not requested quality ABORTED',
    202: 'could not get stream url for selected quality ABORTED',
    203: 'TrackRestrictedByRightHolders ABORTED',
    204: 'Qobuz Invalid Secret',
    205: "Asset is not available in user's location ABORTED (Tidal)",
    206: 'HTTP Error',
    207: 'Asset is not ready for playback',
    208: 'NapsterNoTrackStream'
}

CODE_101 = 'Track downloaded in lower quality! (selected: {}, got: {})'
CODE_202 = 'Track has selected quality, but error getting stream url for it try a lower quality'
CODE_203 = 'TrackRestrictedByRightHolders'
CODE_204 = 'Invalid Qobuz Secret'
CODE_205 = "Asset is not available in user's location"
CODE_207 = 'Asset is not ready for playback'
CODE_208 = 'No stream found for track!'


def any_track(track, session, track_type=None, overwrite=True, add_to_db=False, task=None,
              check_db=False, lyrics=False, save_lyrics=False, dlthread=None) -> DownloadResponse:
    """
    download any track Object (Deezer, Tidal, Qobuz), supply with correct session
    Args:
        `track` track object
        `session` active session for respective track
        `overwrite=True` overwrite existing track
        `add_to_db=False` adds track to db for (only usefull for SpotifyTrackc sync)
        `task` if track is from DownloadThread
        `lyrics` gets lyrics informations from deezer
        `save_lyrics` saves synced lyrics as file with the same name next to the audio file
    Returns:
        DownloadResponse
    """
    # 1. pre check
    if track is None:
        if task:
            task.failed = True
            task.finished = True
        return DownloadResponse(True, 'Not a valid track')

    # 2. check if track is already existing in the db
    if check_db:
        # needs a new object! if no results => None
        _track = search_dbtrack(track)
        if type(_track) is DBTrack:
            if task:
                task.finished = True
            return DownloadResponse(False, 'Track already in db',
                                    file_name=os.path.join(cc.root_path, _track.path), status_code=102)

    # 3. check if file exists and if this file has title and artist tags, of not overwide overwrite feature
    if os.path.exists(track.path.full_path) and chimera.utils.check_tags(track.path.full_path) == False:
        overwrite = True

    # 4. check if overwite is set and if file exists
    if overwrite is False and os.path.exists(track.path.full_path):
        if cc.cli and dlthread is None:
            print(f'already downloaded {track.title} by {track.artist} ID: {track.song_id}')
        if add_to_db:
            chimera.db.add(track)
        if task:
            task.finished = True
        return DownloadResponse(False, 'Track already on disk',
                                file_name=track.path.full_path, status_code=103)

    # 5. print information => maybe create callback function for this
    if cc.cli and dlthread is None:
        print(f'grabbing {track.title} by {track.artist} ID: {track.song_id}')
    log.info('grabbing {} from {}'.format(track, session))

    # 6. update tags
    log.info('Updating Tags')
    if track.update_tags(session) == False:
        log.info('failed tags')
        if task:
            task.failed = True
            task.finished = True
        return DownloadResponse(True, 'failed to update tags')

    if lyrics or save_lyrics:
        track.get_lyrics(session)

    # 7. check if type is set
    if track_type == None:
        track_type = guess_track(track)

    # 8. download the track
    res: DownloadResult = None
    selected_quality = None
    if track_type == 'deezer':
        selected_quality = cc.deezer_quality
        res = track.download(quality=cc.deezer_quality, folder=track.path.full_folder,
                             to_file=track.path.file_name, task=task, lower_quality=cc.deezer_quality_fallback, dlthread=dlthread)
    elif track_type == 'tidal':
        # tidal needs session object for stream url
        selected_quality = cc.tidal_quality
        res = track.download(session, quality=cc.tidal_quality, folder=track.path.full_folder,
                             to_file=track.path.file_name, task=task, lower_quality=cc.tidal_quality_fallback, dlthread=dlthread)
    elif track_type == 'qobuz':
        selected_quality = cc.qobuz_quality
        res = track.download(session, quality=cc.qobuz_quality, folder=track.path.full_folder, to_file=track.path.file_name,
                             task=task, lower_quality=cc.qobuz_quality_fallback, dlthread=dlthread)
    elif track_type == 'napster':
        selected_quality = cc.napster_quality
        res = track.download(session, quality=cc.napster_quality, folder=track.path.full_folder, to_file=track.path.file_name,
                             task=task, lower_quality=cc.napster_quality_fallback, dlthread=dlthread)
    elif track_type == 'gpm':
        selected_quality = cc.gpm_quality
        res = track.download(session, quality=cc.gpm_quality, folder=track.path.full_folder,
                             to_file=track.path.file_name, task=task, dlthread=dlthread)

    # 9. error checking if download succesfull, res.file_name is the full path to the track
    dr_reason = 'successfully downloaded'
    _res = res._asdict()

    # 9.a) lower quality selected
    if res.status_code == 101:
        dr_reason = CODE_101.format(selected_quality, res.status_text)
    if res.status_code == 104:
        dr_reason = res.status_text


    if task:
        if 200 < res.status_code < 300:
            task.failed = True
            task.finished = True

    # 9.b) aborted
    if res.status_code == 201:
        return DownloadResponse(True, res.status_text, **_res)
    if res.status_code == 202:
        return DownloadResponse(True, CODE_202, **_res)
    if res.status_code == 203:
        return DownloadResponse(True, CODE_203, **_res)
    if res.status_code == 204:
        return DownloadResponse(True, CODE_204, **_res)
    if res.status_code == 205:
        return DownloadResponse(True, CODE_205, **_res)
    if res.status_code == 206:
        return DownloadResponse(True, res.status_text, **_res)
    if res.status_code == 207:
        return DownloadResponse(True, res.status_text, **_res)
    if res.status_code == 208:
        return DownloadResponse(True, CODE_208, **_res)

    # 9.c) check if valid file, sometimes there are 0 byte files
    if chimera.utils.get_file_length_seconds(res.file_name) == None:
        if os.path.exists(res.file_name):
            os.remove(res.file_name)
        # TODO add to ignore list and db
        if task:
            task.finished = True
            task.failed = True
        return DownloadResponse(True, 'not a valid audio file', **_res)

    # 10. tag track
    track.tag(res.file_name)

    #### POST PROCESSING TODO maybe own function for this if more features get added

    # 11. add to db
    if add_to_db:
        chimera.db.add(track)

    # 12. save synced lyric file
    if save_lyrics:
        track.save_lyrics(track.path.full_path_ext('.lrc'))

    # 13. save cover into album folder
    if cc.save_cover:
        track.save_cover()

    # 14. misc
    global download_count
    download_count = download_count + 1
    if cc.cli and dlthread is None:
        print(f'Download count: {download_count}')
    log.info('download count: {}'.format(download_count))
    if task:
        task.finished = True
    # 15. return True response
    return DownloadResponse(False, dr_reason, quality=selected_quality, **_res)


def search_dbtrack(track):
    db_session = create_session()
    return db_session.query(DBTrack).filter_by(remote_id=track.song_id).first()


def guess_track(track):
    return track.service


def sp_track(sptrack: SpotifyTrack, session, task=None, dlthread=None):
    """converst sp track to active session track
    deezer supports isrc lookup"""

    track = None

    # 1. check db
    db_session = create_session()
    track = db_session.query(DBTrack).filter_by(isrc=sptrack.isrc).first()
    if track:
        if os.path.isfile(os.path.join(cc.root_path, track.path)):
            if task:
                task.finished = True
            return DownloadResponse(False, 'Track already in db', file_name=os.path.join(cc.root_path, track.path), status_code=102)
        else:
            track = None # maybe different fix

    # 2. ISRC lookup
    if str(session) == 'DEEZER':
        track = session.search_isrc(sptrack.isrc)

    # 3. no isrc match, search on services
    if track is None:
        services = {str(session).lower(): session}
        track = search_track_on_services(sptrack.title, sptrack.artist, sptrack.album.title, **services,
                                         isrc=sptrack.isrc, verbose=False if dlthread else True)
        # if track found track is no longer false, check again
        if track is None:
            if task:
                task.finished = True
            return DownloadResponse(True, 'Track not found on services!')

    # 4.a) copy over playlist details
    track.is_playlist = sptrack.is_playlist
    track.playlist_name = sptrack.playlist_name
    track.playlist_index = sptrack.playlist_index
    track.playlist_length = sptrack.playlist_length

    # 4.b) deezer download
    if str(session) == 'DEEZER':
        ds = any_track(track, session, overwrite=cc.dl_playlist_overwrite,
                       add_to_db=cc.dl_playlist_add_to_db, check_db=cc.dl_playlist_check_db,
                       lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics,
                       task=task, dlthread=dlthread)
        return ds
    # 4.c) everything else
    else:
        ds = any_track(track, session, overwrite=cc.dl_playlist_overwrite,
                       add_to_db=cc.dl_playlist_add_to_db, check_db=cc.dl_playlist_check_db,
                       task=task, dlthread=dlthread)
        return ds
    # 5. TODO fallback search

def any_playlist(playlist, session, m3u=True, m3u_path=None, log_missing=True,
                 ignore_tracks=False, m3u_tracks=None, missing_tracks=None, verbose=True):
    """download playlist object
    Args:
        `ignore_tracks` do not download tracks only execute playlist logic
        `m3u_tracks` all tracks will be writting in the m3u file
        `missing_tracks` missing file
        Those arguments are only needed for concurrency
    """

    import_path = 'import'
    sub_dir = 'playlists'
    csv_missing = os.path.join(import_path, sub_dir, '{}_missing.csv'.format(
        remove_illegal_characters(playlist.name)))
    if m3u_path == None:
        m3u_path = os.path.join(import_path, sub_dir, remove_illegal_characters(playlist.name) + '.m3u')
    if m3u_tracks == None:
        m3u_tracks = []
    if missing_tracks == None:
        missing_tracks = []

    if not ignore_tracks:
        for track in playlist.songs:
            ds = None
            if track.service == 'deezer':
                # deezer lyrics support
                ds = any_track(track, session, overwrite=cc.dl_playlist_overwrite,
                               add_to_db=cc.dl_playlist_add_to_db, check_db=cc.dl_playlist_check_db,
                               lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics)
            elif track.service == 'spotify':
                ds = sp_track(track, session)
            else:
                ds = any_track(track, session, overwrite=cc.dl_playlist_overwrite,
                               add_to_db=cc.dl_playlist_add_to_db, check_db=cc.dl_playlist_check_db)
            if ds.failed:
                missing_tracks.append(track)
                if cc.cli:
                    pred(ds.reason)
            else:
                m3u_tracks.append(ds.file_name + '\n')
                if ds.status_code != 0:
                    if cc.cli:
                        pyel(ds.reason)
    if m3u:
        write_m3u_file(m3u_path, m3u_tracks, verbose=verbose)
    if log_missing and len(missing_tracks) > 0:
        chimera.csv.write_csv(csv_missing, missing_tracks)
    # for spotify global logs
    return missing_tracks


def search_track_on_services(title, artist, album, deezer=None, tidal=None, qobuz=None, napster=None,
                             gpm=None, conversion_test=False, isrc=None, verbose=True):
    """
    Searches on active services for title artist album
    returns track object if match is greater than 90%
    `q` Search String (short for query)
    """
    if verbose:
        print(f'Searching: {title} {album} {artist}')
    blacklist = ['Version', 'Deluxe']
    q_all = ' '.join([title, artist, album])
    q = ' '.join([title, artist])
    for x in blacklist:
        q = q.replace(x, '')

    # print(q)

    # get active services
    services = [s for s in [deezer, tidal, qobuz, napster, gpm] if s]

    # limit for each service
    limit = 5
    q_tracks = []
    for service in services:
        q_tracks += service.search_track(q, limit=limit)

    #  'id', 'title','artist','album'
    if verbose:
        print(f'Tracks found: {len(q_tracks)}')
    if conversion_test:
        return MatchTracks(q_all, q, q_tracks, isrc=isrc).best()
    match = MatchTracks(q_all, q, q_tracks, isrc=isrc).best()
    if match:
        track = match['track']
        if verbose:
            print('Found: {}, {}, {} from {} with match: {}'.format(
                track['title'], track['album'], track['artist'], track['type'], match['ratio']))
        if track['type'] == 'deezer':
            return deezer.get_track(track['id'])
        elif track['type'] == 'tidal':
            return tidal.get_track(track['id'])
        elif track['type'] == 'qobuz':
            return qobuz.get_track(track['id'])
        elif track['type'] == 'napster':
            return napster.grab_track(track['id'], napster)
        elif track['type'] == 'gpm':
            return gpm.grab_track(track['id'], gpm)

    # no match found
    return None



class MatchTracks:
    def __init__(self, q_all, q, q_tracks, isrc=None):
        """Looks through all tracks in q_tracks and returns best
        Args:
            `q_all` string TITLE ARTIST ALBUM
            `q` string TITLE ARTIST
            `q_tracks` list of tracks dict from search
                dict keys: title, artist, album, isrc
            `isrc` isrc code
        Returns:
            match object with track key or None
            3 = isrc match
            2 = perfect album match
            1 = perfect track match
        """
        results = {'q_all': [], 'q': [], 'isrc': []}
        for track in q_tracks:
            # 1. ISRC best match: 3.0
            if isrc:
                results['isrc'].append({'track': track, 'ratio': 3 if track['isrc'].lower() == isrc.lower() else 0,
                                        'match_type': 'isrc'})

            # 2. Title, Artist, Ablum: 2.0
            q_all_string = ' '.join([track['title'], track['artist'], track['album']])
            ratio_q_all = difflib.SequenceMatcher(None, q_all, q_all_string).ratio()
            results['q_all'].append({'track': track, 'ratio': ratio_q_all * 2, 'match_type': 'q_all'})

            # 3- Title Artist: 1.0
            q_string = ' '.join([track['title'], track['artist']])
            ratio_q = difflib.SequenceMatcher(None, q, q_string).ratio()
            results['q'].append({'track': track, 'ratio': ratio_q, 'match_type': 'q'})
        self.ratios = results
        self.matches: List[Dict] = MatchTracks.filter_ratios(results)

    @staticmethod
    def filter_ratios(ratios, r_isrc=3.0, r_q=0.9, r_q_all=1.2):
        """filters results based on ratios"""
        try:
            isrc_max = list(filter(lambda y: y['ratio'] == r_isrc, ratios['isrc']))
        except ValueError as e:
            isrc_max = []

        # get max ratio from q tracks (TITLE + ARTIST)
        try:
            q_max = list(filter(lambda y: y['ratio'] >= r_q, ratios['q']))
        except ValueError as e:
            q_max = [] # when q is empty

        # get max ratio from q_all tracks (TITLE + ARTIST + ALBUM)
        try:
            q_all_max = list(filter(lambda y: y['ratio'] >= r_q_all, ratios['q_all']))
        except ValueError as e:
            q_all_max = []
        return sorted([*isrc_max, *q_max, *q_all_max], key=lambda x: x['ratio'], reverse=True)

    def best(self):
        try:
            # matches should be ordered
            return self.matches[0]
        except IndexError as e:
            return None
