class FunesException(Exception):
    """Base exception class."""
    pass


class ConfigurationError(FunesException):
    """A configuration option is not set."""


class RuleParsingException(FunesException):
    """A rule encounters something it can't parse."""
    pass


class StorageFileMissing(FunesException):
    """A file could not be found in the blob storage."""

    def __init__(self, content_hash, file_name=None):
        self.content_hash = content_hash
        self.file_name = file_name
        msg = 'Could not load: %s' % content_hash
        super(StorageFileMissing, self).__init__(msg)


class ParseError(FunesException):
    """An error while parsing a structured HTTP response."""
    pass
