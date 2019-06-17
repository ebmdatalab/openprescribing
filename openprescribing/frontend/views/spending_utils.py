from django.db import connection
from django.db.models import Max
from datetime import date

from dateutil.relativedelta import relativedelta

from api.view_utils import dictfetchall
from frontend.models import ImportLog, NCSOConcession


# The tariff (or concession) price is not what actually gets paid as each CCG
# will have some kind of discount with the dispenser. However the average
# discount has been pretty consistent over the years so we use that here.
NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE = 7.2


def ncso_spending_for_entity(entity, entity_type, num_months, current_month=None):
    if entity_type.lower() == 'ccg':
        prescribing_table = 'vw__presentation_summary_by_ccg'
        entity_field = 'pct_id'
        entity_condition = entity.code
    elif entity_type == 'practice':
        prescribing_table = 'frontend_prescription'
        entity_field = 'practice_id'
        entity_condition = entity.code
    elif entity_type == 'all_england':
        prescribing_table = 'vw__presentation_summary_by_ccg'
        entity_field = 'frontend_pct.org_type'
        entity_condition = 'CCG'
    else:
        raise ValueError('Unknown entity_type: '+entity_type)
    end_date = NCSOConcession.objects.aggregate(Max('date'))['date__max']
    # In practice, we always have at least one NCSOConcession object but we
    # need to handle the empty case in testing
    if not end_date:
        return []
    start_date = end_date + relativedelta(months=-num_months)
    with connection.cursor() as cursor:
        sql, params = _ncso_spending_query(prescribing_table, start_date, end_date)
        params.update(
            entity_condition=entity_condition
        )
        cursor.execute("""
            SELECT
              month,
              SUM(tariff_cost) AS tariff_cost,
              SUM(additional_cost) AS additional_cost,
              is_estimate,
              %(last_prescribing_date)s AS last_prescribing_date
            FROM
              ({sql}) AS subquery
            JOIN
              frontend_pct ON frontend_pct.code = pct_id
            WHERE
              month > %(start_date)s AND month <= %(end_date)s
              AND {entity_field} = %(entity_condition)s
            GROUP BY
              month, is_estimate
            ORDER BY
              month
            """.format(
                sql=sql, entity_field=entity_field),
            params)
        results = dictfetchall(cursor)
    # Price concessions are released gradually over the course of the month.
    # This means that the numbers for the current month will start off looking
    # low and then gradually increase as more concessions are granted. We want
    # to flag this to the user.
    if current_month is not None:
        for row in results:
            row['is_incomplete_month'] = row['month'] >= current_month
    return results


def ncso_spending_breakdown_for_entity(entity, entity_type, month):
    if entity_type == 'all_england':
        return _ncso_spending_breakdown_for_all_england(month)
    elif entity_type == 'CCG':
        prescribing_table = 'vw__presentation_summary_by_ccg'
        entity_field = 'pct_id'
    elif entity_type == 'practice':
        prescribing_table = 'frontend_prescription'
        entity_field = 'practice_id'
    else:
        raise ValueError('Unknown entity_type: '+entity_type)
    with connection.cursor() as cursor:
        sql, params = _ncso_spending_query(prescribing_table, month, month)
        params.update(
            entity_id=entity.code,
            month=month
        )
        cursor.execute("""
            SELECT
              bnf_code,
              product_name,
              quantity,
              tariff_cost,
              additional_cost
            FROM
              ({sql}) AS subquery
            WHERE
              month=%(month)s AND {entity_field} = %(entity_id)s
            ORDER BY
              additional_cost DESC, tariff_cost DESC
            """.format(
                sql=sql, entity_field=entity_field),
            params)
        return cursor.fetchall()


def _ncso_spending_breakdown_for_all_england(month):
    with connection.cursor() as cursor:
        sql, params = _ncso_spending_query(
            'vw__presentation_summary_by_ccg', month, month)
        params.update(month=month)
        cursor.execute("""
            SELECT
              bnf_code,
              product_name,
              SUM(quantity) AS quantity,
              SUM(tariff_cost) AS tariff_cost,
              SUM(additional_cost) AS additional_cost
            FROM
              ({sql}) AS subquery
            JOIN
              frontend_pct ON frontend_pct.code = pct_id
            WHERE
              month=%(month)s AND frontend_pct.org_type = 'CCG'
            GROUP BY
              bnf_code, product_name
            ORDER BY
              additional_cost DESC, tariff_cost DESC
            """.format(
                sql=sql),
            params)
        return cursor.fetchall()


def _date_as_str(d):
    # Necessary because the prescribing table uses a DATE field for
    # storing the date, but the view vw__presentation_summary_by_ccg
    # uses a VARCHAR
    if isinstance(d, date):
        return d.strftime('%Y-%m-%d')
    return d


def _ncso_spending_query(
        prescribing_table,
        start_date,
        end_date):
    """Return a query with params that joins all NCSO (i.e. price concession) items
    with the spending on those items.

    Where our NCSO data is more recent than our prescribing data we use the
    latest prescribing data and flag the results as estimates.

    The prescribing table is parameterised as sometimes we want to use the table
    with prescribing pre-aggregated by CCG.

    """
    sql_template = """
        SELECT
          ncso.date AS month,
          presentation.bnf_code AS bnf_code,
          COALESCE(presentation.dmd_name, presentation.name) AS product_name,
          dt.price_pence
            * rx.quantity
            * CASE WHEN
                presentation.quantity_means_pack
              THEN
                1
              ELSE
                1 / vmpp.qtyval::float
              END
            * %(discount_factor)s
            AS tariff_cost,
          COALESCE(ncso.price_pence - dt.price_pence, 0)
            * rx.quantity
            * CASE WHEN
                presentation.quantity_means_pack
              THEN
                1
              ELSE
                1 / vmpp.qtyval::float
              END
            * %(discount_factor)s
            AS additional_cost,
          ncso.date != rx.processing_date AS is_estimate,
          rx.*
        FROM
          frontend_ncsoconcession AS ncso
        JOIN
          frontend_tariffprice AS dt
        ON
          ncso.vmpp_id = dt.vmpp_id AND ncso.date = dt.date
        JOIN
          dmd2_vmpp AS vmpp
        ON
          vmpp.vppid=ncso.vmpp_id
        JOIN
          frontend_presentation AS presentation
        ON
          presentation.bnf_code = vmpp.bnf_code
        JOIN
          {prescribing_table} AS rx
        ON
          rx.presentation_code = vmpp.bnf_code
        AND
          rx.processing_date >= %(earliest_date)s
        AND
          rx.processing_date <= %(end_date)s
        AND
          -- Where we have prescribing data for the corresponding month we use
          -- that, otherwise we use the latest month of prescribing data to
          -- produce an estimate
          (
            rx.processing_date = ncso.date
            OR
            (
              rx.processing_date = %(last_prescribing_date)s
              AND
              ncso.date > rx.processing_date
            )
          )
        """
    sql = sql_template.format(prescribing_table=prescribing_table)
    last_prescribing_date = (
        ImportLog.objects.latest_in_category('prescribing').current_at
    )
    params = {
        'last_prescribing_date': last_prescribing_date,
        'start_date': start_date,
        'end_date': end_date,
        'earliest_date': min(
            _date_as_str(start_date), _date_as_str(last_prescribing_date)),
        # We discount by an additional factor of 100 to convert the figures
        # from pence to pounds
        'discount_factor': (100 - NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE) / (100*100)
    }
    return sql, params
