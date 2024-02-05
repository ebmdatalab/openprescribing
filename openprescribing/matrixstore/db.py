"""
This module provides the primary interface between the MatrixStore and the rest
of the application.

It makes use of the assumption that data is static throughout the runtime of
the application and therefore any data imports or updates will require an
application restart before they take effect.
"""

from functools import lru_cache

from django.conf import settings
from frontend.models import Practice

from .connection import MatrixStore

# We don't raise this directly here but consumers of the module should be able
# to catch this exception without having to import from `row_grouper` directly,
# which violates the abstraction
from .row_grouper import RowGrouper
from .row_grouper import UnknownGroupError as UnknownOrgIDError  # noqa

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


def org_has_prescribing(org_type, org_id):
    """
    Return whether this org has any prescribing data associated with it
    """
    row_grouper = get_row_grouper(org_type)
    return org_id in row_grouper.offsets


def latest_prescribing_date():
    """
    Return the latest date for which we have prescribing data
    """
    return get_db().dates[-1]


@memoize
def get_row_grouper(org_type):
    """
    Return a "row grouper" function which will group the rows of a practice
    level matrix by the supplied `org_type`

    Note that the function is memoized so that if org relationships are changed
    in the database then the application will need to be restarted to see the
    changes.
    """
    # Get the mapping from practice codes to IDs of groups
    if org_type == "practice":
        mapping = _practice_to_practice_map()
    elif org_type == "standard_practice":
        mapping = _practice_to_standard_practice_map()
    elif org_type == "ccg":
        mapping = _practice_to_ccg_map()
    elif org_type == "standard_ccg":
        mapping = _standard_practice_to_ccg_map()
    elif org_type == "pcn":
        mapping = _practice_to_pcn_map()
    elif org_type == "stp":
        mapping = _practice_to_stp_map()
    elif org_type == "regional_team":
        mapping = _practice_to_regional_team_map()
    elif org_type == "all_practices":
        mapping = _group_all(_practice_to_practice_map())
    elif org_type == "all_standard_practices":
        mapping = _group_all(_practice_to_standard_practice_map())
    else:
        raise ValueError("Unhandled org_type: " + org_type)
    return RowGrouper(
        (offset, mapping[practice_code])
        for practice_code, offset in get_db().practice_offsets.items()
        if practice_code in mapping
    )


def _practice_to_practice_map():
    # For practice level data we just map each practice code to itself. This
    # means that we're not really doing any "grouping" in a meaningful sense,
    # but it simplifies the code by keeping things consistent.
    return {
        practice_code: practice_code
        for practice_code in get_db().practice_offsets.keys()
    }


def _practice_to_standard_practice_map():
    # Again we map practices to themselves, but this time only standard GP
    # practices which belong to a CCG
    return {
        practice_code: practice_code
        for practice_code in Practice.objects.filter(
            setting=4, ccg__org_type="CCG"
        ).values_list("code", flat=True)
    }


def _practice_to_ccg_map():
    # Map practices to their CCGs including non-standard (i.e. not setting 4)
    # practices
    return dict(
        Practice.objects.filter(ccg__org_type="CCG").values_list("code", "ccg_id")
    )


def _standard_practice_to_ccg_map():
    # Map practices to their CCGs but only include standard practices
    return dict(
        Practice.objects.filter(ccg__org_type="CCG", setting=4).values_list(
            "code", "ccg_id"
        )
    )


def _practice_to_pcn_map():
    return dict(
        Practice.objects.filter(pcn_id__isnull=False).values_list("code", "pcn_id")
    )


def _practice_to_stp_map():
    return dict(
        Practice.objects.filter(ccg__stp_id__isnull=False).values_list(
            "code", "ccg__stp_id"
        )
    )


def _practice_to_regional_team_map():
    return dict(
        Practice.objects.filter(ccg__regional_team_id__isnull=False).values_list(
            "code", "ccg__regional_team_id"
        )
    )


def _group_all(mapping):
    """
    Maps every practice contained in the supplied mapping to a single entity,
    which we give an ID of None as it doesn't really need an ID
    """
    return {practice_code: None for practice_code in mapping.keys()}
