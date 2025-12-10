# miniup/settings/__init__.py
"""
Settings package for miniup project.
Import the appropriate settings based on environment.
"""

import os

environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .prod import *
else:
    from .dev import *
