from django.test import TestCase

from frontend.tests.data_factory import DataFactory

from frontend.measure_tags import _lazy_load_measure_tags


class TestMeasureTags(TestCase):
    path = 'frontend/tests/fixtures/measure_tags.json'

    def test_counts(self):
        factory = DataFactory()
        factory.create_measure(tags=['tag1'])
        factory.create_measure(tags=['tag1', 'tag2'])

        tags = _lazy_load_measure_tags(self.path)
        self.assertEqual(tags['tag1']['count'], 2)
        self.assertEqual(tags['tag2']['count'], 1)

    def test_descriptions(self):
        tags = _lazy_load_measure_tags(self.path)
        self.assertEqual(
            tags['tag1']['description'],
            'This description is a string'
        )
        self.assertEqual(
            tags['tag2']['description'],
            'This description is an array'
        )
