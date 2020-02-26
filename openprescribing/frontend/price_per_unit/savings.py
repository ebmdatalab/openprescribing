import numpy

from matrixstore.db import get_db, get_row_grouper
from matrixstore.matrix_ops import get_submatrix, zeros_like
from matrixstore.sql_functions import MatrixSum

from .substitution_sets import get_substitution_sets


# Defines how we determine the target PPU against which savings are calculated.
# We want to know which set of practices we are comparing with and which
# centile over those practices we are targeting.
CONFIG_TARGET_CENTILE = 10
# Note this is "standard_practice" rather than "practice" as we only want to
# include setting 4 practices (i.e. ordinary GP practices)
CONFIG_TARGET_PEER_GROUP = "standard_practice"

# Savings are calculated in two stages: first at the practice level, and then
# aggregated up into organisation savings. At both stages we apply a minimum
# threshold such that savings below that threshold are treated as zero. This is
# particularly important at practice level as it prevents "negative savings"
# from practices already performing better than the target PPU.
# (Note: all values in pence)
CONFIG_MIN_SAVINGS_FOR_ORG_TYPE = {
    "practice": 10 * 100,
    "ccg": 200 * 100,
    # Picked somewhat arbitrarily based on the CCG limit
    "all_standard_practices": 50000 * 100,
}


def get_all_savings_for_orgs(date, org_type, org_ids):
    """
    Get all available savings through presentation switches for the given orgs
    """
    results = []
    for generic_code in get_substitution_sets().keys():
        savings = get_savings_for_orgs(generic_code, date, org_type, org_ids)
        results.extend(savings)
    results.sort(key=lambda i: i["possible_savings"], reverse=True)
    return results


def get_savings_for_orgs(generic_code, date, org_type, org_ids):
    """
    Get available savings for the given orgs within a particular class of
    substitutable presentations
    """
    substitution_set = get_substitution_sets()[generic_code]

    quantities, net_costs = get_quantities_and_net_costs_at_date(
        get_db(), substitution_set, date
    )

    group_by_org = get_row_grouper(org_type)
    quantities_for_orgs = group_by_org.sum(quantities, org_ids)
    # Bail early if none of the orgs have any relevant prescribing
    if not numpy.any(quantities_for_orgs):
        return []
    net_costs_for_orgs = group_by_org.sum(net_costs, org_ids)
    ppu_for_orgs = net_costs_for_orgs / quantities_for_orgs

    target_ppu = get_target_ppu(
        quantities,
        net_costs,
        group_by_org=get_row_grouper(CONFIG_TARGET_PEER_GROUP),
        target_centile=CONFIG_TARGET_CENTILE,
    )
    practice_savings = get_savings(
        quantities,
        net_costs,
        target_ppu,
        min_saving=CONFIG_MIN_SAVINGS_FOR_ORG_TYPE["practice"],
    )

    savings_for_orgs = group_by_org.sum(practice_savings, org_ids)
    min_threshold = CONFIG_MIN_SAVINGS_FOR_ORG_TYPE[org_type]

    results = [
        {
            "date": date,
            "org_id": org_id,
            "price_per_unit": ppu_for_orgs[offset, 0] / 100,
            "possible_savings": savings_for_orgs[offset, 0] / 100,
            "quantity": quantities_for_orgs[offset, 0],
            "lowest_decile": target_ppu[0] / 100,
            "presentation": substitution_set.id,
            "formulation_swap": substitution_set.formulation_swaps,
            "name": substitution_set.name,
        }
        for offset, org_id in enumerate(org_ids)
        if savings_for_orgs[offset, 0] >= min_threshold
    ]

    results.sort(key=lambda i: i["possible_savings"], reverse=True)
    return results


def get_total_savings_for_org(date, org_type, org_id):
    """
    Get total available savings through presentation switches for the given org
    """
    group_by_org = get_row_grouper(org_type)
    totals = get_total_savings_for_org_type(
        db=get_db(),
        substitution_sets=get_substitution_sets(),
        date=date,
        group_by_org=group_by_org,
        min_saving=CONFIG_MIN_SAVINGS_FOR_ORG_TYPE[org_type],
        practice_group_by_org=get_row_grouper(CONFIG_TARGET_PEER_GROUP),
        target_centile=CONFIG_TARGET_CENTILE,
        practice_min_saving=CONFIG_MIN_SAVINGS_FOR_ORG_TYPE["practice"],
    )
    offset = group_by_org.offsets[org_id]
    return totals[offset, 0] / 100


def get_total_savings_for_org_type(
    db,
    substitution_sets,
    date,
    group_by_org,
    min_saving,
    practice_group_by_org,
    target_centile,
    practice_min_saving,
):
    """
    Return a matrix giving total savings for all orgs of a given type

    This duplicates some of the logic in `get_savings_for_orgs` but it gives us
    much better caching behaviour to calculate savings for all orgs of a given
    type together in a single, cacheable matrix than it does to do them one by
    one.

    Because we want this function to be cacheable it needs to touch no global
    state and have eveything passed into it, hence the slightly convoluted call
    signature.
    """
    totals = None
    for substitution_set in substitution_sets.values():
        quantities, net_costs = get_quantities_and_net_costs_at_date(
            db, substitution_set, date
        )
        target_ppu = get_target_ppu(
            quantities,
            net_costs,
            group_by_org=practice_group_by_org,
            target_centile=target_centile,
        )
        practice_savings = get_savings(
            quantities, net_costs, target_ppu, min_saving=practice_min_saving
        )
        savings_for_orgs = group_by_org.sum(practice_savings)
        savings_above_threshold = savings_for_orgs >= min_saving
        if totals is None:
            totals = zeros_like(savings_for_orgs)
        numpy.add(totals, savings_for_orgs, out=totals, where=savings_above_threshold)
    assert totals is not None
    return totals


def get_target_ppu(quantities, net_costs, group_by_org, target_centile):
    """
    Calculate the price-per-unit achieved by the organisation (as defined by
    `group_by_org`) at the target centile
    """
    quantities = group_by_org.sum(quantities)
    net_costs = group_by_org.sum(net_costs)
    ppu = net_costs / quantities
    target_ppu = numpy.nanpercentile(ppu, axis=0, q=target_centile)
    return target_ppu


def get_savings(quantities, net_costs, target_ppu, min_saving):
    """
    For a given target price-per-unit calculate how much would be saved by each
    practice if they had achieved that price-per-unit
    """
    target_costs = quantities * target_ppu
    savings = net_costs - target_costs
    # Remove all savings that are under the minimum threshold (which includes
    # any negative savings from practices already achieving better than the
    # target)
    savings_under_threshold = savings < min_saving
    savings[savings_under_threshold] = 0
    return savings


def get_quantities_and_net_costs_at_date(db, substitution_set, date):
    """
    Sum quantities and net costs over the supplied list of BNF codes for just
    the specified date.
    """
    bnf_codes = substitution_set.presentations
    date_column = db.date_offsets[date]
    date_slice = slice(date_column, date_column + 1)

    results = db.query(
        """
        SELECT
          quantity, net_cost
        FROM
          presentation
        WHERE
          bnf_code IN ({})
        """.format(
            ",".join("?" * len(bnf_codes))
        ),
        bnf_codes,
    )

    quantity_sum = MatrixSum()
    net_cost_sum = MatrixSum()
    for quantity, net_cost in results:
        quantity_sum.add(get_submatrix(quantity, cols=date_slice))
        net_cost_sum.add(get_submatrix(net_cost, cols=date_slice))
    return quantity_sum.value(), net_cost_sum.value()
