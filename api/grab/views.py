from flask import jsonify, request

import api.grab.utils
import chimera.concurrency
from api import API_URL, parseargs
from api.grab import grab_bp
from api.models import DownloadThread
from api.status import tokenrequired
from main import ci
from tidal.utils import ARTIST_IMG_URL


#################################### TRACK ####################################
# @grab_bp.route(API_URL.format('grab/track'), methods=['OPTIONS'])
# def track_preflight():
#     return jsonify('')
@grab_bp.route(API_URL.format('grab/track'), methods=['POST'])
@tokenrequired
def track():
    if request.is_json:
        data = request.get_json()
        track_id = data.get('id', None)
        service = data.get('service', None)
    else:
        track_id = request.form.get('id', None)
        service = request.form.get('service', None)
    if not track_id or not service:
        return jsonify(error='Missing argument', args={'id': track_id, 'service': service}), 400

    track = ci.services[service].get_track(track_id)
    task = chimera.concurrency.blackhole(track, 'track')
    if task.track:
        return jsonify(DownloadThread.to_json_track(task))
    else:
        return jsonify(error='Error grabbing track.'), 404


#################################### ALBUM ####################################
@grab_bp.route(API_URL.format('grab/album'), methods=['POST'])
@tokenrequired
def album():
    # carefull, do not int(album_id) qobuz has leading zeros in some
    # album ids
    album_id = request.form.get('id', None)
    service = request.form.get('service', None)
    if not album_id or not service:
        return jsonify(error='Missing argument', args={'id': album_id, 'service': service}), 400

    album = ci.services[service].get_album(album_id)
    album_task = chimera.concurrency.blackhole(album, 'album')

    # create json dump
    status = DownloadThread.wrapper(album_task.job_id, 'album', DownloadThread.to_json_album)
    status['progress'] = float()
    return jsonify(status)


@grab_bp.route(API_URL.format('grab/data/album'), methods=['GET'])
@tokenrequired
def album_data():
    # carefull, do not int(album_id) qobuz has leading zeros in some
    # album ids
    album_id = request.args.get('id')
    service = request.args.get('service')
    res = None
    #creating album objects takes too long
    # not alot of keys are neeed
    # album.title, album.songs => song_id, title, artist
    if service == 'deezer':
        album = ci.services[service].get_album_data(int(album_id))
        res = {
            'title': album['results']['DATA']['ALB_TITLE'],
            'album_id': album['results']['DATA']['ALB_ID'],
            'songs': api.grab.utils.create_deezer_tracks(album['results']['SONGS']['data'])
        }
    elif service == 'tidal':
        album = ci.services[service].get_album_full_data(int(album_id))
        res = {
            'title': album['title'],
            'album_id': album['id'],
            'songs': api.grab.utils.create_tidal_tracks(album['songs']['items'])
        }
    elif service == 'qobuz':
        album = ci.services[service].get_album_data(album_id)
        res = {
            'title': album['title'],
            'album_id': album['id'],
            'songs': api.grab.utils.create_qobuz_tracks(album)
        }

    return jsonify(res)

#################################### PLAYLIST ####################################
@grab_bp.route(API_URL.format('grab/playlist'), methods=['POST'])
@tokenrequired
def playlist():
    playlist_id = request.form.get('id', None)
    service = request.form.get('service', None)

    if not playlist_id or not service:
        return jsonify(error='Missing argument', args={'id': playlist_id, 'service': service}), 400

    playlist = ci.services[service].get_playlist(playlist_id)
    playlist_task = chimera.concurrency.blackhole(playlist, 'playlist')

    status = DownloadThread.wrapper(playlist_task.job_id, 'playlist', DownloadThread.to_json_playlist)
    status['progress'] = float()
    return jsonify(status)

@grab_bp.route(API_URL.format('grab/data/playlists'), methods=['GET'])
@tokenrequired
def user_playlist_data():
    """gets users playlist data
    uses dtq as service argument"""
    services = ci.map_service(request.args['service'])
    res = []
    # qobuz does not work, no playlists to test!
    for service in services:
        res += service.get_user_playlists_data()
    return jsonify(res)


@grab_bp.route(API_URL.format('grab/data/playlist'), methods=['GET'])
@tokenrequired
def playlist_data():
    """gets data  for specified playlist id"""
    # get_playlist_data
    playlist_id = request.args.get('id')
    service = request.args.get('service')
    res = None
    #creating album objects takes too long
    # not alot of keys are neeed
    # album.title, album.songs => song_id, title, artist
    if service == 'deezer':
        playlist = ci.services[service].get_playlist_data(playlist_id)
        res = {
            'title': playlist['title'],
            'playlist_id': playlist['id'],
            'songs': api.grab.utils.create_deezer_tracks_playlist(playlist['tracks']['data']),
            'image': playlist['picture_xl']
        }
    elif service == 'tidal':
        playlist = ci.services[service].get_playlist_data(playlist_id)
        res = {
            'title': playlist['title'],
            'playlist_id': playlist['uuid'],
            'songs': api.grab.utils.create_tidal_tracks(playlist['songs']),
            'image': ARTIST_IMG_URL.format(width=512, height=512, id=playlist['uuid'], id_type='uuid')
        }
    elif service == 'qobuz':
        playlist = ci.services[service].get_playlist_data(playlist_id)
        res = {
            'title': playlist['name'],
            'playlist_id': playlist['id'],
            'songs': api.grab.utils.create_qobuz_tracks_playlist(playlist['songs']),
            'image': None,
            'images': playlist['images300']
        }
        pass

    return jsonify(res)


#################################### DISCOGRAPHY ####################################
@grab_bp.route(API_URL.format('grab/discography'), methods=['POST'])
@tokenrequired
@parseargs('POST', ['id', 'service'])
def discography(args):
    service = ci.services[args['service']]
    discography = chimera.discography.get_discography(args['id'], service)
    discography.check()
    discography_task = chimera.concurrency.blackhole(discography, 'discography')

    status = DownloadThread.wrapper(discography_task.job_id, 'discography', DownloadThread.to_json_discography)
    status['progress'] = float()
    return jsonify(status)

#################################### VIDEO ####################################
@grab_bp.route(API_URL.format('grab/video'), methods=['POST'])
@tokenrequired
@parseargs('POST', ['id'])
def grab_video(args):
    video = ci.tidal.get_video(args['id'])
    video_task = chimera.concurrency.blackhole(video, 'video')
    status = DownloadThread.wrapper(video_task.job_id, 'video', DownloadThread.to_json_video)
    return jsonify(status)
