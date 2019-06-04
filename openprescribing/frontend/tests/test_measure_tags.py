from django.test import TestCase

from frontend.tests.data_factory import DataFactory

from frontend.measure_tags import _load_measure_tags


class TestMeasureTags(TestCase):
    def test_counts(self):
        factory = DataFactory()
        factory.create_measure(tags=['tag1'])
        factory.create_measure(tags=['tag1', 'tag2'])

        path = 'frontend/tests/fixtures/measure_tags.json'
        tags = _load_measure_tags(path)
        self.assertEqual(tags['tag1']['count'], 2)
        self.assertEqual(tags['tag2']['count'], 1)

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
