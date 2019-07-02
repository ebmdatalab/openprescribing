"""
Infer boundaries for practices from their locations using a Voronoi partition
(i.e. assign each point in the country to its closest practice)

These boundaries have no real meaning but they're easy enough to explain and
they allow us to render plausible-looking maps for arbitrary collections of
practices.

The boundaries are clipped at the national border to stop them extending into
the sea -- or Wales -- and generally looking ridiculous.
"""
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Func
from django.contrib.gis.db.models import Collect, Union
from django.contrib.gis.geos import GEOSGeometry
from django.db import connection, transaction

from frontend.models import Practice, PCT


NATIONAL_BOUNDARY_FILE = os.path.join(
    settings.REPO_ROOT, 'openprescribing/media/geojson/england-boundary.geojson'
)


class Command(BaseCommand):

    help = __doc__

    def handle(self, *args, **options):
        infer_practice_boundaries()


def infer_practice_boundaries():
    practices = (
        Practice.objects
        .filter(location__isnull=False, setting=4)
        .exclude(
            status_code__in=(
                Practice.STATUS_RETIRED,
                Practice.STATUS_DORMANT,
                Practice.STATUS_CLOSED
            )
        )
    )
    partition = (
        practices
        .aggregate(
            voronoi=Func(Collect('location'), function='ST_VoronoiPolygons')
        )
        ['voronoi']
    )
    national_boundary = get_national_boundary()
    practice_regions = get_practice_code_to_region_map(partition, national_boundary)
    with transaction.atomic():
        for practice in practices:
            practice.boundary = practice_regions[practice.code]
            practice.save(update_fields=['boundary'])


def get_practice_code_to_region_map(regions, clip_boundary):
    with connection.cursor() as cursor:
        return _get_practice_code_to_region_map(cursor, regions, clip_boundary)


def _get_practice_code_to_region_map(cursor, regions, clip_boundary):
    """
    Return a dict mapping practice codes to the region in `regions` in which
    they're located, with returned regions clipped to `clip_boundary`
    """
    cursor.execute(
        'CREATE TEMPORARY TABLE regions (original GEOMETRY, clipped GEOMETRY)'
    )
    for region in regions:
        clipped = region.intersection(clip_boundary)
        # This is a workaround for the error "Relate Operation called with a
        # LWGEOMCOLLECTION type" which happens when clipped boundaries end up
        # including things which aren't polygons (i.e. points or lines) and we
        # then try to do ST_Contains queries on them. Generating a zero-width
        # buffer causes all non-polygons to get dropped. See:
        # https://lists.osgeo.org/pipermail/postgis-users/2008-August/020740.html
        clipped = clipped.buffer(0.0)
        if clipped.empty:
            raise RuntimeError(
                """
                Clipped region is empty. This means we have a practice located
                entirely outside the national boundary (as determined by
                aggregating all CCG boundaries) so probably there's some dodgy
                data somewhere.
                """
            )
        cursor.execute(
            'INSERT INTO regions (original, clipped) VALUES (%s, %s)',
            [region.ewkb, clipped.ewkb]
        )
    cursor.execute('CREATE INDEX regions_idx ON regions USING GIST (original)')
    cursor.execute('ANALYSE regions')
    # We match practices to regions using the original, unclipped boundary.
    # This allows us to handle the case that a practice lies just outside its
    # clipped boundary due to imprecision in the geographic data.
    cursor.execute(
        """
        SELECT
          p.code,
          r.clipped
        FROM
          frontend_practice AS p
        JOIN
          regions AS r
        ON
          ST_Contains(r.original, p.location)
        """
    )
    return dict(cursor.fetchall())


def get_national_boundary():
    # In theory there's a `geos.fromfile` method, but it doesn't work
    with open(NATIONAL_BOUNDARY_FILE, 'rb') as f:
        contents = f.read()
    return GEOSGeometry(contents)


# This function is left in place in case we ever want to update the boundary
# file, which we shouldn't need to under ordinary circumstances.  The reason we
# use a static file rather than dynamically generating the boundary from CCG
# data each time is that we can't always guarantee to have complete CCG
# boundary data and we don't want that to prevent us from importing practice
# data
def update_national_boundary_file():
    """
    Generate a national boundary by joining together all CCG boundaries and
    write it to disk

    Run with:
      echo 'import frontend.management.commands.infer_practice_boundaries as c;' \
        'c.update_national_boundary_file()' \
        | ./manage.py shell
    """
    ccgs_without_boundary = PCT.objects.filter(
        org_type='CCG', close_date__isnull=True, boundary__isnull=True
    )
    if ccgs_without_boundary.exists():
        raise RuntimeError(
            """
            Some active CCGs missing boundary data, meaning we can't reliably
            synthesize a national boundary by aggregating CCGs
            """
        )
    boundary = (
        PCT.objects
        .filter(boundary__isnull=False)
        .aggregate(boundary=Union('boundary'))
        ['boundary']
    )
    with open(NATIONAL_BOUNDARY_FILE, 'wb') as f:
        f.write(boundary.geojson)
