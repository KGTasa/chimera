from __future__ import annotations

import json
import random
import threading
import jsonpickle

from .download import any_task
from cli.utils import master_login
# base store for TrackTask
store = {
    'track': {},
    'album': {},
    'playlist': {},
    'discography': {},
    'video': {}
}

rnd_store = []


def get_rnd():
    rnd = random.randint(0, 100000)
    if rnd not in rnd_store:
        rnd_store.append(rnd)
        return rnd
    else:
        get_rnd()


class VideoTask():
    def __init__(self, video):
        self.job_id = get_rnd()
        self.finished = False
        self.service = 'tidal'
        self.video = video
        self.downloaded = 0
        self.ttype = 'video'

class DiscographyTask():
    def __init__(self, discography):
        self.job_id = get_rnd()
        self.finished = False
        self.service = discography.service
        albums = []
        for album in discography.albums:
            album.songs = [TrackTask(track, ttype='discography') for track in album.songs]
            albums.append(album)
        discography.albums = albums
        self.discography = discography

    def show_status(self):
        albums = []
        for album in self.discography.albums:
            # create progress value of download status
            total_songs = len(album.songs)
            total_progress = float()
            for task in album.songs:
                prg = task.progress
                if prg != None:
                    total_progress = total_progress + float(prg)

            progress = total_progress // total_songs
            album_str = f'{str(progress).rjust(6)}% | {album.title}'
            albums.append('\t └─ ' + album_str)

        album_tasks = '\n.'.join(albums)
        self_str = f'{str(self.get_progress()).rjust(6)}% | {self.discography.artist}'
        if self.finished:
            return self_str
        return self_str + '\n' + album_tasks


    def get_progress(self):
        """get progress of tasks"""
        # create progress value of download status
        total_songs = len([task for album in self.discography.albums for task in album.songs])
        total_progress = float()

        # check if finished
        is_finished = True

        # for each task
        for album in self.discography.albums:
            for task in album.songs:
                prg = task.progress
                if prg != None:
                    total_progress = total_progress + float(prg)

                if task.finished is False:
                    is_finished = False

        self.finished = is_finished
        return total_progress // total_songs

class PlaylistTask():
    def __init__(self, playlist, service=None):
        self.job_id = get_rnd()
        self.finished = False
        self.service = playlist.songs[0].service

        # create tasks
        playlist.songs = [TrackTask(track, ttype='playlist') for track in playlist.songs]
        self.playlist = playlist

    def show_status(self):
        # track_tasks = '\n'.join(['\t └─ ' + t.show_status() for t in self.playlist.songs])
        self_str = f'{str(self.get_progress()).rjust(6)}% | {self.playlist.name} [Total: {self.playlist.song_count}]'
        return self_str  # + '\n' + track_tasks

    def get_progress(self):
        """get progress of tasks"""
        # create progress value of download status
        total_songs = len(self.playlist.songs)
        total_progress = float()

        # check if finished
        is_finished = True

        # for each task
        for task in self.playlist.songs:
            prg = task.progress
            if prg != None:
                total_progress = total_progress + float(prg)

            if not task.finished:
                is_finished = False


        self.finished = is_finished
        return total_progress // total_songs



class AlbumTask():
    def __init__(self, album):
        self.job_id = get_rnd()
        self.finished = False
        self.service = album.songs[0].service

        # create tasks
        album.songs = [TrackTask(track, ttype='album') for track in album.songs]
        self.album = album

    def show_status(self, brief=False):
        track_tasks = '\n'.join(['\t └─ ' + t.show_status() for t in self.album.songs])
        try:
            self_str = f'{str(self.get_progress()).rjust(6)}% | {self.album.title} from {self.album.artists[0].name}'
        except AttributeError as e:
            self_str = f'{str(self.get_progress()).rjust(6)}% | {self.album.title}' # napster no artists


        # only print out album string if finished
        if self.finished or brief:
            return self_str
        return self_str + '\n' + track_tasks

    def get_progress(self):
        """get progress of tasks"""
        # create progress value of download status
        total_songs = len(self.album.songs)
        total_progress = float()

        # check if finished
        is_finished = True

        # for each task
        for task in self.album.songs:
            prg = task.progress
            if prg != None:
                total_progress = total_progress + float(prg)

            if task.finished is False:
                is_finished = False


        self.finished = is_finished
        return total_progress // total_songs

class TrackTask():
    def __init__(self, track, ttype):
        """"ttype str track, album, playlist"""

        self.job_id = get_rnd()
        self.length = 0
        self.downloaded = 0
        self.finished = False
        self.failed = False # track download
        self.track = track
        self.service = track.service
        self.ttype = ttype

    @property
    def progress(self):
        if self.length != 0:
            if self.finished:
                return 100
            else:
                progress_percent = '%.2f' % (self.downloaded / self.length * 100)
                return(progress_percent)
        else:
            if self.failed == True:
                return 100
            elif self.finished:
                return 100
            else:
                return 0

    def show_status(self):
        return f'{str(self.progress).rjust(6)}% | {self.track.title} from {self.track.artist} in {self.track.album.title}'

    def __getstate__(self):
        state = self.__dict__.copy()
        state['progress'] = self.progress
        return state


class DownloadThread(threading.Thread):
    def __init__(self, queue, services, args=(), kwargs=None):
        threading.Thread.__init__(self, args=(), kwargs=None)
        self.queue = queue
        self.daemon = True
        self.finished = False
        self.services = services

    def __repr__(self):
        return f'<Worker {self.ident}> Alive: {self.is_alive()}'

    def run(self):
        while True:
            # Only TrackTasks get added to the queue but to enable
            # video download, VideoTasks get added to the same queue
            task = self.queue.get()
            if type(task) is TrackTask:
                store['track'][task.job_id] = task
            elif type(task) is VideoTask:
                store['video'][task.job_id] = task
            self.check_service(self.services[task.service])
            any_task(task, self.services[task.service], ttype=task.ttype, dlthread=self)
            self.queue.task_done()

    def check_service(self, service):
        """checks if services is logged in"""
        if not service.logged_in:
            master_login(**{str(service).lower(): service}, verbose=False)

    @property
    def queue_size(self):
        return self.queue.qsize()

    @staticmethod
    def store_size():
        return {
            'track_history': len(store['track']),
            'album_history': len(store['album']),
            'playlist_history': len(store['playlist']),
            'discography_history': len(store['discography']),
            'video_history': len(store['video'])
        }

    def get_health(self):
        return {
            'services': {k: v.logged_in for k, v in self.services.items()},
            'alive': self.is_alive(),
            'id': self.ident
        }

    @staticmethod
    def wrapper(job_id, job_type, func, *args, **kwargs):
        """
        Use this wrapper to call functions within DownloadThread, it gets the task
        from the job_id, returns errors if it isn't existings or hasn't started yet.
        Executes `func` with all *args and **kwargs
        Args:
            `job_type` what type of job_id is supplied possible types:
            track, album, playlist
        """
        task = store[job_type].get(job_id, None)
        if task == None:
            # task is not in store, so download has not started yet but,
            # task maybe in queue, look into rand_store if key exists
            if job_id in rnd_store:
                return {'status': 'Task has not yet been started, check back later!'}
            else:
                return {'status': 'Wrong job_id!'}
        return func(task, *args, **kwargs)

    def progress(self, task: TrackTask):
        if task.length != 0:
            return task.progress, task.finished

    @staticmethod
    def parse_job_ids(job_ids):
        valid_request = {k: [] for k in store.keys()}
        for job_id in job_ids:
            for job_store in store.keys():
                if job_id in store[job_store]:
                    valid_request[job_store].append(job_id)
        return valid_request

    @staticmethod
    def to_json_track(task: TrackTask):
        # check if it even exsits
        if task.track:
            # because of __getstate__ there is an extra key 'py/state'
            task_json = json.loads(jsonpickle.encode(task, make_refs=False))['py/state']
            # because GenericTrack is a class all keys are added below py/state
            task_json['track']['path'] = task_json['track']['path']['py/state']
            task_json['track']['path'].pop('_GenericTrackPath__track')
            return task_json

    @staticmethod
    def to_json_album(task: AlbumTask):
        # add progress to object
        prg = task.get_progress()
        res = json.loads(jsonpickle.encode(task, make_refs=False))
        res['progress'] = prg

        for i, track_task in enumerate(res['album']['songs']):
            res['album']['songs'][i] = track_task.pop('py/state')

            # generic path fix
            res['album']['songs'][i]['track']['path'] = res['album']['songs'][i]['track']['path'].pop('py/state')
            res['album']['songs'][i]['track']['path'].pop('_GenericTrackPath__track')

        return res

    @staticmethod
    def to_json_playlist(task: PlaylistTask):
        prg = task.get_progress()
        res = json.loads(jsonpickle.encode(task, make_refs=False))
        res['progress'] = prg

        for i, track_task in enumerate(res['playlist']['songs']):
            res['playlist']['songs'][i] = track_task.pop('py/state')

            # generic path fix
            res['playlist']['songs'][i]['track']['path'] = res['playlist']['songs'][i]['track']['path'].pop('py/state')
            res['playlist']['songs'][i]['track']['path'].pop('_GenericTrackPath__track')

        return res

    @staticmethod
    def to_json_discography(task: DiscographyTask):
        prg = task.get_progress()
        res = json.loads(jsonpickle.encode(task, make_refs=False))
        res['progress'] = prg

        # TODO display progress for every track in each album
        # for i, album in enumerate(res['discography']['albums']):
        #     for j, track_task in enumerate(res['discography']['albums'][i]['songs']):
        #         res['discography']['albums'][i]['songs'][j] = track_task.pop('py/state')
        #         res['discography']['albums'][i][j]['songs']['track']['path'] = res['discography']['albums'][i][j]['track']['path'].pop('py/state')
        #         res['discography']['albums'][i][j]['songs']['track']['path'].pop('_GenericTrackPath__track')
        for i, album in enumerate(res['discography']['albums']):
            res['discography']['albums'][i].pop('songs')
        return res

    @staticmethod
    def to_json_video(task: VideoTask):
        res = json.loads(jsonpickle.encode(task))
        return res