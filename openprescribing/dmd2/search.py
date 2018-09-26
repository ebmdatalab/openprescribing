from collections import OrderedDict

from .models import VTM, VMP, VMPP, AMP, AMPP


def search(q):
    try:
        int(q)
    except ValueError:
        return search_by_term(q)

    return search_by_snomed_code(q)


def search_by_term(q):
    results = OrderedDict()

    for cls in [VTM, VMP, VMPP, AMP, AMPP]:
        if hasattr(cls, 'descr'):
            kwargs = {'descr__icontains': q}
        else:
            kwargs = {'nm__icontains': q}

        objs = list(cls.objects.filter(**kwargs))
        if objs:
            results[cls._meta.verbose_name_plural] = objs

    return results


def search_by_snomed_code(q):
    results = OrderedDict()

    for cls in [VTM, VMP, VMPP, AMP, AMPP]:
        try:
            obj = cls.objects.get(pk=q)
        except cls.DoesNotExist:
            continue

        results[cls._meta.verbose_name_plural] = [obj]

    return results
