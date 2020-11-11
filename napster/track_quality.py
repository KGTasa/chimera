from generic.object import Object

class NapsterTrackQuality(Object):
    @staticmethod
    def from_raw_data(raw_data):
        # qualities = [
        #     {}
        # ]
        track_qualities = []
        for quality in raw_data['formats']:
              track_qualities.append('{}_{}'.format(quality['name'].split(' ')[0], quality['bitrate']))
        return track_qualities[::-1]
    @staticmethod
    def get_file_format(quality):
        formats = {
            '.m4a': ['AAC_64', 'AAC_192', 'AAC_320']
        }
        for format in formats.keys():
            qualities = formats[format]
            if quality in qualities:
                return format