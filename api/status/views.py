from flask import jsonify, request

from api import API_URL
from api.models import DownloadThread
from api.status import status_bp, tokenrequired
from main import ci


@status_bp.route(API_URL.format('status/health'), methods=['GET'])
@tokenrequired
def health():
    """various informations about service health"""
    worker_status = [w.get_health() for w in ci.download_workers]
    store_size = DownloadThread.store_size()

    return jsonify({
        'workers': worker_status,
        'store': store_size,
        'queue': ci.queue.qsize()
    })

@status_bp.route(API_URL.format('status'))
@tokenrequired
def status_wrapper():
    job_ids = [int(x) for x in (request.args.get('job_ids').split(','))]
    valid_ids = DownloadThread.parse_job_ids(job_ids)
    result = {'track': [], 'album': [], 'playlist': []}
    func = {
        'track': DownloadThread.to_json_track,
        'album': DownloadThread.to_json_album,
        'playlist': DownloadThread.to_json_playlist,
        'discography': DownloadThread.to_json_discography
    }
    for job_type, ids in valid_ids.items():
        for job_id in ids:
            progress = DownloadThread.wrapper(job_id, job_type, func[job_type])
            result[job_type].append(progress)
    return jsonify(result)

@status_bp.route(API_URL.format('status/track'), methods=['GET'])
@tokenrequired
def track():
    job_id = int(request.args.get('job_id'))
    status = DownloadThread.wrapper(job_id, 'track', DownloadThread.to_json_track)
    return jsonify(status)


@status_bp.route(API_URL.format('status/album'), methods=['GET'])
@tokenrequired
def album():
    job_id = int(request.args.get('job_id'))
    status = DownloadThread.wrapper(job_id, 'album', DownloadThread.to_json_album)
    return jsonify(status)

@status_bp.route(API_URL.format('status/playlist'), methods=['GET'])
@tokenrequired
def playlist():
    job_id = int(request.args.get('job_id'))
    status = DownloadThread.wrapper(job_id, 'playlist', DownloadThread.to_json_playlist)
    return jsonify(status)

@status_bp.route(API_URL.format('status/discography'), methods=['GET'])
@tokenrequired
def discography():
    job_id = int(request.args.get('job_id'))
    status = DownloadThread.wrapper(job_id, 'discography', DownloadThread.to_json_discography)
    return jsonify(status)

@status_bp.route(API_URL.format('status/video'), methods=['GET'])
@tokenrequired
def video():
    job_id = int(request.args.get('job_id'))
    status = DownloadThread.wrapper(job_id, 'video', DownloadThread.to_json_video)
    return jsonify(status)

@status_bp.route(API_URL.format('status/thread'), methods=['GET'])
@tokenrequired
def is_alive():
    return jsonify(status=DownloadThread.is_alive())


@status_bp.app_errorhandler(500)
def http_500(e):
    return jsonify(error='something wrong with chimera'), 500
