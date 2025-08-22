import os
from pathlib import Path
from typing import Dict, Any

# Use pathlib for more modern path handling
_currdir = Path(__file__).parent.parent

MANPAGEDIR = str(_currdir / 'manpages')
CLASSIFIER_CUTOFF = 0.7
TOOLSDIR = _currdir / 'tools'

MAN2HTML = str(TOOLSDIR / 'w3mman2html.cgi')

# host to pass into Flask's app.run.
HOST_IP = os.getenv('HOST_IP', None)  # Use None instead of False for clarity
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost')
DEBUG = True

# Type hint the logging configuration for better IDE support
LOGGING_DICT: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': 'application.log',
            'mode': 'a',
        },
    },
    'loggers': {
        'explainshell': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
