from queue import Queue

from db import cc
from deezer.deezer import Deezer
from napster.napster import Napster
from qobuz.qobuz import Qobuz
from soundcloud.soundcloud import Soundcloud
from tidal.tidal import Tidal
from generic.object import Object
if cc.gpm_enabled:
    from gpm.gpm import GPM


def create_services():
    """used for api workers"""
    services = {
        'deezer': Deezer(),
        'tidal': Tidal(),
        'qobuz': Qobuz(),
        # 'soundcloud': Soundcloud(cc.soundcloud_username),
        'napster': Napster(cc.napster_api_token),
    }
    if cc.gpm_enabled:
        services['gpm'] = GPM(cc.gpm_device_id)
    services['spotify'] = services[cc.spotify_default_service]
    return services

class ChimeraInterface(Object):
    """This class is used to interact with chimera"""
    def set_values(self):
        #only dummy, because generic.Object
        pass

    def __init__(self):
        self.a_deezer = 'deezer'
        self.a_tidal = 'tidal'
        self.a_qobuz = 'qobuz'
        self.a_dtq = 'dtq' # all combined for track, album search
        self.a_soundcloud = 'soundcloud'
        self.a_napster = 'napster'
        self.a_gpm = 'gpm'
        self.a_spotify = 'spotify'

        self.deezer = Deezer()
        self.tidal = Tidal()
        self.qobuz = Qobuz()
        self.soundcloud = Soundcloud(cc.soundcloud_username)
        self.napster = Napster(cc.napster_api_token)
        self.gpm = GPM(cc.gpm_device_id) if cc.gpm_enabled else None
        self.active = 'deezer'

        self.spotify_conversion = self.deezer

        # services is mostly used for api workers
        # and to check which services are logged in
        self.services = {
            self.a_deezer: self.deezer,
            self.a_tidal: self.tidal,
            self.a_qobuz: self.qobuz,
            # self.a_soundcloud: self.soundcloud,
            self.a_napster: self.napster,
        }
        if cc.gpm_enabled:
            self.services[self.a_gpm] = self.gpm
        # self.services['spotify'] = self.services[cc.spotify_default_service]

        self.download_workers = []
        self.queue = Queue()

    def add_workers(self, revive=None, count=None):
        from api.models import DownloadThread
        if revive == None:
            for i in range(cc.workers):
                download_worker = DownloadThread(self.queue, create_services())
                download_worker.start()
                self.download_workers.append(download_worker)

    @property
    def service(self):
        if self.active == self.a_deezer:
            return self.deezer
        elif self.active == self.a_tidal:
            return self.tidal
        elif self.active == self.a_qobuz:
            return self.qobuz
        elif self.active == self.a_soundcloud:
            return self.soundcloud
        elif self.active == self.a_napster:
            return self.napster
        elif self.active == self.a_gpm:
            return self.gpm
        elif self.active == self.a_spotify:
            return self.spotify_conversion

    @property
    def cli(self):
        from cli import (deezer_cli, dtq_cli, gpm_cli, napster_cli, qobuz_cli,
                         soundcloud_cli, spotify_cli, tidal_cli)
        if self.active == self.a_deezer:
            return deezer_cli
        elif self.active == self.a_tidal:
            return tidal_cli
        elif self.active == self.a_qobuz:
            return qobuz_cli
        elif self.active == self.a_soundcloud:
            return soundcloud_cli
        elif self.active == self.a_dtq:
            return dtq_cli
        elif self.active == self.a_napster:
            return napster_cli
        elif self.active == self.a_gpm:
            return gpm_cli
        elif self.active == self.a_spotify:
            return spotify_cli

    def services_logged_in(self):
        return {n: s for n, s in self.services.items() if s.logged_in}

    def map_service(self, raw, _format='list', check_login=False):
        """returns a list or dict of found services in raw"""
        raw_s = [x.strip() for x in raw.split(',')]
        _services = []
        services = self.services
        for service in raw_s:
            if service in services:
                if check_login:
                    if services[service].logged_in:
                        _services.append(services[service])
                else:
                    _services.append(services[service])
        if _format == 'list':
            return _services
        elif _format == 'dict':
            return {str(s).lower(): s for s in _services}
