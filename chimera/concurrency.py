"""logic to handle concurrent downloads for track, album and playlists"""
import threading
import time

import api.models
import chimera.download
from db import cc
from main import ci

# from chimera.utils import timeit

def blackhole(thing, ttype):
    """put anything in this and it will create a Task object
    and add it to the queue
    Args:
        `thing` Track, Album, Playlist
        `type` string representation of the thing
    """
    if ttype == 'track':
        task = api.models.TrackTask(thing, ttype)
        ci.queue.put(task)
        return task

    elif ttype == 'album':
        album_task = api.models.AlbumTask(thing)
        for task in album_task.album.songs:
            ci.queue.put(task)
        api.models.store['album'][album_task.job_id] = album_task
        return album_task

    elif ttype == 'discography':
        discography_task = api.models.DiscographyTask(thing)
        for album in discography_task.discography.albums:
            for task in album.songs:
                ci.queue.put(task)
        api.models.store['discography'][discography_task.job_id] = discography_task
        return discography_task

    elif ttype == 'playlist':
        playlist_task = api.models.PlaylistTask(thing)
        for task in playlist_task.playlist.songs:
            ci.queue.put(task)
        api.models.store['playlist'][playlist_task.job_id] = playlist_task

        pwatchdog = threading.Thread(target=playlist_watchdog, name='playlist_watchdog', args=(playlist_task,))
        pwatchdog.daemon = True
        pwatchdog.start()

        return playlist_task

    elif ttype == 'video':
        video_task = api.models.VideoTask(thing)
        ci.queue.put(video_task)
        api.models.store['video'][video_task.job_id] = video_task
        return video_task


# @timeit
def playlist_watchdog(task):
    """playlist has some extra logic to it, for example, create m3u8 file
    this is a watchdog to see if all tracks are downloaded
    """
    while not task.finished:
        time.sleep(5)
        task.get_progress()

    m3u_tracks = []
    missing_tracks = []
    for track_task in task.playlist.songs:
        if track_task.download_status.failed:
            missing_tracks.append(track_task.track)
        else:
            m3u_tracks.append(track_task.download_status.file_name + '\n')
    chimera.download.any_playlist(task.playlist, None, m3u=cc.m3u, log_missing=True, ignore_tracks=True,
                                  m3u_tracks=m3u_tracks, missing_tracks=missing_tracks, verbose=False)
