import logging
import io
from memorious.core import ocr_service

log = logging.getLogger(__name__)


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
