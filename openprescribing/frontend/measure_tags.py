import json
import os.path
from functools import partial

from django.conf import settings
from django.utils.functional import SimpleLazyObject

from frontend.models import Measure


def _load_measure_tags(path):
    with open(path) as f:
        tags = json.load(f)
    for tag_name, tag_details in tags.items():
        if isinstance(tag_details.get('description'), list):
            tag_details['description'] = ' '.join(
                line.strip() for line in tag_details['description']
            )
        tag_details['count'] = (
            Measure.objects.filter(tags__contains=[tag_name]).count()
        )
    return tags


def _lazy_load_measure_tags(path):
    return SimpleLazyObject(partial(_load_measure_tags, path))


MEASURE_TAGS = _lazy_load_measure_tags(
    os.path.join(settings.APPS_ROOT, 'common', 'measure_tags.json')
)
