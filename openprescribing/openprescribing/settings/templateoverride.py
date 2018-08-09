"""Setting to temporarily override template path."""

from os.path import join, normpath
from .production import *


overrides = normpath(join(SITE_ROOT, 'template_overrides'))
TEMPLATES[0]['DIRS'].insert(0, overrides)
