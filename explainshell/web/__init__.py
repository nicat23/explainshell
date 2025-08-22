import collections
import collections.abc

# For Python 3.10+
if not hasattr(collections, 'MutableSet'):
    setattr(collections, 'MutableSet', collections.abc.MutableSet)
if not hasattr(collections, 'Mapping'):
    setattr(collections, 'Mapping', collections.abc.Mapping)
if not hasattr(collections, 'MutableMapping'):
    setattr(collections, 'MutableMapping', collections.abc.MutableMapping)

from flask import Flask

app = Flask(__name__)

from explainshell.web import views  # noqa: F401, E402
from explainshell import store, config  # noqa: F401, E402

if config.DEBUG:
    from explainshell.web import debugviews  # noqa: F401, E402

app.config.from_object(config)
