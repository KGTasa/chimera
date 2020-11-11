class QobuzTrackQuality:
    @staticmethod
    def from_raw_data(raw_data):
        qualities = [
            {
                'format_id': 5,
                'mime_type': 'audio/mpeg',
                'bit_depth': 16,
                'sampling_rate': 44.1,
                'pretty': 'MP3_320'
            },
            {
                'format_id': 6,
                'mime_type': 'audio/flac',
                'bit_depth': 16,
                'sampling_rate': 44.1,
                'pretty': '16-bit 44.1kHz'
            },
            {
                'format_id': 7,
                'mime_type': 'audio/flac',
                'bit_depth': 24,
                'sampling_rate': 44.1,
                'pretty': '24-bit 44.1kHz'
            },
            {
                'format_id': 27,
                'mime_type': 'audio/flac',
                'bit_depth': 24,
                'sampling_rate': 96,
                'pretty': '24-bit 96kHz'
            },
            {
                'format_id': 27,
                'mime_type': 'audio/flac',
                'bit_depth': 24,
                'sampling_rate': 192,
                'pretty': '24-bit 192kHz'
            }
        ]
        track_qualities_pretty = []
        track_qualities = []
        for quality in qualities:
            if raw_data['maximum_bit_depth'] >= quality['bit_depth']:
                if raw_data['maximum_bit_depth'] == 24:
                    if raw_data['maximum_sampling_rate'] >= quality['sampling_rate']:
                        track_qualities_pretty.append(quality['pretty'])
                        track_qualities.append(quality['pretty'])
                    elif 44.1 < raw_data['maximum_sampling_rate'] < 96:
                        # create custom quality profile
                        track_qualities.append('24-bit 96kHz')
                        track_qualities_pretty.append('24-bit {}kHz'.format(raw_data['maximum_sampling_rate']))
                else:
                    track_qualities_pretty.append(quality['pretty'])
                    track_qualities.append(quality['pretty'])
        # pretty is only needed to display correct kHz range in `show_track`
        return {'pretty': track_qualities_pretty, 'qualities': track_qualities}

    @staticmethod
    def get_file_format(quality):
        formats = {
            '.mp3': ['MP3_320'],
            '.flac': ['16-bit 44.1kHz', '24-bit 44.1kHz', '24-bit 96kHz']
        }
        for format in formats.keys():
            qualities = formats[format]
            if str(quality) in qualities:
                return format
