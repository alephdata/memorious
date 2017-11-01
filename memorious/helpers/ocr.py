from tesserocr import PyTessBaseAPI # Requires Tesseract 0.3.4+


def read_word(image, whitelist=None, chars=None, spaces=False):
    """ OCR a single word from an image. Useful for captchas.
        Image should be pre-processed to remove noise etc. """
    api = PyTessBaseAPI()
    api.SetPageSegMode(8)
    if whitelist is not None:
        api.SetVariable("tessedit_char_whitelist",
                            whitelist)
    api.SetImage(image)
    api.Recognize()
    guess = api.GetUTF8Text()

    if not spaces:
        guess = ''.join([c for c in guess if c != " "])
        guess = guess.strip()

    if chars is not None and len(guess) != chars:
        return guess, None

    return guess, api.MeanTextConf()