# coding=utf8

import colorsys

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import BooleanField, ForeignKey
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from frontend.models import Presentation

from .models import VTM, VMP, VMPP, AMP, AMPP
from .search import search
from .view_schema import schema

obj_type_to_cls = {
    "vtm": VTM,
    "vmp": VMP,
    "vmpp": VMPP,
    "amp": AMP,
    "ampp": AMPP,
}

cls_to_obj_type = {cls: obj_type for obj_type, cls in obj_type_to_cls.items()}

def _build_row(obj, field):
    value = getattr(obj, field.name)
    if value is None:
        return

    if field.name == "invalid" and not value:
        return

    if isinstance(field, ForeignKey):
        related_model = field.related_model
        if related_model in cls_to_obj_type:
            obj_type = cls_to_obj_type[related_model]
            link = reverse("dmd_obj", args=[obj_type, value.id])
            text = getattr(value, related_model.name_field)
            return {
                "key": related_model._meta.verbose_name,
                "value": text,
                "link": link
            }

        try:
            value = value.descr
        except AttributeError:
            value = value.nm

    elif isinstance(field, BooleanField):
        value = {True: "✓", False: "✗"}.get(value)

    return {"key": field.help_text, "value": value}


def dmd_obj_view(request, obj_type, id):
    try:
        cls = obj_type_to_cls[obj_type]
    except KeyError:
        raise Http404

    obj = get_object_or_404(cls, id=id)

    fields_by_name = {field.name: field for field in cls._meta.fields}
    rels_by_name = {rel.name: rel for rel in cls._meta.related_objects}

    rows = []

    # Fields for the object
    for field_name in schema[obj_type]["fields"]:
        field = fields_by_name[field_name]

        row = _build_row(obj, field)
        if row is not None:
            rows.append(row)

    # Related objects (eg VPIs for a VMP)
    for rel_name in schema[obj_type]["other_relations"]:
        relname = rel_name.replace("_", "")
        rel = rels_by_name[relname]
        model = rel.related_model
        rel_fields_by_name = {field.name: field for field in model._meta.fields}

        if rel.multiple:
            related_instances = getattr(obj, rel.get_accessor_name()).all()
            if not related_instances.exists():
                continue
        else:
            try:
                related_instances = [getattr(obj, rel.name)]
            except ObjectDoesNotExist:
                continue

        for related_instance in related_instances:
            rows.append({"title": model._meta.verbose_name})
            for field_name in schema[rel_name]["fields"]:
                if field_name == obj_type:
                    continue
                field = rel_fields_by_name[field_name]
                row = _build_row(related_instance, field)
                if row is not None:
                    rows.append(row)

    # Related child dm+d objects (for a VMP, these will be VMPPs and AMPs)
    for rel_name in schema[obj_type]["dmd_obj_relations"]:
        relname = rel_name.replace("_", "")
        rel = rels_by_name[relname]
        assert rel.multiple
        model = rel.related_model

        related_instances = getattr(obj, rel.get_accessor_name()).valid_and_available()
        if not related_instances.exists():
            continue

        rows.append({"title": model._meta.verbose_name_plural})
        for related_instance in related_instances:
            link = reverse("dmd_obj", args=[rel_name, related_instance.id])
            rows.append({"value": related_instance.title(), "link": link})

    ctx = {
        "title": "{} {}".format(cls.__name__, id),
        "rows": rows,
    }
    return render(request, "dmd/dmd_obj.html", ctx)


def vmp_relationships_view(request, vmp_id):
    bnf_codes = set()

    vmp = get_object_or_404(VMP, id=vmp_id)
    bnf_codes.add(vmp.bnf_code)

    vmpps = vmp.vmpp_set.order_by('nm')
    vmpp_ids = [vmpp.id for vmpp in vmpps]
    bnf_codes |= {vmpp.bnf_code for vmpp in vmpps}

    amps = vmp.amp_set.order_by('descr')
    amp_ids = [amp.id for amp in amps]
    bnf_codes |= {amp.bnf_code for amp in amps}

    ampps = AMPP.objects.filter(vmpp__vmp=vmp)
    bnf_codes |= {ampp.bnf_code for ampp in ampps}

    presentations = Presentation.objects.filter(bnf_code__in=bnf_codes).order_by('bnf_code')
    num_presentations = len(presentations)

    colours_hls = [
        ((ix * 1.0 / num_presentations), 0.85, 0.75)
        for ix in range(num_presentations)
    ]

    colours_rgb = [colorsys.hls_to_rgb(*hls) for hls in colours_hls]
    colours_hex = [
        "#{0:02x}{1:02x}{2:02x}".format(
            int(rgb[0] * 256),
            int(rgb[1] * 256),
            int(rgb[2] * 256),
        )
        for rgb in colours_rgb
    ]

    bnf_code_to_colour = {}

    for ix, presentation in enumerate(presentations):
        bnf_code_to_colour[presentation.bnf_code] = colours_hex[ix]
        presentation.colour = colours_hex[ix]

    # We can remove this if we're only showing objects with BNF codes
    bnf_code_to_colour[None] = '#FFFFFF'

    table = [
        [None for _ in range(len(vmpps) + 1)]
        for _ in range(len(amps) + 1)
    ]

    for ix, vmpp in enumerate(vmpps):
        table[0][ix + 1] = {'obj': vmpp, 'colour': bnf_code_to_colour[vmpp.bnf_code]}

    for ix, amp in enumerate(amps):
        table[ix + 1][0] = {'obj': amp, 'colour': bnf_code_to_colour[amp.bnf_code]}

    for ampp in ampps:
        row_ix = amp_ids.index(ampp.amp_id) + 1
        col_ix = vmpp_ids.index(ampp.vmpp_id) + 1
        table[row_ix][col_ix] = {'obj': ampp, 'colour': bnf_code_to_colour[ampp.bnf_code]}

    if vmp.bnf_code:
        vmp_presentation = Presentation.objects.get(bnf_code=vmp.bnf_code)
    else:
        vmp_presentation = None
    vmp_colour = bnf_code_to_colour[vmp.bnf_code]

    ctx = {
        'vmp': vmp,
        'num_vmpps': len(vmpps),
        'num_amps': len(amps),
        'table': table,
        'presentations': presentations,
        'vmp_presentation': vmp_presentation,
        'vmp_colour': vmp_colour,
    }

    return render(request, "dmd/vmp_relationships.html", ctx)


def search_view(request):
    q = request.GET.get("q")

    ctx = {"q": q}

    if q:
        results = search(q)

        if len(results) == 1:
            if len(results.values()[0]) == 1:
                obj = results.values()[0][0]
                link = reverse("dmd_obj", args=[type(obj).__name__.lower(), obj.id])
                return redirect(link)

        ctx["results"] = results
    else:
        ctx["results"] = None

    return render(request, "dmd/search.html", ctx)
