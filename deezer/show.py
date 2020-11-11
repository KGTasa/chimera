import os

from db import cc
from generic.object import Object
from generic.utils import remove_illegal_characters
from chimera.grabber import fetch_list

class DeezerShow(Object):
    def set_raw_data(self, raw_data):
        self.set_values(
            show_id=raw_data['SHOW_ID'],
            title=raw_data['SHOW_NAME'],
            direct_stream=bool(raw_data['SHOW_IS_DIRECT_STREAM']),
            explicit=bool(raw_data['SHOW_IS_EXPLICIT']),
            language=raw_data['LANGUAGE_CD'],
            label=raw_data['LABEL_NAME'],
        )

    def set_values(
        self,
        show_id=None,
        title=None,
        direct_stream=None,
        explicit=None,
        raw_data=None,
        language=None,
        label=None,
    ):
        if raw_data != None:
            return self.set_raw_data(raw_data)
        self.show_id = show_id
        self.title = title
        self.direct_stream = direct_stream
        self.explicit = explicit
        self.language = language
        self.label = label
        self.episodes = None


    def download(self, folder=None):
        """downlods all episodes with chimera.grabber"""
        if self.episodes == None:
            return
        show_path = os.path.join(cc.root_path, 'podcast', remove_illegal_characters(self.title))
        if os.path.exists(show_path) == False:
            os.makedirs(show_path)
        urls = [episode.stream_url for episode in self.episodes]
        file_names = [os.path.join(show_path, remove_illegal_characters(episode.title)) + '.mp3' for episode in self.episodes]
        print('downloading {}'.format(self.title))
        fetch_list(urls, file_names)