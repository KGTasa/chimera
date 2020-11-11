"""
place for downloading different tracks for DownloadThread
with the correct config options set
"""
from chimera.download import any_track, sp_track

from db import cc
from cli.utils import parse_ds


def any_task(task, service, ttype, dlthread=None, *args, **kwargs):
    """downloads any track task
    Args:
        `ttype` str track, album, playlist
    """
    if ttype == 'track':
        return _any_track(task, service, dlthread=dlthread, *args, *kwargs)
    elif ttype == 'album':
        return _any_album(task, service, dlthread=dlthread, *args, **kwargs)
    elif ttype == 'playlist':
        return _any_playlist(task, service, dlthread=dlthread, *args, **kwargs)
    elif ttype == 'discography':
        return _any_playlist(task, service, dlthread=dlthread, *args, **kwargs)
    elif ttype == 'video':
        return _any_video(task, service, dlthread=dlthread, *args, **kwargs)


def _any_track(task, service, dlthread=None,  *args, **kwargs):
    if task.track.service == 'deezer':
        ds = any_track(task.track, service, overwrite=cc.dl_track_overwrite,
                       add_to_db=cc.dl_track_add_to_db, check_db=cc.dl_track_check_db,
                       lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics,
                       task=task, dlthread=dlthread)

    elif task.track.service in ['tidal', 'qobuz', 'napster', 'gpm']:
        ds = any_track(task.track, service, overwrite=cc.dl_track_overwrite,
                       add_to_db=cc.dl_track_add_to_db, check_db=cc.dl_track_check_db,
                       task=task, dlthread=dlthread)
    elif task.track.service == 'spotify':
        ds = sp_track(task.track, service, task=task, dlthread=dlthread) # uses playlist config

    parse_ds(ds, verbose=False)
    task.download_status = ds

def _any_album(task, service, dlthread=None, *args, **kwargs):
    if task.service == 'deezer':
        ds = any_track(task.track, service, overwrite=cc.dl_album_overwrite,
                       add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db,
                       lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics,
                       task=task, dlthread=dlthread)
    else:
        ds = any_track(task.track, service, overwrite=cc.dl_album_overwrite,
                       add_to_db=cc.dl_album_add_to_db, check_db=cc.dl_album_check_db,
                       task=task, dlthread=dlthread)
    parse_ds(ds, verbose=False)
    task.download_status = ds

def _any_playlist(task, service, dlthread=None, *args, **kwargs):
    if task.service == 'deezer':
        ds = any_track(task.track, service, overwrite=cc.dl_playlist_overwrite,
                       add_to_db=cc.dl_playlist_add_to_db, check_db=cc.dl_playlist_check_db,
                       lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics,
                       task=task, dlthread=dlthread)
    elif task.track.service == 'spotify':
        ds = sp_track(task.track, service, task=task, dlthread=dlthread) # uses playlist config
    else:
        ds = any_track(task.track, service, overwrite=cc.dl_playlist_overwrite,
                       add_to_db=cc.dl_playlist_add_to_db, check_db=cc.dl_playlist_check_db,
                       task=task, dlthread=dlthread)
    parse_ds(ds, verbose=False)
    task.download_status = ds

def _any_discography(task, service, dlthread=None, *args, **kwargs):
    if task.service == 'deezer':
        ds = any_track(task.track, service, overwrite=cc.dl_discography_overwrite,
                       add_to_db=cc.dl_discography_add_to_db, check_db=cc.dl_discography_check_db,
                       lyrics=cc.tag_lyrics, save_lyrics=cc.save_lyrics,
                       task=task, dlthread=dlthread)
    elif task.track.service == 'spotify':
        ds = sp_track(task.track, service, task=task, dlthread=dlthread) # uses playlist config
    else:
        ds = any_track(task.track, service, overwrite=cc.dl_discography_overwrite,
                       add_to_db=cc.dl_discography_add_to_db, check_db=cc.dl_discography_check_db,
                       task=task, dlthread=dlthread)
    parse_ds(ds, verbose=False)
    task.download_status = ds

def _any_video(task, service, dlthread=None, *args, **kwargs):
    task.video.download(service, task=task, dlthread=dlthread)
