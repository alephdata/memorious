class FunesException(Exception):
    """Base exception class."""
    pass


class StorageNotFound(FunesException):
    """A file hasn't been found in the storage layer."""
    pass


class ConfigurationError(FunesException):
    """A configuration option is not set."""


class RuleParsingException(FunesException):
    """A rule encounters something it can't parse."""
    pass


class NoPathException(FunesException):
    """A required path is not set."""
    pass
