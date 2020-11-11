import json

import jsonpickle
from flask import jsonify, request

from api import API_URL, parseargs
from api.search import search_bp
from api.status import tokenrequired
from chimera.dtq import adv_search
from main import ci


@search_bp.route(API_URL.format('search/track'), methods=['GET'])
@tokenrequired
def track():
    """
    search for tracks on specified service
    Args:
        `q` Search argument
        `service` d = Deezer, t = Tidal, q = Qobuz
        Able to combine them however it is possible, so : tq = Tidal and Qobuz
    """
    query = request.args['q']
    limit = int(request.args.get('limit', 5))
    services = ci.map_service(request.args['service'])
    q_tracks = []
    for service in services:
        q_tracks += service.search_track(query, limit=limit)

    return jsonify(q_tracks)


@search_bp.route(API_URL.format('search/track_adv'), methods=['GET'])
@tokenrequired
def track_adv_search():
    """
    Advanced Search with ratios
    """
    title = request.args['title']
    artist = request.args['artist']
    album = request.args.get('album', '')
    isrc = request.args.get('isrc', '')
    services = ci.map_service(request.args['service'])

    tracks = adv_search(**{str(s).lower(): s for s in services},
                        title=title, artist=artist, album=album, isrc=isrc)
    return jsonify(tracks)


@search_bp.route(API_URL.format('search/video'), methods=['GET'])
@tokenrequired
@parseargs('GET', ['q'])
def video(args):
    """for tidal video search"""
    videos = ci.tidal.search_videos(args['q'])
    return jsonify(json.loads(jsonpickle.encode(videos)))
