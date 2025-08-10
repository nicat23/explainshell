# Compatibility shim for Python 3.11 collections.* removals
try:
    import collections as _collections
    import collections.abc as _collections_abc
    if not hasattr(_collections, 'MutableSet'):
        _collections.MutableSet = _collections_abc.MutableSet
    if not hasattr(_collections, 'Mapping'):
        _collections.Mapping = _collections_abc.Mapping
    if not hasattr(_collections, 'MutableMapping'):
        _collections.MutableMapping = _collections_abc.MutableMapping
except Exception:
    pass

from explainshell import config
from explainshell.web import app

import logging.config
logging.config.dictConfig(config.LOGGING_DICT)

if __name__ == '__main__':
    if config.HOST_IP:
        app.run(debug=config.DEBUG, host=config.HOST_IP)
    else:
        app.run(debug=config.DEBUG)
