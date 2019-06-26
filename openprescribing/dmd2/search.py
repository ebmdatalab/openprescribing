from .models import VTM, VMP, VMPP, AMP, AMPP


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
        if cls.obj_type not in obj_types:
            continue

        qs = cls.objects
        if 'invalid' not in include:
            qs = qs.valid()
        if 'unavailable' not in include:
            qs = qs.available()
        if 'no_bnf_code' not in include:
            qs = qs.with_bnf_code()
        qs = qs.search(q)

        objs = list(qs)
        if objs:
            results.append({
                'cls': cls,
                'objs': objs,
            })

    return results


def search_by_snomed_code(q):
    for cls in [VTM, VMP, VMPP, AMP, AMPP]:
        try:
            obj = cls.objects.get(pk=q)
        except cls.DoesNotExist:
            continue

        return [{
            'cls': cls,
            'objs': [obj],
        }]

    return []
