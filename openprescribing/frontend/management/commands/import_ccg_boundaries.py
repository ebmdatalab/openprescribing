"""Import CCG boundaries

This is currently a semi-manual process. Mattia Ficarelli at NHSX has written a script
for us (see below) which automates the download, but this has not yet been integrated
into our data fetching pipeline.
https://github.com/ebmdatalab/fetch-boundaries
"""

import warnings

from django import VERSION as DJANGO_VERSION
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.gdal import GDAL_VERSION
from django.contrib.gis.utils import LayerMapping
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F

from frontend.models import PCT


# This has to be available as a standalone function as it's imported by a migration
def set_centroids():
    PCT.objects.filter(boundary__isnull=False).update(centroid=Centroid(F("boundary")))


class Command(BaseCommand):
    help = "Imports CCG boundaries from mapinfo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--filename", help="Should point to a filename like `CCG_BSC_Apr2015.TAB`"
        )

    def handle(self, *args, **options):
        # Without this check the command will run without error, but the imported shapes
        # will have inverted axis order
        if DJANGO_VERSION[:2] < (3, 1):
            if GDAL_VERSION[0] > 2:
                raise RuntimeError(
                    "Django <3.1 is not compatible with GDAL 3, see:\n"
                    "https://github.com/ebmdatalab/openprescribing/issues/3263"
                )
        else:
            warnings.warn(
                "GDAL_VERSION check above can be removed as we're running Django >= 3.1"
            )

        layer_mapping = {"code": "ods_code", "boundary": "geometry"}
        lm = LayerMapping(PCT, options["filename"], layer_mapping, transform=True)
        with transaction.atomic():
            for feature in lm.layer:
                fields = lm.feature_kwargs(feature)
                PCT.objects.filter(code=fields["code"]).update(
                    boundary=fields["boundary"]
                )
            set_centroids()
