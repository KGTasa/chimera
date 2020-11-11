from generic.object import Object
class TidalTrackQuality(Object):
    @staticmethod
    def from_raw_data(raw_data):
        qualities = [
            {
                'pretty': 'LOW'
            },
            {
                'pretty': 'HIGH'
            },
            {
                'pretty': 'LOSSLESS'
            },
            {
                'pretty': 'HI_RES'
            }
        ]
        track_qualities = []
        for i, quality in enumerate(qualities):
            if quality['pretty'] == raw_data['audioQuality']:
                for j in range(i + 1):
                    track_qualities.append(qualities[j]['pretty'])
        return track_qualities

    @staticmethod
    def get_file_format(quality):
        formats = {
            '.m4a': ['LOW', 'HIGH'],
            '.flac': ['LOSSLESS', 'HI_RES']
        }
        for format in formats.keys():
            qualities = formats[format]
            if str(quality) in qualities:
                return format