from django.db import connection
from django.db.models import Max

from dateutil.relativedelta import relativedelta

from api.view_utils import dictfetchall
from dmd.models import NCSOConcession


# The tariff (or concession) price is not what actually gets paid as each CCG
# will have some kind of discount with the dispenser. However the average
# discount has been pretty consistent over the years so we use that here.
NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE = 7.2


def ncso_spending_for_entity(entity, entity_type, num_months, current_month=None):
    if entity_type == 'CCG':
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
        sql, params = _ncso_spending_query(prescribing_table)
        params.update(
            entity_condition=entity_condition,
            start_date=start_date,
            end_date=end_date
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
        sql, params = _ncso_spending_query(prescribing_table)
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
        sql, params = _ncso_spending_query('vw__presentation_summary_by_ccg')
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


def _ncso_spending_query(prescribing_table='frontend_prescription'):
    """
    Return a query with params that joins all NCSO (i.e. price concession) items
    with the spending on those items.

    Where our NCSO data is more recent than our prescribing data we use the
    latest prescribing data and flag the results as estimates.

    The prescribing table is parameterised as sometimes we want to use the table
    with prescribing pre-aggregated by CCG.
    """
    sql_template = """
        SELECT
          ncso.date AS month,
          product.bnf_code AS bnf_code,
          product.name AS product_name,
          dt.price_pence * (rx.quantity / vmpp.qtyval) * %(discount_factor)s
            AS tariff_cost,
          COALESCE(ncso.price_concession_pence - dt.price_pence, 0)
            * (rx.quantity / vmpp.qtyval) * %(discount_factor)s
            AS additional_cost,
          ncso.date != rx.processing_date AS is_estimate,
          rx.*
        FROM
          dmd_ncsoconcession AS ncso
        JOIN
          dmd_tariffprice AS dt
        ON
          ncso.vmpp_id = dt.vmpp_id AND ncso.date = dt.date
        JOIN
          dmd_product AS product
        ON
          dt.product_id=product.dmdid
        JOIN
          dmd_vmpp AS vmpp
        ON
          vmpp.vppid=ncso.vmpp_id
        JOIN
          {prescribing_table} AS rx
        ON
          rx.presentation_code = product.bnf_code
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
    with connection.cursor() as cursor:
        cursor.execute(
            'SELECT MAX(processing_date) FROM {}'.format(prescribing_table))
        last_prescribing_date = cursor.fetchone()[0]
    params = {
        'last_prescribing_date': last_prescribing_date,
        # We discount by an additional factor of 100 to convert the figures
        # from pence to pounds
        'discount_factor': (100 - NATIONAL_AVERAGE_DISCOUNT_PERCENTAGE) / (100*100)
    }
    return sql, params
