from generic.object import Object
class SoundcloudtrackQuality(Object):
    @staticmethod
    def from_raw_data(raw_data):
        pass

    @staticmethod
    def get_file_format(quality):
        formats = {
            ".m4a": [],
            ".mp3": []
        }
        for format in formats.keys():
            qualities = formats[format]
            if quality in qualities:
                return format