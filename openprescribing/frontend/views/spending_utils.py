from __future__ import division

from django.db import connection
from django.db.models import Max
from django.db.models.functions import Coalesce

from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as parse_date

from frontend.models import NCSOConcession, Presentation
from matrixstore.db import get_db, get_row_grouper
from matrixstore.labelled_array import LabelledArray


# The tariff (or concession) price is not what actually gets paid as each CCG
# will have some kind of discount with the dispenser. However the average
# discount has been pretty consistent over the years so we use that here.
NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE = 7.2


def ncso_spending_for_entity(entity, entity_type, num_months, current_month=None):
    org_type, org_id = _get_org_type_and_id(entity, entity_type)
    end_date = NCSOConcession.objects.aggregate(Max("date"))["date__max"]
    # In practice, we always have at least one NCSOConcession object but we
    # need to handle the empty case in testing
    if not end_date:
        return []
    start_date = end_date - relativedelta(months=num_months - 1)
    last_prescribing_date = parse_date(get_db().dates[-1]).date()
    _, tariff_costs, extra_costs = _get_concession_cost_matrices(
        start_date, end_date, org_type, org_id
    )
    # Sum together costs over all presentations (i.e. all rows)
    tariff_costs = tariff_costs.sum_rows()
    extra_costs = extra_costs.sum_rows()
    results = []
    for date_str in extra_costs.labels:
        date = parse_date(date_str).date()
        if extra_costs[date_str] == 0:
            continue
        entry = {
            "month": date,
            "tariff_cost": float(tariff_costs[date_str]),
            "additional_cost": float(extra_costs[date_str]),
            "is_estimate": date > last_prescribing_date,
            "last_prescribing_date": last_prescribing_date,
        }
        if current_month is not None:
            entry["is_incomplete_month"] = date >= current_month
        results.append(entry)
    return results


def ncso_spending_breakdown_for_entity(entity, entity_type, month):
    org_type, org_id = _get_org_type_and_id(entity, entity_type)
    quantities, tariff_costs, extra_costs = _get_concession_cost_matrices(
        month, month, org_type, org_id
    )
    # We sum across columns (i.e. dates) to get the totals over time for each
    # BNF code.
    quantities = quantities.sum_columns()
    tariff_costs = tariff_costs.sum_columns()
    extra_costs = extra_costs.sum_columns()
    bnf_codes = quantities.labels
    names = _get_names_for_bnf_codes(bnf_codes)
    results = []
    for bnf_code in bnf_codes:
        results.append(
            (
                bnf_code,
                names[bnf_code],
                int(quantities[bnf_code]),
                float(tariff_costs[bnf_code]),
                float(extra_costs[bnf_code]),
            )
        )
    # Sort by "additional cost" column, descending
    results.sort(key=lambda i: i[4], reverse=True)
    return results


def _get_org_type_and_id(entity, entity_type):
    if entity_type == "all_england":
        org_type = "all_practices"
        org_id = None
    else:
        org_type = entity_type if entity_type != "CCG" else "ccg"
        org_id = entity.code
    return org_type, org_id


def _get_names_for_bnf_codes(bnf_codes):
    """
    Given a list of BNF codes return a dictionary mapping those codes to their
    DM&D names
    """
    name_map = Presentation.objects.filter(bnf_code__in=bnf_codes).values_list(
        "bnf_code", Coalesce("dmd_name", "name")
    )
    return dict(name_map)


def _get_concession_cost_matrices(min_date, max_date, org_type, org_id):
    """
    Given a date range (inclusive) and an organisation return three
    LaballedArrays (of the same shape) detailing all spending affected by price
    concessions during the period.

              quantities: LabelledArray giving, for each BNF code and date, the
                          quantity prescribed of that presentation by the
                          specified organisation

            tariff_costs: LabelledArray giving, for each BNF code and date, the
                          cost of the above prescriptions at standard Drug
                          Tariff prices

             extra_costs: LabelledArray giving, for each BNF code and date, the
                          cost increase due to price concessions

    """
    tariff_prices, price_increases = _get_concession_price_matrices(min_date, max_date)
    bnf_codes = tariff_prices.row_labels
    dates = tariff_prices.column_labels
    quantities = _get_prescribed_quantity_matrix(bnf_codes, dates, org_type, org_id)
    # If the dates extend beyond the latest date for which we have prescribing
    # data then we just project the last month forwards (e.g. if we only have
    # prescriptions up to March but have price concessions up to May then we just
    # assume the same quantities as for March were prescribed in April and May).
    projected_quantities = quantities.remap_columns(dates, project_forward=True)
    tariff_costs = tariff_prices * projected_quantities
    extra_costs = price_increases * projected_quantities
    return quantities, tariff_costs, extra_costs


def _get_prescribed_quantity_matrix(bnf_codes, org_type, org_id):
    """
    Given a list of BNF codes and an organisation (specified by its type and
    ID) return a LabelledArray indexed by BNF code and date, giving prescribed
    quantities.
    """
    group_by_org = get_row_grouper(org_type)
    db = get_db()
    quantities = LabelledArray((bnf_codes, db.dates), integer=True)
    for bnf_code, quantity in _get_quantities_for_bnf_codes(db, bnf_codes):
        quantity_for_org = group_by_org.sum_one_group(quantity, org_id)
        quantities.set_row(bnf_code, quantity_for_org)
    return quantities


def _get_quantities_for_bnf_codes(db, bnf_codes):
    """
    Return the prescribed quantity matrices for the given list of BNF codes
    """
    return db.query(
        """
        SELECT
          bnf_code, quantity
        FROM
          presentation
        WHERE
          quantity IS NOT NULL AND bnf_code IN ({})
        """.format(
            ",".join(["?"] * len(bnf_codes))
        ),
        bnf_codes,
    )


def _get_concession_price_matrices(min_date, max_date):
    """
    Given a date range (inclusive) return two LaballedArrays (of the same
    shape) detailing all NCSO price concessions during the period:

           tariff_prices: LabelledArray giving, for each BNF code and date, the
                          standard Drug Tariff price for that presentation (in
                          pounds-per-unit)

         price_increases: LabelledArray giving, for each BNF code and date, the
                          price increase due to concessions (in
                          pounds-per-unit)

    """
    # Fetch list of concessions and associated tariff prices from Postgres
    concessions = _get_concession_prices(min_date, max_date)
    # Construct the BNF code and date indices we need to store these prices in
    # matrix form
    dates = _get_dates_in_range(min_date, max_date)
    bnf_codes = {concession[1] for concession in concessions}
    tariff_prices = LabelledArray((bnf_codes, dates))
    price_increases = LabelledArray.zeros_like(tariff_prices)
    # Loop over the concessions and write them into the matrices
    for date, bnf_code, tariff_price, price_increase, quantity_per_pack in concessions:
        index = (bnf_code, str(date))
        # Convert prices from per-pack into per-unit
        tariff_price = tariff_price / quantity_per_pack
        price_increase = price_increase / quantity_per_pack
        # Price concessions are defined at the product-pack level but we only
        # have prescribing data at product level. Occasionally there are
        # multiple simultaneous concessions for a given product with different
        # implied prices-per-unit for different pack sizes. As we can't know
        # from our data which pack size was dispensed we just use the highest
        # per-unit price.
        if price_increase > price_increases[index]:
            price_increases[index] = price_increase
            tariff_prices[index] = tariff_price
    # Apply the national average discount to get a better approximation of the
    # actual price paid, and while we're at it convert from pence to pounds to
    # make later calcuations easier
    discount_factor = (100 - NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE) / (100 * 100)
    tariff_prices *= discount_factor
    price_increases *= discount_factor
    return tariff_prices, price_increases


def _get_dates_in_range(date_start, date_end):
    date = date_start
    while date <= date_end:
        yield date
        date = date + relativedelta(months=1)


def _get_concession_prices(min_date, max_date):
    """
    Gets all NCSO price concessions in the given period (where both min and max
    are inclusive), returning an iterable of tuples of the form:

                     date: Datetime instance giving the month of the concession

                 bnf_code: Presentation to which concession is applied

             tariff_price: Standard drug tariff price in pence-per-pack

           price_increase: The *extra* cost of the price concession (i.e. the
                           cost above the tariff price) in pence-per-pack

        quantity_per_pack: Divide prescribed quantity by this to get number of
                           packs

    Note that because concessions are defined at the product-pack level and BNF
    codes refer to products it's possible to have multiple different concession
    prices for the same (BNF code, date) pair.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
              ncso.date AS date,
              vmpp.bnf_code AS bnf_code,
              tariff.price_pence AS tariff_price,
              COALESCE(ncso.price_pence - tariff.price_pence, 0) AS price_increase,
              CASE WHEN presentation.quantity_means_pack THEN
                  1
                ELSE
                  vmpp.qtyval
                END
              AS quantity_per_pack
            FROM
              frontend_ncsoconcession AS ncso
            JOIN
              frontend_tariffprice AS tariff
            ON
              ncso.vmpp_id = tariff.vmpp_id AND ncso.date = tariff.date
            JOIN
              dmd2_vmpp AS vmpp
            ON
              vmpp.vppid=ncso.vmpp_id
            JOIN
              frontend_presentation AS presentation
            ON
              presentation.bnf_code = vmpp.bnf_code
            WHERE
              ncso.date >= %(min_date)s AND ncso.date <= %(max_date)s
            """,
            {"min_date": min_date, "max_date": max_date},
        )
        return cursor.fetchall()
