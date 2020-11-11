from functools import wraps

from flask import Flask, request, jsonify
from flask_bootstrap import Bootstrap
from flask_cors import CORS

API_VERSION = '0.1'
API_URL = '/api/' + API_VERSION + '/{}'



def parseargs(method, args):
    """Checks for supplied arguments returns error if not all are found
    method: 'GET', 'POST'
    args: List of strings
    """

    def wrapper(f):
        @wraps(f)
        def wrap(*argv, **kwargs):
            found_args = {}
            for arg in args:
                if method == 'GET':
                    found_args[arg] = request.args.get(arg, None)
                else:
                    found_args[arg] = request.form.get(arg, None)

            if len([v for k, v in found_args.items() if v == None]):
                return jsonify(error='Missing argument', args=found_args), 400
            return f(found_args, *argv, **kwargs)
        return wrap
    return wrapper


def create_app(chimera_config=False):
    app = Flask(__name__)
    cors = CORS(app, resources={r'/*': {'origins': '*'}})
    app.config['SECRET_KEY'] = 'lkj1234oipujsdfalsknm2334açRJ'

    bootstrap = Bootstrap(app)
    from api.status import status_bp
    app.register_blueprint(status_bp)

    from api.grab import grab_bp
    app.register_blueprint(grab_bp)

    from api.search import search_bp
    app.register_blueprint(search_bp)

    from api.service import service_bp
    app.register_blueprint(service_bp)

    if chimera_config:
        from api.chimera import chimera_bp
        app.register_blueprint(chimera_bp)

    return app
