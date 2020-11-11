from enum import Enum


class DeezerTrackQuality(Enum):
    #AAC_64 = 1
    #MP3_64 = 2
    MP3_128 = 1
    #MP3_256 = 4
    MP3_320 = 3
    FLAC = 9
    @staticmethod
    def from_raw_data(raw_data):
        bindings = {
            'FILESIZE_MP4_RA1': '360_RA1',
            'FILESIZE_MP4_RA2': '360_RA2',
            'FILESIZE_MP4_RA3': '360_RA3',
            # 'FILESIZE_AAC_64': 'AAC_64',
            # 'FILESIZE_MP3_64': 'MP3_64',
            'FILESIZE_MP3_128': 'MP3_128',
            # 'FILESIZE_MP3_256': 'MP3_256',
            'FILESIZE_MP3_320': 'MP3_320',
            'FILESIZE_FLAC': 'FLAC',
        }
        track_qualities = list(map(
            lambda k: bindings[k],
            filter(
                lambda k: k in bindings and raw_data[k] != 0 and raw_data[k] != '0',
                raw_data.keys(),
            )
        ))

        # shuffle 128 and 320 for fallback to work correctly
        shuffle = ['FLAC', 'MP3_320', 'MP3_128']
        for key in shuffle:
            if key in track_qualities:
                i = track_qualities.index(key)
                track_qualities.insert(0, track_qualities.pop(i))
        return track_qualities

    @staticmethod
    def get_file_format(quality):
        if isinstance(quality, DeezerTrackQuality):
            quality = quality.name
        formats = {
            '.aac': ['AAC_64'],
            '.mp3': ['MP3_64', 'MP3_128', 'MP3_256', 'MP3_320'],
            '.flac': ['FLAC'],
            '.mp4': ['360_RA3', '360_RA2', '360_RA1']
        }
        for format in formats.keys():
            qualities = formats[format]
            if quality in qualities:
                return format
