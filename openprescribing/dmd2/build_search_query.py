from django.db.models import fields, ForeignKey, ManyToOneRel, OneToOneRel, Q

from .obj_types import clss


def build_query_obj(cls, search):
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
