"""Import CCG boundaries from a manually-curated input file.

I've given up bothering automating the process of importing
boundaries, as they rarely change, and every time they do, a new
format is used. Furthemore, CCGs are likely to become subordinate to
STPs as the key level of aggregated analysis over the next 12 months
in any case. See issue #490 for some discussion, for example.

So, here are some notes about how I did it manually this time.

This command expects a file of boundaries in MapInfo format, with a
single attribute column indicating the CCG code associated with the
geometry.  The value corresponding with the key `code` in the variable
`layer_mapping` (below) should be the name of that attribute column in
the source data.

Here's what I did:

* Download "generalised" shapefile from
  [here](http://geoportal.statistics.gov.uk/datasets/clinical-commissioning-groups-april-2017-super-generalised-clipped-boundaries-in-england-v4)
* Download CSV of CCG code mappings from
  [here](http://geoportal.statistics.gov.uk/datasets/lower-layer-super-output-area-2011-to-clinical-commissioning-group-to-local-authority-district-april-2017-lookup-in-england-version-4/data?where=CCG17CDH%20like%20%27%2514L%25%27)
* Open the shapefile in QGIS (I used version 2.14.11):
  * Create a new project
  * Add a shapefile layer
    * Browse to the downloaded zip fill
* Add "delimited text file" layer ("no geometry" option) for the code
  mappings CSC
* Right click - properties - join - join the two layers on `ccg17cd` -
  include only the attribute `ccg17cdh` from the CSV file (these are
  the short CCG codes)
* Save the CCG layer as a shapefile (so you can edit it; you can't
  edit the zip one)
* Click pencil to enter edit mode
* Go to layer properties, remove all attributes except the CCG code one
* Right click the layer - save as MapInfo TAB. If you are doing this
  manually, it doesn't matter where you save it. If you have found
  this comment during a pipeline import, then place the MapInfo files
  in the location specified by the manual fetch process.  If doing
  this manually, import the file with:

       python manage.py import_ccg_boundaries --filename /tmp/foo.tab

   (but ensure the code field in `layer_mapping` below matches the
   name of the exported attribute column - in this case it was
   `Lower_Laye`; you can examine the column names with `ogrinfo`)
* Don't forget to import CCG names after running this command (I ran
  `python manage.py import_org_names --ccg
  ~/openprescribing-data/data/ccg_details/2017_06/eccg.csv)

"""

import sys
from django.core.management.base import BaseCommand
from django.contrib.gis.db.models.functions import Centroid
from django.contrib.gis.utils import LayerMapping
from frontend.models import PCT


def set_centroids():
    for pct in PCT.objects.filter(boundary__isnull=False).annotate(
            centroid_annotation=Centroid('boundary')):
        pct.centroid = pct.centroid_annotation
        pct.save()


class Command(BaseCommand):
    args = ''
    help = 'Imports CCG boundaries from mapinfo. Note that you should '
    help += 'run this BEFORE importing CCG names, as this creates new '
    help += 'records in the database rather than updating existing ones.'
    help += 'Read notes in the source code before proceeding'

    def add_arguments(self, parser):
        parser.add_argument(
            '--filename',
            help='Should point to a filename like `CCG_BSC_Apr2015.TAB`'
        )

    def handle(self, *args, **options):
        layer_mapping = {
            'code': 'Lower_Laye',
            'boundary': 'Unknown',
        }
        lm = LayerMapping(PCT, options['filename'],
                          layer_mapping, transform=True)
        lm.save(strict=True)
        set_centroids()
