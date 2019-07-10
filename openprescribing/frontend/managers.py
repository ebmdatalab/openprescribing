from django.db import models
from django.db.models import FloatField, Func, F, Q, Value, Sum
from django.db.models.functions import Cast, Coalesce, Greatest
from django.contrib.postgres.fields.jsonb import (
    JSONField, KeyTextTransform as ValueFromJsonObject
)


CENTILES = ['10', '20', '30', '40', '50', '60', '70', '80', '90']


class MeasureValueQuerySet(models.QuerySet):
    def for_measures(self, measure_ids):
        if measure_ids:
            return self.filter(measure_id__in=measure_ids)
        else:
            return self

    def for_tags(self, tags):
        if tags:
            return self.filter(measure__tags__contains=tags)
        else:
            return self

    def filter_by_org_type(self, org_type):
        if org_type == 'practice':
            return self.filter(
                practice_id__isnull=False,
            )
        elif org_type == 'pcn':
            return self.filter(
                pcn_id__isnull=False,
                practice_id__isnull=True,
                pct_id__isnull=True,
            )
        elif org_type == 'ccg':
            return self.filter(
                practice_id__isnull=True,
                pct_id__isnull=False,
                pct__org_type='CCG',
                pct__close_date__isnull=True,
            )
        elif org_type == 'stp':
            return self.filter(
                stp_id__isnull=False,
                pct_id__isnull=True,
                practice_id__isnull=True,
            )
        elif org_type == 'regional_team':
            return self.filter(
                regional_team_id__isnull=False,
                pct_id__isnull=True,
                practice_id__isnull=True,
            )
        else:
            raise ValueError('Unknown org_type: {}'.format(org_type))

    def for_orgs(self, org_type, org_ids):
        qs = self.select_related('measure')

        if org_ids:
            qs = qs.select_related(org_type)

            org_type_key = org_type + '_id'
            org_Q = Q()

            for org_id in org_ids:
                org_Q |= Q(**{org_type_key: org_id})

            qs = qs.filter(org_Q)

        return qs

    def by_org(
            self,
            org_type,
            parent_org_type=None,
            org_ids=None,
            measure_ids=None,
            tags=None
        ):
        '''Return MeasureValues for org_type.

        MeasureValues can be restricted to particular organisations, measures,
        and/or tags.

        For instance, to find all MeasureValues for practices in CCG 99P:

            .by_org('practice', parent_org_type='ccg', org_ids=['P99'])
        '''

        # The JS code that displays MeasureValues will never cause this method
        # to be called with multiple orgs and multiple measures.
        if org_ids is not None and measure_ids is not None:
            assert len(org_ids) <= 1 or len(measure_ids) <= 1

        if org_type == 'pct':
            org_type = 'ccg'

        qs = self.filter_by_org_type(org_type)

        if parent_org_type == 'ccg':
            parent_org_type = 'pct'

        return qs.for_orgs(parent_org_type, org_ids) \
            .for_measures(measure_ids) \
            .for_tags(tags) \
            .order_by('month')

    def aggregate_by_measure_and_month(self):
        """
        Sum MeasureValues in the current query, grouped by measure and month

        This handles recalcuating the ratios and summing the cost savings
        correctly.  Note a couple of potential gotchas:

         * Return value is a generator, not a QuerySet, so you can iterate
           over it as normal but not do other things you might with a QuerySet

         * Returned objects are unsaved MeasureValue instances so they have
           all the attributes/methods you would expect on a MeasureValue but
           they don't actually exist in the database
        """
        aggregate_queryset = (
            self
            .values('measure_id', 'month')
            .order_by('measure_id', 'month')
            .annotate(
                numerator=Sum('numerator'),
                denominator=Sum('denominator'),
                calc_value=_divide('numerator', 'denominator'),
                cost_savings=_aggregate_over_json(
                    field='cost_savings',
                    aggregate_function=_sum_positive_values,
                    keys=CENTILES
                )
            )
        )
        return (self.model(**row) for row in aggregate_queryset)

    def aggregate_cost_savings(self):
        """
        Returns a dictionary of cost savings, summed over all MeasureValues in
        the current query
        """
        result = self.aggregate(
            total=_aggregate_over_json(
                field='cost_savings',
                aggregate_function=_sum_positive_values,
                keys=CENTILES
            )
        )
        return result['total']

    def calculate_cost_savings(self, target_costs,
                               cost_per_unit_field='calc_value',
                               units_field='denominator'):
        """
        Calculates cost savings dynamically for measures (like Low Priority
        measures) where we don't yet precalculate them.

        `target_costs` is a dictionary mapping arbitrary keys (which will
        usually be centiles, but don't have to be) to a target cost-per-unit.
        Note "unit" here can be anything: in the case of Low Priority measures
        it means "1000 patients".

        Returns a dictionary whose keys are those supplied in `target_costs`
        and whose values are the saving that would be achieved if that target
        cost were met across all MeasureValues included in the current query.
        """
        savings = {
            key: _calculate_saving_at_cost(
                target_cost, cost_per_unit_field, units_field
            )
            for (key, target_cost) in target_costs.items()
        }
        savings_as_json = _build_json_object(savings)
        return self.aggregate(savings=savings_as_json)['savings']


def _calculate_saving_at_cost(target_cost, cost_per_unit_field, units_field):
    """
    SQL function which calculates savings achieved if the target cost-per-unit
    was met across the aggregation
    """
    per_unit_saving = F(cost_per_unit_field) - Value(target_cost)
    saving = F(units_field) * per_unit_saving
    return _sum_positive_values(saving)


def _divide(numerator_field, denominator_field):
    """
    SQL division function which handles NULLs and divide-by-zero gracefully
    """
    numerator = Coalesce(numerator_field, Value(0.0))
    denominator = Func(denominator_field, Value(0.0), function='NULLIF')
    return numerator / denominator


def _aggregate_over_json(field, aggregate_function, keys):
    """
    SQL function which aggregates over `field` (which should be of JSONB type)
    by applying `aggregate_function` over each of the supplied `keys` within
    the object.  Returns a JSONB object with those specified keys.
    """
    return _build_json_object({
        key: aggregate_function(_get_json_value(key, field))
        for key in keys
    })


def _build_json_object(dictionary):
    """
    SQL function which builds a JSONB object from a Python dictionary whose
    keys are fixed values (strings or ints) but whose values may be arbitrary
    SQL functions
    """
    args = []
    for key, value in dictionary.items():
        args.append(Value(_preserve_key_type(key)))
        args.append(value)
    return Func(*args, function='jsonb_build_object', output_field=JSONField())


def _sum_positive_values(field):
    """
    SQL function which sums over `field` ignoring all negative values
    """
    field_as_float = Cast(field, FloatField())
    field_with_floor = Greatest(field_as_float, Value(0.0))
    return Sum(field_with_floor)


def _get_json_value(key, json_field):
    """
    SQL function which extracts `key` from a field of type JSONB
    """
    return ValueFromJsonObject(_preserve_key_type(key), json_field)


def _preserve_key_type(key):
    """
    Django's Postgres JSON library always converts int-like strings to ints. If
    you want to read from an object with a key of "10" (the string) you are
    screwed. Hence this nasty workaround.
    """
    if not isinstance(key, (int, NotAnInt)):
        key = NotAnInt(key)
    return key


class NotAnInt(str):
    """
    Represents a string that can't be converted to an int, even if it looks
    like one
    """
    def __int__(self):
        raise ValueError('Not an int')
