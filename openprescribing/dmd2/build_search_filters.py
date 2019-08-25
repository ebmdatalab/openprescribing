from django.db.models import fields, ForeignKey, ManyToOneRel, OneToOneRel


from .obj_types import clss
from .search_schema import schema as search_schema


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

    # The type is "string", even though the values are actually integers.  This is
    # because the QueryBuilder library calls parseInt on any values produced by a filter
    # of type "integer" (see call to Utils.changeType in getRuleInputValue).  It turns
    # out that parseInt cannot actually parse integers larger than
    # Number.MAX_SAFE_INTEGER, which is (2 ** 53) - 1, or 9007199254740991, and loses
    # precision when it tries.  This is a problem, because certain dm+d models have
    # identifiers larger than Number.MAX_SAFE_INTEGER.  Fortunately, Django is able to
    # deal with query parameters for integer fields that are submitted as strings.

    return {
        "type": "string",
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
