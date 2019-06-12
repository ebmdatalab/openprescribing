"""
Django's built-in GeoJSON serializer (django.core.serializers.geojson) will
only serialize fields defined on the model, so if you want to include results
calculated on a QuerySet using e.g. `annotate` or `aggregate` then you're out
of luck.

Below is a dirt-simple implementation of a GeoJSON convertor which accepts
dictionaries with arbitrary keys.
"""
from django.contrib.gis.gdal import CoordTransform, SpatialReference


def as_geojson(dictionaries, geometry_field='geometry', srid=4326):
    """
    Convert an iterable of dictionaries into a GeoJSON structure
    """
    converter = GeoJSONConvertor(geometry_field, srid)
    return {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:{:d}".format(srid)
            }
        },
        "features": [converter.convert_dict(d) for d in dictionaries]
    }


class GeoJSONConvertor(object):

    def __init__(self, geometry_field, srid):
        self.geometry_field = geometry_field
        self.srid = srid
        self._transform_cache = {}

    def convert_dict(self, d):
        geometry = d.pop(self.geometry_field, None)
        if geometry is not None:
            geometry = self.as_geojson(geometry)
        return {
            'geometry': geometry,
            'type': 'Feature',
            'properties': d
        }

    def as_geojson(self, geometry):
        if geometry.srid != self.srid:
            if geometry.srid not in self._transform_cache:
                srs = SpatialReference(self.srid)
                self._transform_cache[geometry.srid] = CoordTransform(geometry.srs, srs)
            geometry.transform(self._transform_cache[geometry.srid])
        # This seems kind of bad, but it's what Django's geojson serializer does
        return eval(geometry.geojson)
