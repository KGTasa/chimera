import os

import deezer.show
from db import cc
from generic.object import Object
from generic.utils import remove_illegal_characters
from chimera.grabber import fetch_list

class DeezerEpisode(Object):
    def set_raw_data(self, raw_data):
        self.set_values(
            episode_id=raw_data['EPISODE_ID'],
            title=raw_data['EPISODE_TITLE'],
            filesize=raw_data['FILESIZE_MP3_64'], # look into creating quality class
            show=deezer.show.DeezerShow.grab_or_create(
                raw_data['SHOW_ID'], title=raw_data['SHOW_NAME'], show_id=raw_data['SHOW_ID'],
                direct_stream=bool(raw_data['SHOW_IS_DIRECT_STREAM'])
            ),
            duration=raw_data['DURATION'],
            stream_url=raw_data['EPISODE_DIRECT_STREAM_URL']
        )

    def set_values(
        self,
        episode_id=None,
        title=None,
        filesize=None,
        show=None,
        duration=None,
        stream_url=None,
        raw_data=None
    ):
        if raw_data != None:
            return self.set_raw_data(raw_data)
        self.episode_id = episode_id
        self.title = title
        self.filesize = filesize
        self.show = show
        self.duration = duration
        self.stream_url = stream_url


    def download(self):
        show_path = os.path.join(cc.root_path, 'podcast', remove_illegal_characters(self.show.title))
        if os.path.exists(show_path) == False:
            os.makedirs(show_path)
        urls = [self.stream_url]
        file_names = [os.path.join(show_path, remove_illegal_characters(self.title)) + '.mp3']
        fetch_list(urls, file_names)