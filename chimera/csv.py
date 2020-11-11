import csv
import os

from db import cc
from db.db import session
from db.models import DBTrack
from main import ci
import chimera.download

def import_from_csv(file, **kwargs):
    with open(file, 'r', newline='', encoding='utf_8_sig') as f:
        reader = csv.reader(f, delimiter=';', escapechar='')
        header = next(reader)
        csv_tracks = [row for row in reader]

    # search
    mixed_tracks = []
    for csv_track in csv_tracks:
        search = chimera.download.search_track_on_services(
            csv_track['title'], csv_track['artist'], csv_track['album'], **ci.services_logged_in()
        )
        mixed_tracks.append({'input': csv_track, 'result': search})
    


def read(csv_file, deezer_session):
    csv_file_name = csv_file.replace('.csv', '')
    csv_missing = csv_file_name + '_missing.csv'
    m3u_playlist = csv_file_name + '.m3u'
    csv_missing_tracks = []
    m3u_tracks = []
    tracks = []
    with open(csv_file, 'r', newline='', encoding='utf_8_sig') as f:
        reader = csv.reader(f, delimiter=';', escapechar='')
        header = next(reader)
        for row in reader:
            # create csv_track object for output csv file
            csv_track = {
                'name': row[0],
                'artist': row[1],
                'album': row[2],
                'release_date': row[3],
                'duration_ms': row[4],
                'spotify_id': row[6]
            }
            if row[5] is not None:
                # iscr exists add to object
                csv_track['isrc'] = row[5]
                # db search for isrc number if not found dbtrack is None
                dbtrack = session.query(DBTrack).filter_by(isrc=row[5]).first()
                if dbtrack is not None:
                    # track already downloaded get fullpath and add to m3u list and csv export
                    print(f'Song {row[0]} by {row[1]} found in db already downloaded, skipping...')
                    # append to m3u playlist
                    m3u_tracks.append(os.path.join(cc.root_path, dbtrack.path) + '\n')
                    continue
                # search for track
                res = deezer_session.search_isrc(row[5])
                if res is False:
                    print(f'song not found: {row[0]}')
                    # not found -> serach with name not implemented yet
                    # append csv output
                    csv_missing_tracks.append(csv_track)
                else:
                    # set spotify id and append to track list
                    res.spotify_id = row[6]
                    tracks.append(res)
                    # update m3u list with full path, maybe problem if song failes to downlaod
                    m3u_tracks.append(res.path.full_path + '\n')


    for track in tracks:
        # check if file exists:
        if os.path.isfile(track.path.full_path):
            # TODO id3tag checker
            continue
        # download song
        chimera.download.track_download(track, deezer_session)


    # write new csv file
    with open(csv_missing, 'w', newline='', encoding='utf_8_sig') as f:
        print('Writing csv status file')
        writer = csv.writer(f, delimiter=';', escapechar='')
        writer.writerow(['track_name', 'artist', 'album', 'release_date', 'duration_ms', 'isrc'])
        for track in csv_missing_tracks:
            writer.writerow([track['name'], track['artist'], track['album'], track['release_date'], track['duration_ms'], track['isrc']])



def write_csv(file_path, tracks):
    with open(file_path, 'w', newline='', encoding='utf_8_sig') as f:
        writer = csv.writer(f, delimiter=';', escapechar='')
        writer.writerow(['track_name', 'artist', 'album', 'release_date', 'seconds', 'isrc'])
        for track in tracks:
            writer.writerow([track.title, track.artist, track.album.title, track.album.date, track.duration, track.isrc])


def write_album_search(file_path, albums):
    with open(file_path, 'w', newline='', encoding='utf_8_sig') as f:
        # {'id': 80226, 'title': 'Fire Up The Blades', 'artist': '3 Inches of Blood'}
        writer = csv.writer(f, delimiter=';', escapechar='')
        writer.writerow(['search', 'id', 'title', 'artist', 'found'])
        for album in albums:
            writer.writerow([album['search'], album['id'], album['title'], album['artist'], album['found']])

def discography_report(file_path, discography):
    with open(file_path, 'w', newline='', encoding='utf_8_sig') as f:
        writer = csv.writer(f, delimiter=';', escapechar='')
        writer.writerow(['title', 'artist', 'album', 'allowed'])
        for album in discography.albums:
            for track in album.songs:
                writer.writerow([track.title, track.artist, track.album.title, track.discography_allowed])