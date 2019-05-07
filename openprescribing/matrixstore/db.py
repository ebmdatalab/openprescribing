"""
This module provides the primary interface between the MatrixStore and the rest
of the application.

It makes use of the assumption that data is static throughout the runtime of
the application and therefore any data imports or updates will require an
application restart before they take effect.
"""
from django.conf import settings
from django.utils.lru_cache import lru_cache

from frontend.models import Practice

from .grouper import Grouper
from .connection import MatrixStore


# Create a memoize decorator (i.e. a decorator which caches the return value
# for a given set of arguments). Here `maxsize=None` means "don't apply any
# cache eviction, just keep values for ever"
memoize = lru_cache(maxsize=None)


@memoize
def get_db():
    """
    Return a singleton instance of the current live version of the MatrixStore
    """
    return MatrixStore.from_file(settings.MATRIXSTORE_LIVE_FILE)


@memoize
def group_by(org_type):
    """
    Return a "grouper" function which will group the rows of a practice level
    matrix by the supplied `org_type`

    Note that the function is memoized so that if org relationships are changed
    in the database then the application will need to be restarted to see the
    changes.
    """
    # For practice level data we return a grouper that does nothing, but
    # otherwise acts like a normal grouper so we don't need to treat ungrouped
    # data differently
    if org_type == 'practice':
        return NoOpGrouper(get_db().practice_offsets)
    # Get the mapping from practice codes to IDs of groups
    elif org_type == 'ccg':
        mapping = _practice_to_ccg_map()
    elif org_type == 'stp':
        mapping = _practice_to_stp_map()
    elif org_type == 'regional_team':
        mapping = _practice_to_regional_team_map()
    elif org_type == 'all_practices':
        mapping = _all_practices_map()
    else:
        raise ValueError('Unhandled org_type: ' + org_type)
    return Grouper(
        (offset, mapping[practice_code])
        for practice_code, offset in get_db().practice_offsets.items()
        if practice_code in mapping
    )


class NoOpGrouper(object):
    """
    Grouper that leaves data at practice level (i.e. does no grouping at all)
    but which has the same interface as a normal grouper and so can help avoid
    branching in parts of the codebase where we may or may not need to group
    """

    def __init__(self, practice_offsets):
        self.offsets = practice_offsets
        self.ids = sorted(
            practice_offsets.keys(),
            key=practice_offsets.__getitem__
        )

    def __call__(self, matrix):
        return matrix


def _practice_to_ccg_map():
    return dict(
        Practice.objects
        .filter(ccg__org_type='CCG')
        .values_list('code', 'ccg_id')
    )


def _practice_to_stp_map():
    return dict(
        Practice.objects
        .filter(ccg__stp_id__isnull=False)
        .values_list('code', 'ccg__stp_id')
    )


def _practice_to_regional_team_map():
    return dict(
        Practice.objects
        .filter(ccg__regional_team_id__isnull=False)
        .values_list('code', 'ccg__regional_team_id')
    )


def _all_practices_map():
    """
    Maps every practice (standard GP practices and others) which belongs to a
    CCG to a single group, which we give of ID of None as it doesn't really
    need an ID
    """
    return {
        code: None
        for code in Practice.objects
        .filter(ccg_id__isnull=False)
        .values_list('code', flat=True)
    }
