class FunesException(Exception):
    """Base exception class."""
    pass


class ConfigurationError(FunesException):
    """A configuration option is not set."""


class RuleParsingException(FunesException):
    """A rule encounters something it can't parse."""
    pass
