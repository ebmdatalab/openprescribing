from urllib.parse import urlencode

from django.urls import reverse
from frontend.utils.bnf_hierarchy import simplify_bnf_codes

from .build_rules import build_rules
from .build_search_query import build_query_obj
from .models import AMP, AMPP, VMP, VMPP, VTM

NUM_RESULTS_PER_OBJ_TYPE = 10


def search(q, obj_types, include):
    results = search_by_term(q, obj_types, include)
    if not results:
        results = search_by_snomed_code(q)
    if not results:
        results = search_by_gtin(q)
    return results


def search_by_term(q, obj_types, include):
    results = []

    for cls in [VTM, VMP, VMPP, AMP, AMPP]:
        if obj_types and cls.obj_type not in obj_types:
            continue

        qs = cls.objects
        if "invalid" not in include:
            qs = qs.valid()
        if "unavailable" not in include:
            qs = qs.available()
        if "no_bnf_code" not in include:
            qs = qs.with_bnf_code()
        qs = qs.search(q)

        objs = list(qs)
        if objs:
            results.append({"cls": cls, "objs": objs})

    return results


def search_by_snomed_code(q):
    try:
        int(q)
    except ValueError:
        return []

    for cls in [VTM, VMP, VMPP, AMP, AMPP]:
        try:
            obj = cls.objects.get(pk=q)
        except cls.DoesNotExist:
            continue

        return [{"cls": cls, "objs": [obj]}]

    return []


def search_by_gtin(q):
    try:
        int(q)
    except ValueError:
        return []

    try:
        obj = AMPP.objects.get(gtin__gtin=q)
    except AMPP.DoesNotExist:
        return []

    return [{"cls": AMPP, "objs": [obj]}]


def advanced_search(cls, search, include):
    """Perform a search against all dm+d objects of a particular type.

    Parameters:

      cls: class of dm+d object to search
      search_params: a dict with the following keys:
        search: a tree describing the search to be performed, submitted when user
                performs the search (see TestAdvancedSearchHelpers for an example)
        include: a list of strings taken from: ["invalid", "unavailable", "no_bnf_code"]

    Returns dict with the following keys:

      objs: queryset of results
      rules: structure used to populate a QueryBuilder instance (see
             https://querybuilder.js.org/#method-setRules)
      too_many_results: flag indicating whether more than 10,000 results were returned
    """

    rules = build_rules(search)
    query_obj = build_query_obj(cls, search)

    qs = cls.objects
    if "invalid" not in include:
        qs = qs.valid()
    if "unavailable" not in include:
        qs = qs.available()
    if "no_bnf_code" not in include:
        qs = qs.with_bnf_code()

    # 10,000 is an arbitrary cut off.  We should do pagination properly.
    objs = qs.filter(query_obj)[:10001]

    if len(objs) == 10001:
        too_many_results = True
        objs = objs[:10000]
        analyse_url = None
    else:
        too_many_results = False
        analyse_url = _build_analyse_url(objs)

    return {
        "objs": objs,
        "rules": rules,
        "too_many_results": too_many_results,
        "analyse_url": analyse_url,
    }


def _build_analyse_url(objs):
    bnf_codes = [obj.bnf_code for obj in objs if obj.bnf_code]
    params = {
        "numIds": ",".join(simplify_bnf_codes(bnf_codes)),
        "denom": "total_list_size",
    }

    querystring = urlencode(params)
    url = "{}#{}".format(reverse("analyse"), querystring)

    if len(url) > 5000:
        # Anything longer than 5000 characters takes too long to load.  This
        # matches the behaviour of import_measures.build_analyse_url().
        return

    return url
