import time
stime = time.time()
import argparse
import os
import sys

from colorama import init

from api import create_app
from chimera.interface import ChimeraInterface

from config import log
from db import cc

# colorama
init(autoreset=True)

# refactored, imports still fucked
# this is so it will always return the same
# chimera interface, because it get's imported
# from other files
ci = ChimeraInterface.grab_or_create(0)

def arg_parse():
    parser = argparse.ArgumentParser(description='Chimera')
    parser.add_argument('-a', '--api', action='store_true', help='start chimera in api mode')
    parser.add_argument('-na', '--noautologin', action='store_true', help='disable auto login')
    parser.add_argument('--debug', action='store_true', help='enable debug logs')
    parser.add_argument('-url', action='store')
    parser.add_argument('-u', action='store')
    parser.add_argument('-p', action='store')
    parser.add_argument('-sync', action='store_true')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    import cli.main_cli
    # create download workers
    ci.add_workers()

    args = arg_parse()
    if args.api:
        cc.cli = False
    if cc.cli:
        log.info('chimera started')
        if cc.first_run:
            cc.first_run = False
            cc.save()
            cli.main_cli.setup_chimera()
        try:
            cli.main_cli.main(args, stime)
        except (KeyboardInterrupt, SystemExit):
            print('\nExiting...')
            if cc.prod:
                sys.exit()
            else:
                os._exit(1)
    else:
        # set logging to true
        import logging
        app = create_app()
        log = logging.getLogger('werkzeug')
        log.disabled = False
        # from gevent.pywsgi import WSGIServer
        # print('Started API SERVER')
        # http_server = WSGIServer(('0.0.0.0', 5000), app)
        # http_server.serve_forever()
        app.run(host='0.0.0.0', port=5000)
