from django.db.models import fields, ForeignKey, ManyToOneRel, OneToOneRel, Q

from .obj_types import clss
from functools import reduce


def build_query_obj(cls, search):
    """Return Q object to filter dm+d objects based on search.

    Parameters:

      cls: class of dm+d object to search
      search: a tree describing the search to be performed

    See TestAdvancedSearchHelpers.test_build_query_obj for an example.

    _build_query_obj_helper is a nested function to allow easier use of `map()`.
    """

    def _build_query_obj_helper(search):
        """Do the work.

        A branch node like:

            ["and", [node1, node2]]

        will be transformed, recursively, into:

        _build_query_obj_helper(node1) & _build_query_obj_helper(node2)

        A leaf node like:

            ["nm", "contains", "paracetamol"]

        will be transformed into:

            Q(nm__icontains="paracetamol")
        """

        assert len(search) in [2, 3]

        if len(search) == 2:
            # branch node
            fn = {"and": Q.__and__, "or": Q.__or__}[search[0]]
            clauses = list(map(_build_query_obj_helper, search[1]))
            return reduce(fn, clauses[1:], clauses[0])
        else:
            # leaf node
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
