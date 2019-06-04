import json
import os.path

from frontend.models import Measure


def _load_measure_tags(filename):
    with open(filename) as f:
        tags = json.load(f)
    for tag_name, tag_details in tags.items():
        if isinstance(tag_details.get('description'), list):
            tag_details['description'] = ' '.join(
                line.strip() for line in tag_details['description']
            )
        tag_details['count'] = Measure.objects.filter(tags__contains=[tag_name]).count()
    return tags


MEASURE_TAGS = _load_measure_tags(
    os.path.join(os.path.dirname(__file__), '../common/measure_tags.json'))
