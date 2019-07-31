class MemoriousException(Exception):
    """Base exception class."""
    pass


class QueueTooBigError(MemoriousException):
    pass


class ConfigurationError(MemoriousException):
    """A configuration option is not set."""


class RuleParsingException(MemoriousException):
    """A rule encounters something it can't parse."""
    pass


class StorageFileMissing(MemoriousException):
    """A file could not be found in the blob storage."""

    def __init__(self, content_hash, file_name=None):
        self.content_hash = content_hash
        self.file_name = file_name
        msg = 'Could not load: %s' % content_hash
        super(StorageFileMissing, self).__init__(msg)


class ParseError(MemoriousException):
    """An error while parsing a structured HTTP response."""
    pass


class RateLimitException(Exception):
    """Rate limit exceeded for a crawler operation"""
    pass
