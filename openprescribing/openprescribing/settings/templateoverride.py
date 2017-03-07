"""Setting to temporarily override template path."""
from __future__ import absolute_import
from os.path import join, normpath
from .production import *


overrides = normpath(join(SITE_ROOT, 'template_overrides'))
TEMPLATES[0]['DIRS'].insert(0, overrides)
print TEMPLATES
