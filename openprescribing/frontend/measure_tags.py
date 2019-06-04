import json
import os.path


def _load_measure_tags(filename):
    with open(filename) as f:
        tags = json.load(f)
    for tag_name, tag_details in tags.items():
        if isinstance(tag_details.get('description'), list):
            tag_details['description'] = ''.join(tag_details['description'])
    return tags


MEASURE_TAGS = _load_measure_tags(
    os.path.join(os.path.dirname(__file__), '../common/measure_tags.json'))
