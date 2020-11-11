import json
API_URL = 'https://www.qobuz.com/api.json/0.2/'
STREAM_URL = 'trackgetFileUrlformat_id{}intentstreamtrack_id{}{}{}'
ALBUM_URL = 'https://play.qobuz.com/album/{}'

# APP ID and Secret
BASE_URL = 'https://play.qobuz.com/{}'


def dump_json_to_file(data, file_name="qobuz_album.json"):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile, indent=2)
