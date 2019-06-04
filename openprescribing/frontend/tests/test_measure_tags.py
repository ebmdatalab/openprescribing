from django.test import TestCase

from frontend.measure_tags import _load_measure_tags


class TestMeasureTags(TestCase):
    def test_descriptions(self):
        path = 'frontend/tests/fixtures/measure_tags.json'
        tags = _load_measure_tags(path)
        self.assertEqual(
            tags['tag1']['description'],
            'This description is a string'
        )
        self.assertEqual(
            tags['tag2']['description'],
            'This description is an array'
        )
