import locale
import logging
import threading

from memorious.core import settings

LANGUAGES = 'eng'
log = logging.getLogger(__name__)
lock = threading.RLock()


def get_ocr():
    """Check if OCR service is available; else throw an error"""
    if not hasattr(settings, '_ocr'):
        try:
            from tesserocr import PyTessBaseAPI, PSM, OEM
            log.info("Configuring OCR engine...")
            settings._ocr = PyTessBaseAPI(lang=LANGUAGES,
                                          oem=OEM.LSTM_ONLY,
                                          psm=PSM.AUTO_OSD)
        except ImportError:
            log.warning("OCR engine is not available")
            settings._ocr = None
    return settings._ocr


def read_text(image, languages=None):
    """OCR text from an image."""
    with lock:
        api = None
        currlocale = locale.getlocale()
        try:
            locale.setlocale(locale.LC_CTYPE, 'C')
            api = get_ocr()
            if api is None or image is None:
                return ''
            api.SetImage(image)
            return api.GetUTF8Text() or ''
        finally:
            if api is not None:
                api.Clear()
            locale.setlocale(locale.LC_CTYPE, currlocale)


def read_word(image, languages=None, spaces=False):
    """ OCR a word from an image. Useful for captchas.
        Image should be pre-processed to remove noise etc. """
    guess = read_text(image, languages=languages)
    if not spaces:
        guess = ''.join([c for c in guess if c != " "])
        guess = guess.strip()
    return guess


def read_char(image, languages=None):
    return read_word(image, languages=languages)