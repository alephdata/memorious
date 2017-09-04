import os
import tempfile
from chardet.universaldetector import UniversalDetector


def save_to_temp(content, suffix=''):
    _, path = tempfile.mkstemp(suffix=suffix)
    with open(path, 'w') as fh:
        fh.write(content)
    return path


def guess_fh_encoding(path):
    encoding_detector = UniversalDetector()
    with open(path, 'r') as fh:
        while True:
            chunk = fh.read(4096)
            if not chunk:
                return
            encoding_detector.feed(chunk)
            if encoding_detector.done:
                break

    encoding_detector.close()
    if encoding_detector.result:
        return encoding_detector.result.get('encoding')
