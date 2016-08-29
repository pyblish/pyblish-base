class PyblishError(Exception):
    """Baseclass for all Pyblish exceptions"""


class ValidationError(PyblishError):
    """Baseclass for validation errors"""


class SelectionError(PyblishError):
    """Baseclass for selection errors"""


class ExtractionError(PyblishError):
    """Baseclass for extraction errors"""


class ConformError(PyblishError):
    """Baseclass for conforming errors"""


class NoInstancesError(Exception):
    """Raised if no instances could be found"""
