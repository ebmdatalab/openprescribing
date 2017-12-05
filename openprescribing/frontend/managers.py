from django.db.models import Q
from django.db import models


class MeasureValueManager(models.Manager):
    def by_ccg(self, org_ids, measure_id=None, tags=None):
        org_Q = Q()
        for org_id in org_ids:
            org_Q |= Q(pct_id=org_id)

        qs = self.select_related('pct', 'measure').\
            filter(
                org_Q,
                pct__org_type='CCG',
                pct__close_date__isnull=True,
                practice_id__isnull=True,
            ).\
            order_by('pct_id', 'measure_id', 'month')

        if measure_id:
            qs = qs.filter(measure_id=measure_id)

        if tags:
            qs = qs.filter(measure__tags__contains=tags)
        
        return qs

    def by_practice(self, org_ids, measure_id=None, tags=None):
        org_Q = Q()
        for org_id in org_ids:
            if len(org_id) == 3:
                org_Q |= Q(pct_id=org_id)
            else:
                org_Q |= Q(practice_id=org_id)

        qs = self.select_related('practice', 'measure').\
            filter(
                practice_id__isnull=False,
            ).\
            filter(org_Q).\
            order_by('practice_id', 'measure_id', 'month')

        if measure_id:
            qs = qs.filter(measure_id=measure_id)

        if tags:
            qs = qs.filter(measure__tags__contains=tags)

        return qs
