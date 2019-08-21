import json

from django.db.models import fields, ForeignKey, ManyToOneRel, OneToOneRel, Q

from .models import VTM, VMP, VMPP, AMP, AMPP
from .obj_types import clss
from .search_schema import schema as search_schema


NUM_RESULTS_PER_OBJ_TYPE = 10


def search(q, obj_types, include):
    try:
        int(q)
    except ValueError:
        return search_by_term(q, obj_types, include)

    return search_by_snomed_code(q)


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
    for cls in [VTM, VMP, VMPP, AMP, AMPP]:
        try:
            obj = cls.objects.get(pk=q)
        except cls.DoesNotExist:
            continue

        return [{"cls": cls, "objs": [obj]}]

    return []


def advanced_search(cls, search_params):
    search = json.loads(search_params["search"])
    include = search_params["include"]

    rules = _build_rules(search)
    query_obj = _build_query_obj(cls, search)

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
    else:
        too_many_results = False

    return {"objs": objs, "rules": rules, "too_many_results": too_many_results}


def _build_rules(search):
    """Return structure used to populate a QueryBuilder instance.

    See https://querybuilder.js.org/#method-setRules
    """

    rules = _build_rules_helper(search)
    if "condition" not in rules:
        rules = {"condition": "AND", "rules": [rules]}
    return rules


def _build_rules_helper(search):
    assert len(search) in [2, 3]

    if len(search) == 2:
        return {
            "condition": search[0].upper(),
            "rules": map(_build_rules_helper, search[1]),
        }
    else:
        value = search[2]
        if value is True:
            value = 1
        elif value is False:
            value = 0

        return {"id": search[0], "operator": search[1], "value": value}


def _build_query_obj(cls, search):
    """Return Q object to filter dm+d objects based on search.
    """

    def _build_query_obj_helper(search):
        assert len(search) in [2, 3]

        if len(search) == 2:
            fn = {"and": Q.__and__, "or": Q.__or__}[search[0]]
            clauses = map(_build_query_obj_helper, search[1])
            return reduce(fn, clauses, Q())
        else:
            field_name, operator, value = search
            if field_name == "bnf_code":
                if operator == "begins_with":
                    return Q(bnf_code__startswith=value)
                elif operator == "not_begins_with":
                    return ~Q(bnf_code__startswith=value)
                else:
                    assert False, operator
            else:
                key = _build_lookup_key(cls, field_name, operator)
                kwargs = {key: value}
                return Q(**kwargs)

    return _build_query_obj_helper(search)


def _build_lookup_key(cls, field_name, operator):
    field = cls._meta.get_field(field_name)
    builder = {
        ForeignKey: _build_lookup_fk,
        ManyToOneRel: _build_lookup_rev_fk,
        OneToOneRel: _build_lookup_rev_fk,
        fields.CharField: _build_lookup_char,
        fields.DateField: _build_lookup_date,
        fields.BooleanField: _build_lookup_boolean,
        fields.DecimalField: _build_lookup_decimal,
    }[type(field)]
    return builder(cls, field_name, operator)


def _build_lookup_fk(cls, field_name, operator):
    assert operator == "equal"
    return field_name


def _build_lookup_rev_fk(cls, field_name, operator):
    field = cls._meta.get_field(field_name)
    intermediate_model = field.related_model
    fk_fields = [
        f
        for f in intermediate_model._meta.get_fields()
        if (
            isinstance(f, ForeignKey)
            and f.related_model not in clss
            and "prev" not in f.name
        )
    ]
    assert len(fk_fields) == 1
    return "{}__{}".format(field_name, fk_fields[0].name)


def _build_lookup_char(cls, field_name, operator):
    lookup = {"contains": "icontains"}[operator]
    return "{}__{}".format(field_name, lookup)


def _build_lookup_date(cls, field_name, operator):
    lookup = {"equal": "exact", "before": "lt", "after": "gt"}[operator]
    return "{}__{}".format(field_name, lookup)


def _build_lookup_boolean(cls, field_name, operator):
    assert operator == "equal"
    return field_name


def _build_lookup_decimal(cls, field_name, operator):
    lookup = {"equal": "exact", "less than": "lt", "greater than": "gt"}[operator]
    return "{}__{}".format(field_name, lookup)


def build_search_filters(cls):
    """Return list of dicts of options for a QueryBuilder filter.

    See https://querybuilder.js.org/#filters for details.
    """

    filters = [
        _build_search_filter(cls, field_name)
        for field_name in search_schema[cls.obj_type]["fields"]
    ]

    return filters


def _build_search_filter(cls, field_name):
    if field_name == "bnf_code":
        return _build_search_filter_bnf_code_prefox()

    field = cls._meta.get_field(field_name)
    builder = {
        ForeignKey: _build_search_filter_fk,
        ManyToOneRel: _build_search_filter_rev_fk,
        OneToOneRel: _build_search_filter_rev_fk,
        fields.CharField: _build_search_filter_char,
        fields.DateField: _build_search_filter_date,
        fields.BooleanField: _build_search_filter_boolean,
        fields.DecimalField: _build_search_filter_decimal,
    }[type(field)]
    search_filter = builder(field)
    search_filter["id"] = field_name
    return search_filter


def _build_search_filter_bnf_code_prefox():
    return {
        "id": "bnf_code",
        "type": "string",
        "label": "BNF code",
        "operators": ["begins_with", "not_begins_with"],
        "validation": {"min": 4},
    }


def _build_search_filter_fk(field):
    values = field.related_model.objects.values_list("cd", "descr").order_by("descr")
    values = [{r[0]: r[1]} for r in values]

    return {
        "type": "integer",
        "label": field.help_text,
        "input": "select",
        "values": values,
        "operators": ["equal"],
        "plugin": "selectpicker",
        "plugin_config": {"liveSearch": True, "liveSearchStyle": "contains"},
    }


def _build_search_filter_rev_fk(field):
    intermediate_model = field.related_model
    fk_fields = [
        f
        for f in intermediate_model._meta.get_fields()
        if (
            isinstance(f, ForeignKey)
            and f.related_model not in clss
            and "prev" not in f.name
        )
    ]
    assert len(fk_fields) == 1
    field = fk_fields[0]
    return _build_search_filter_fk(field)


def _build_search_filter_char(field):
    return {
        "type": "string",
        "label": field.help_text,
        "operators": ["contains"],
        "validation": {"min": 3},
    }


def _build_search_filter_date(field):
    return {
        "type": "date",
        "label": field.help_text,
        "operators": ["equal", "before", "after"],
        "plugin": "datepicker",
        "plugin_config": {"format": "yyyy-mm-dd"},
    }


def _build_search_filter_boolean(field):
    return {
        "type": "boolean",
        "label": field.help_text,
        "input": "radio",
        "values": [{1: "Yes"}, {0: "No"}],
        "operators": ["equal"],
    }


def _build_search_filter_decimal(field):
    return {
        "type": "double",
        "label": field.help_text,
        "operators": ["equal", "less than", "greater than"],
    }
