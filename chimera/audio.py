import json
import os
import re
import wave

import pyaudio
from acrcloud.recognizer import ACRCloudRecognizer

from chimera.discography import check_dir
from cli import dtq_cli
from cli.utils import master_login
from db import cc
from main import ci

wav_path = os.path.join('import', 'cache', 'listen.wav')
RE_BRACKETS = re.compile('(\[|\(|\{).+(\)|\]|\})')


def rec_audio():
    defaultframes = 512
    recorded_frames = []
    device_info = {}
    useloopback = False
    recordtime = 5
    #Use module
    p = pyaudio.PyAudio()

    #Get input or default
    # device_id = 8 # HOME
    # device_id = 5

    #Open stream
    stream = p.open(format = pyaudio.paInt16,
                    channels = 2,
                    rate = 48000,
                    input = True,
                    frames_per_buffer = defaultframes,
                    input_device_index = cc.audio_device_id,
                    as_loopback = True)

    #Start Recording
    print('Listening...')

    for i in range(0, int((48000) / defaultframes * recordtime)):
        recorded_frames.append(stream.read(defaultframes))

    #Stop Recording
    stream.stop_stream()
    stream.close()

    #Close module
    p.terminate()

    filename = wav_path

    waveFile = wave.open(filename, 'wb')
    waveFile.setnchannels(2)
    waveFile.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    waveFile.setframerate(int(48000))
    waveFile.writeframes(b''.join(recorded_frames))
    waveFile.close()

def identify_audio():
    config = {
        'host': cc.audio_acr_host,
        'access_key': cc.audio_acr_access_key,
        'access_secret': cc.audio_access_secret,
        'timeout': 5 # seconds
    }
    re = ACRCloudRecognizer(config)
    print('Recognizing...')
    acr_res = re.recognize_by_file(wav_path, 0)
    return json.loads(acr_res)



def id_and_search(limit=1):
    """services are defined in cc.audio_services, and request with
    map_service from main
    """
    check_dir()
    rec_audio()
    acr_res = identify_audio()
    status_code = acr_res['status']['code']
    if status_code == 1001:
        print('No result')
        return
    title = acr_res['metadata']['music'][0]['title']
    title = re.sub(RE_BRACKETS, '', title)
    q = '{} {} {}'.format(title, acr_res['metadata']['music'][0]['album']['name'], acr_res['metadata']['music'][0]['artists'][0]['name'])
    print(f'Found: {q}')

    # get services and check login
    active_services = ci.map_service(cc.audio_services)
    master_login(**{str(s).lower(): s for s in active_services}, verbose=False)

    r_tracks = []
    for service in active_services:
        r_tracks += service.search_track(q, limit=limit)

    dtq_cli.search_track(q=q, dtq_tracks=r_tracks, **{str(s).lower(): s for s in active_services})


def print_audio_devices():
    p = pyaudio.PyAudio()
    #Set default to first in list or ask Windows
    try:
        default_device_index = p.get_default_input_device_info()
    except IOError:
        default_device_index = -1

    for i in range(0, p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(str(info['index']) + ')\t%s \n\t%s' % (info['name'], p.get_host_api_info_by_index(info['hostApi'])['name']))

        if default_device_index == -1:
            default_device_index = info['index']


    print('Add device_id to your config, look for a WASAPI Speaker.')
