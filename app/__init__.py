# 1. standard
import os
import logging
import sys
import threading
import time

# 2. third party
from flask import Flask, request
import spotipy.oauth2 as oauth2

# 3. chimera
from db import cc

# FLASK
app = Flask(__name__)
app.config['SECRET_KEY'] = '012i34kljasdflmaadl,nfalödf3e'
os.environ['WERKZEUG_RUN_MAIN'] = 'true'
log = logging.getLogger('werkzeug')
log.disabled = True


@app.route('/callback')
def callback_token():
    """
    get callback code
    """
    sp_oauth = oauth2.SpotifyOAuth(
        cc.spotify_client_id,
        cc.spotify_client_secret,
        cc.spotify_redirect_uri,
        scope=cc.spotify_scope,
        cache_path=os.path.join('tokens', '.cache-' + cc.spotify_username)
    )
    code = sp_oauth.parse_response_code(request.url)
    token_info = sp_oauth.get_access_token(code)
    sys.stdout.write('\nLogged in to your spotify account. Enter the last command again! \n-> ')
    return '<h1> Token created, you can close this tab!</h1>'


def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

def toggle_flask_thread(state=True, sleep=0):
    t1 = threading.Thread(target=run_flask)
    if state:
        print('Starting Web-Server please wait...')
        t1.start()
    else:
        time.sleep(sleep)
        t1.stop()
