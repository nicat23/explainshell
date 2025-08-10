# Compatibility shim for Python 3.11+ where collections.MutableSet moved
try:
    import collections as _collections
    import collections.abc as _collections_abc
    # Provide aliases removed in Python 3.10+
    if not hasattr(_collections, 'MutableSet'):
        _collections.MutableSet = _collections_abc.MutableSet
    if not hasattr(_collections, 'Mapping'):
        _collections.Mapping = _collections_abc.Mapping
    if not hasattr(_collections, 'MutableMapping'):
        _collections.MutableMapping = _collections_abc.MutableMapping
except Exception:
    pass

from flask import Flask
app = Flask(__name__)

from explainshell.web import views
from explainshell import store, config

if config.DEBUG:
    from explainshell.web import debugviews

app.config.from_object(config)
