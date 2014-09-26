class PyblishError(Exception):
    pass


class NoInstancesError(PyblishError):
    pass


class ValidationError(PyblishError):
    pass


class SelectionError(PyblishError):
    pass


class ExtractionError(PyblishError):
    pass


class ConformError(PyblishError):
    pass
