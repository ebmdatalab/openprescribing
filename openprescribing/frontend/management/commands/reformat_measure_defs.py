from collections import OrderedDict
from glob import glob
import json

from django.core.management import BaseCommand


fieldnames = [
    "name",
    "title",
    "description",
    "numerator_short",
    "denominator_short",
    "why_it_matters",
    "tags",
    "tags_focus",
    "include_in_alerts",
    "url",
    "is_percentage",
    "is_cost_based",
    "low_is_good",
    "numerator_type",
    "numerator_columns",
    "numerator_from",
    "numerator_where",
    "numerator_bnf_codes",
    "numerator_bnf_codes_query",
    "numerator_bnf_codes_filter",
    "numerator_is_list_of_bnf_codes",
    "denominator_type",
    "denominator_columns",
    "denominator_from",
    "denominator_where",
    "denominator_bnf_codes",
    "denominator_bnf_codes_query",
    "denominator_bnf_codes_filter",
    "denominator_is_list_of_bnf_codes",
    "no_analyse_url",
    "authored_by",
    "checked_by",
    "date_reviewed",
    "next_review",
    "measure_notebook_url",
    "measure_complexity",
]


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for path in glob("measure_definitions/*.json"):
            measure_id = path.split("/")[-1].split(".")[0]

            with open(path) as f:
                measure_def = json.load(f)

            for k in measure_def:
                assert k in fieldnames, "{} {}".format(measure_id, k)

            measure_def = OrderedDict(
                (k, measure_def[k]) for k in fieldnames if k in measure_def
            )

            with open(path, "w") as f:
                json.dump(measure_def, f, indent=2)
