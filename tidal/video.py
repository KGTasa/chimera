import os
import subprocess

import requests


from chimera.grabber import fetch
from db import cc


class TidalVideo:
    def __init__(self, raw_data):
        self.id = raw_data['id']
        self.quality = raw_data['quality']
        self.artist = raw_data['artist']['name']
        self.title = raw_data['title']
        self.type = raw_data['type']
        self.allow_streaming = raw_data['allowStreaming']
        self.urls = None
        self.qualities = None
        sec = int(raw_data['duration'])
        self.duration = '{}:{}'.format(sec // 60, str((sec % 60)).zfill(2))

    def __repr__(self):
        return f'ID {self.id} Video: {self.title}, Artist: {self.artist}, Quality: {self.quality}'

    @staticmethod
    def grab_ts_urls(raw_data):
        return [x for x in raw_data.split('\n') if '#' not in x and x != '']

    def max_quality(self):
        if self.qualities == None:
            return
        return max(self.qualities, key=lambda f: f.width)

    def get_qualities(self, tidal):
        self.qualities = TidalVideoQuality.from_raw_data(
            tidal.get_stream_video(self.id, self.quality))

    def get_stream(self, tidal):
        if self.qualities == None:
            self.get_qualities(tidal)

        return TidalVideo.grab_ts_urls(
            requests.get(self.max_quality().url).text)

    def download(self, tidal, task=None, dlthread=None):
        ts_urls = self.get_stream(tidal)

        print('Video            : {}'.format(self.title))
        print('Duration:        : {}'.format(self.duration))
        print('Selected Quality : {}'.format(self.max_quality().resolution))

        root = cc.tidal_video_path
        subdir = 'temp'

        if dlthread != None:
            subdir += str(dlthread.ident)

        file_name = os.path.join(root, f'{self.artist} - {self.title}') + '{}'
        valid_files = [file_name.format(x) for x in ['.mkv', '.ts', '.mp4']]
        for valid_file in valid_files:
            if os.path.isfile(valid_file):
                print(f'Video already downloaded, skipping {self}')
                if task != None:
                    task.finished = True
                return

        if os.path.exists(os.path.join(root, subdir)) == False:
            os.makedirs(os.path.join(root, subdir))
        ts_files = os.path.join(root, subdir, '{}.ts')

        # download files
        file_names = fetch(ts_urls, [ts_files.format(i) for i in range(len(ts_urls))], task=task)


        cmd = 'copy /b {} "{}"'.format(' + '.join([x for x in file_names]), file_name.format('.ts'))
        subprocess.run(cmd, shell=True) # shell true needed
        [os.remove(file) for file in file_names] # remove temp files
        os.rmdir(os.path.join(root, subdir))

        if cc.tidal_video_pp:
            print('Running ffmpeg...')
            subprocess.run('ffmpeg -i "{}" "{}"'.format(file_name.format('.ts'), file_name.format('.mkv')))

            # delete .ts file
            os.remove(file_name.format('.ts'))

        if task != None:
            task.finished = True


class TidalVideoQuality:
    def __init__(self, raw_data):
        self.bandwith = raw_data[0].split('=')[1]
        self.average_bandwith = raw_data[1].split('=')[1]
        self.resolution = raw_data[4].split('=')[1]
        self.url = [x for x in raw_data if x.startswith('http://api.tidal.com')][0]
        self.width = int(raw_data[4].split('=')[1].split('x')[0]) # jesus christ...
        self.height = int(raw_data[4].split('=')[1].split('x')[1])

    @staticmethod
    def from_raw_data(raw_data):
        lines = raw_data.split('\n')
        headers = ['#EXTM3U', '#EXT-X-VERSION:1', '']
        lines = list(filter(lambda x: x not in headers, lines))
        qualities = []
        for i, line in enumerate(lines):
            if line.startswith('#'):
                line = line.replace('#EXT-X-STREAM-INF:', '')
                qualities.append(TidalVideoQuality([*line.split(','), lines[i + 1]]))
        return qualities
