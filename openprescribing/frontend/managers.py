from django.db import models

import api.view_utils as utils


class MeasureValueManager(models.Manager):
    def by_ccg(self, org_ids, measure_id=None, tags=None):
        tags = tags or []
        params = []
        query = 'SELECT mv.month AS date, mv.numerator, mv.denominator, '
        query += 'mv.calc_value, mv.percentile, mv.cost_savings, '
        query += 'mv.pct_id, pc.name as pct_name, measure_id, '
        query += 'ms.name, ms.title, ms.description, '
        query += 'ms.why_it_matters, ms.denominator_short, '
        query += 'ms.numerator_short, '
        query += 'ms.url, ms.is_cost_based, ms.is_percentage, '
        query += 'ms.low_is_good '
        query += "FROM frontend_measurevalue mv "
        query += "JOIN frontend_pct pc ON "
        query += "(mv.pct_id=pc.code AND pc.org_type = 'CCG') "
        query += "JOIN frontend_measure ms ON mv.measure_id=ms.id "
        query += "WHERE pc.close_date IS NULL AND "
        if org_ids:
            query += "("
            for i, org_id in enumerate(org_ids):
                query += "mv.pct_id=%s "
                params.append(org_id)
                if (i != len(org_ids) - 1):
                    query += ' OR '
            query += ") AND "
        query += 'mv.practice_id IS NULL '
        if measure_id:
            query += "AND mv.measure_id=%s "
            params.append(measure_id)
        for tag in tags:
            query += "AND %s = ANY(ms.tags) "
            params.append(tag)
        query += "ORDER BY mv.pct_id, measure_id, date"
        data = utils.execute_query(query, [params])

        return data

    def by_practice(self, org_ids, measure_id=None, tags=None):
        tags = tags or []
        params = []
        query = 'SELECT mv.month AS date, mv.numerator, mv.denominator, '
        query += 'mv.calc_value, mv.percentile, mv.cost_savings, '
        query += 'mv.practice_id, pc.name as practice_name, measure_id, '
        query += 'ms.name, ms.title, ms.description, ms.why_it_matters, '
        query += 'ms.denominator_short, ms.numerator_short, '
        query += 'ms.url, ms.is_cost_based, ms.is_percentage, '
        query += 'ms.low_is_good '
        query += "FROM frontend_measurevalue mv "
        query += "JOIN frontend_practice pc ON mv.practice_id=pc.code "
        query += "JOIN frontend_measure ms ON mv.measure_id=ms.id "
        query += "WHERE "
        for i, org_id in enumerate(org_ids):
            if len(org_id) == 3:
                query += "mv.pct_id=%s "
            else:
                query += "mv.practice_id=%s "
            if (i != len(org_ids) - 1):
                query += ' OR '
            params.append(org_id)
        if measure_id:
            query += "AND mv.measure_id=%s "
            params.append(measure_id)
        for tag in tags:
            query += "AND %s = ANY(ms.tags) "
            params.append(tag)
        query += "ORDER BY mv.practice_id, measure_id, date"
        data = utils.execute_query(query, [params])

        return data
