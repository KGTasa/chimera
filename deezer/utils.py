import json
from db import cc
import binascii
import hashlib
from Crypto.Cipher import Blowfish

BLOWFISH_SECRET = b'g4el58' + b'wc0zvf9na1'

PRIVATE_API_URL = 'https://www.deezer.com/ajax/gw-light.php?%s'
PUBLIC_API_URL = 'https://api.deezer.com/'
USER_PICTURES_URL = 'https://e-cdns-images.dzcdn.net/images/user/%s/250x250-000000-80-0-0.jpg'
ALBUM_PICTURES_URL = 'https://e-cdns-images.dzcdn.net/images/cover/%s/' + cc.deezer_cover_size + '-000000-80-0-0.jpg'
ALBUM_PICTURES_URL_THUMBNAIL = 'https://e-cdns-images.dzcdn.net/images/cover/%s/200x200-000000-80-0-0.jpg'
ARTIST_PICTURES_URL = 'https://e-cdns-images.dzcdn.net/images/artist/%s/200x200-000000-80-0-0.jpg'


def dump_json_to_file(data, file_name='data.json'):
    with open(file_name, 'w') as outfile:
        json.dump(data, outfile, indent=2)


def md5hex(data):
    h = hashlib.md5(data)
    return binascii.b2a_hex(h.digest())

def decrypt_chunk(chunk, key):
    c = Blowfish.new(key, Blowfish.MODE_CBC, binascii.a2b_hex('0001020304050607'))
    return c.decrypt(chunk)
