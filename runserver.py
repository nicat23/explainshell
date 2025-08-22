# Compatibility shim for Python 3.11 collections.* removals
import contextlib
with contextlib.suppress(Exception):
    import collections
    import collections.abc as _collections_abc
    if not hasattr(collections, 'MutableSet'):
        collections.MutableSet = _collections_abc.MutableSet  # type: ignore
    if not hasattr(collections, 'Mapping'):
        collections.Mapping = _collections_abc.Mapping  # type: ignore
    if not hasattr(collections, 'MutableMapping'):
        collections.MutableMapping = _collections_abc.MutableMapping  # type: ignore  # noqa: E501
from explainshell import config
from explainshell.web import app

import logging.config

logging.config.dictConfig(config.LOGGING_DICT)

if __name__ == "__main__":
    if config.HOST_IP and isinstance(config.HOST_IP, str):
        app.run(debug=config.DEBUG, host=config.HOST_IP)
    else:
        app.run(debug=config.DEBUG)
