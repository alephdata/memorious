

from chardet.universaldetector import UniversalDetector


def guess_fh_encoding(fh):
    encoding_detector = UniversalDetector()
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
