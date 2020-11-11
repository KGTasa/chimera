import tidal.album
import tidal.artist
import tidal.track_quality
import tidal.utils
from generic.object import Object
from generic.track import Track
from generic.track_path import GenericTrackPath
from generic.utils import DownloadResult

proxies = {'https': 'https://163.172.171.125:80'}


class TidalTrack(Track):
    def set_raw_data(self, song_data, compilation=None):
        """"compliation is used if it's a TidalCompilation"""

        try:
            date_value = song_data['streamStartDate'].split('T')[0]
        except:
            date_value = '2000-01-01'

        is_compilation = False
        if compilation is None:
            album = tidal.album.TidalAlbum.grab_or_create(
                song_data['album']['id'],
                album_id = song_data['album']['id'],
                title = song_data['album']['title'],
                is_full = False,
                date=date_value,
                cover=song_data['album']['cover']
            )
        else:
            album = compilation
            is_compilation = True

        self.set_values(
            title=song_data['title'],
            song_id=song_data['id'],
            artists = list(map(lambda a: tidal.artist.TidalArtist.grab_or_create(
                a['id'], raw_data = a), song_data['artists']
            )),
            album=album,
            qualities=tidal.track_quality.TidalTrackQuality.from_raw_data(song_data),
            is_full=True,
            track_number=song_data['trackNumber'],
            isrc=song_data.get('isrc'),
            duration=song_data['duration'],
            gain=song_data['replayGain'],
            disk_number=song_data['volumeNumber'],
            version=song_data.get('version', ''),
            explicit=song_data['explicit'],
            url=song_data['url'],
            _copyright=song_data['copyright'],
            is_compilation=is_compilation
        )


    def set_values(
        self,
        title=None,
        song_id=None,
        artists=None,
        album=None,
        qualities=None,
        is_full=None,
        raw_data=None,
        track_number=None,
        isrc=None,
        duration=None,
        gain=None,
        disk_number=None,
        version=None,
        explicit=None,
        url=None,
        _copyright=None,
        compilation=None,
        is_compilation=None
    ):
        if raw_data != None:
            self.set_raw_data(raw_data, compilation)
            return
        self.song_id = song_id
        self.title = title.strip()
        self.artists = artists
        self.album = album
        self.qualities = qualities
        self.is_full = is_full
        self.track_number = str(track_number)
        self.isrc = isrc
        self.duration = duration
        self.gain = gain
        self.disk_number = disk_number
        self.version = version
        self.explicit = explicit
        self.copyright = _copyright
        self.url = url
        self.is_compilation = is_compilation
        self.service = 'tidal'


        # set artist value = main artist
        self.artist: str = self.artists[0].name

        self.path = GenericTrackPath(self)

    def get_full_data(self, tidal_session):
        if not self.is_full:
            pass

    def get_stream(self, tidal_session, quality):
        return tidal_session.get_stream(self.song_id, quality)


    def stream(self, track_stream, output_stream, task=None, dlthread=None):
        super().stream(track_stream=track_stream, output_stream=output_stream, task=task, dlthread=dlthread)

    def download(self, tidal_session, folder=None, to_file=None, quality=None, task=None,
                 lower_quality=False, truncate_filename=False, dlthread=None) -> DownloadResult:
        return super().download(tidal_session, folder=folder, to_file=to_file, quality=quality, task=task,
                                lower_quality=lower_quality, truncate_filename=truncate_filename, dlthread=dlthread)


    def decrypt(self, track_stream, file_name):
        """decrypts file from tidal, only used if native token is active,
        requires pycryptodome https://pypi.org/project/pycryptodome/
        """

        from Crypto.Cipher import AES
        from Crypto.Util import Counter

        key, nonce = decrypt_security_token(track_stream.encryption_key)
        counter = Counter.new(64, prefix=nonce, initial_value=0)
        decryptor = AES.new(key, AES.MODE_CTR, counter=counter)

        # Open and decrypt
        with open(file_name, 'rb') as eflac:
            flac = decryptor.decrypt(eflac.read())

        # Replace with decrypted file
        with open(file_name, 'wb') as dflac:
            dflac.write(flac)


    def update_tags(self, tidal_session):
        self.get_full_data(tidal_session)
        self.album.get_full_data(tidal_session)

        self.year = self.album.date.split('-')[0]
        # TODO
        # if cc.discogs_enabled:
        #     dtag = chimera.discogs.search(title=self.title, artist=self.artist)
        #     if dtag:
        #         if dtag.style_found:
        #             self.album.genre = dtag.styles
        #         if dtag.year_found:
        #             self.year = dtag.year
        #             self.album.date = dtag.year
        super().update_tags()

class TidalTrackStream(Object):
    def set_raw_data(self, raw_data):
        self.set_values(
            track_id = raw_data['trackId'],
            quality = raw_data['soundQuality'],
            url = raw_data['url'],
            codec = raw_data['codec'],
            encryption_key = raw_data['encryptionKey']
        )

    def set_values(self, track_id=None, quality=None, url=None, codec=None, encryption_key=None, raw_data=None):
        if raw_data != None:
            self.set_raw_data(raw_data)
            return
        self.track_id = track_id
        self.quality = quality
        self.url = url
        self.codec = codec
        self.encryption_key = encryption_key


def decrypt_security_token(security_token):
    """
    From here https://github.com/redsudo/RedSea
    Decrypts security token into key and nonce pair
    security_token should match the securityToken value from the web response
    """
    import base64
    from Crypto.Cipher import AES

    # Do not change this
    master_key = 'UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754='

    # Decode the base64 strings to ascii strings
    master_key = base64.b64decode(master_key)
    security_token = base64.b64decode(security_token)

    # Get the IV from the first 16 bytes of the securityToken
    iv = security_token[:16]
    encrypted_st = security_token[16:]

    # Initialize decryptor
    decryptor = AES.new(master_key, AES.MODE_CBC, iv)

    # Decrypt the security token
    decrypted_st = decryptor.decrypt(encrypted_st)

    # Get the audio stream decryption key and nonce from the decrypted security token
    key = decrypted_st[:16]
    nonce = decrypted_st[16:24]

    return key, nonce
