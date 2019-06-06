import logging
import io
from hashlib import sha1
from servicelayer.rpc import TextRecognizerService
from servicelayer.cache import get_redis, make_key
from servicelayer.settings import REDIS_LONG

from memorious.core import ocr_service

log = logging.getLogger(__name__)


class OCRService(TextRecognizerService):
    """Perform OCR using an RPC-based service. The service is available at
    github.com/alephdata/aleph-recognize-text, and built as a Docker image
    with the name: alephdata/aleph-recognize-text:latest."""

    MIN_SIZE = 50 * 2
    MAX_SIZE = (1024 * 1024 * 4) - 1024

    @classmethod
    def is_available(cls):
        return cls.SERVICE is not None

    def extract_text(self, data, languages=None):
        if not self.MIN_SIZE < len(data) < self.MAX_SIZE:
            log.info('OCR: file size out of range (%d)', len(data))
            return None
        conn = get_redis()
        key = make_key('ocr', sha1(data).hexdigest())
        if conn.exists(key):
            text = conn.get(key)
            if text is not None:
                log.info('OCR: %s chars cached', len(text))
            return text

        text = self._extract_text(data, languages=languages)
        if text is not None:
            conn.set(key, text, ex=REDIS_LONG)
            log.info('OCR: %s chars (from %s bytes)',
                     len(text), len(data))
        return text

    def _extract_text(self, data, languages=None):
        text = self.Recognize(data, languages=languages)
        if text is not None:
            return text.text or ''


def read_text(image, languages=None):
    """OCR text from an image."""
    img_bytes = io.BytesIO()
    image.save(img_bytes, format=image.format)
    data = img_bytes.getvalue()
    guess = ocr_service.extract_text(data, languages=languages)
    return guess


def read_word(image, languages=None, spaces=False):
    """ OCR a word from an image. Useful for captchas.
        Image should be pre-processed to remove noise etc. """
    guess = read_text(image, languages=languages)
    if not spaces:
        guess = ''.join([c for c in guess if c != " "])
        guess = guess.strip()
    return guess
