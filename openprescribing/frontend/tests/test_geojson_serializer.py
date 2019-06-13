import json

from django.test import TestCase
from django.core.serializers import serialize

from frontend.models import PCT
from api.geojson_serializer import as_geojson_stream


class GeoJSONSerializerTest(TestCase):

    fixtures = ['orgs']

    def test_output_is_the_same_as_core_serializer(self):
        fields = ['name', 'org_type', 'ons_code', 'boundary']
        geo_field = 'boundary'
        queryset = PCT.objects.all()
        expected_json = serialize(
            'geojson',
            queryset,
            geometry_field=geo_field,
            fields=fields
        )
        stream = as_geojson_stream(
            queryset.values(*fields),
            geometry_field=geo_field
        )
        expected = json.loads(expected_json)
        actual = json.loads(''.join(stream))
        self.assertEqual(expected, actual)
