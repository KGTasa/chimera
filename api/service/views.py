
from flask import jsonify, request

from api import API_URL

from api.service import service_bp
# from db import cc
from main import ci
from cli.utils import master_login
from api.status import tokenrequired


@service_bp.route(API_URL.format('service/login'), methods=['GET'])
@tokenrequired
def login():
    # """login with qobuz credentials from config"""
    services = ci.map_service(request.args['service'], _format='dict')
    master_login(**services)
    return jsonify('OK')
