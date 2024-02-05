# coding=utf8

import colorsys
import csv
import json
from copy import copy
from urllib.parse import urlencode

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import ForeignKey, fields
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from frontend.models import ImportLog, Presentation, TariffPrice
from matrixstore.db import get_db

from .build_search_filters import build_search_filters
from .forms import AdvancedSearchForm, SearchForm
from .models import AMP, AMPP, VMP, VMPP
from .obj_types import cls_to_obj_type, obj_type_to_cls
from .search import advanced_search, search
from .view_schema import schema as view_schema


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
                "link": link,
            }

        try:
            value = value.descr
        except AttributeError:
            value = value.nm

    elif isinstance(field, fields.BooleanField):
        value = {True: "✓", False: "✗"}.get(value)

    return {"key": field.help_text, "value": value}


def dmd_obj_view(request, obj_type, id):
    try:
        cls = obj_type_to_cls[obj_type]
    except KeyError:
        raise Http404

    obj = get_object_or_404(cls, id=id)
    obj_type_human = obj_type.upper()

    fields_by_name = {field.name: field for field in cls._meta.fields}
    rels_by_name = {rel.name: rel for rel in cls._meta.related_objects}

    rows = []

    # Fields for the object
    for field_name in view_schema[obj_type]["fields"]:
        field = fields_by_name[field_name]

        row = _build_row(obj, field)
        if row is not None:
            rows.append(row)

    # Related objects (eg VPIs for a VMP)
    for rel_name in view_schema[obj_type]["other_relations"]:
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
            for field_name in view_schema[rel_name]["fields"]:
                if field_name == obj_type:
                    continue
                field = rel_fields_by_name[field_name]
                row = _build_row(related_instance, field)
                if row is not None:
                    rows.append(row)

    # Related child dm+d objects (for a VMP, these will be VMPPs and AMPs)
    for rel_name in view_schema[obj_type]["dmd_obj_relations"]:
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

    if isinstance(obj, (VMP, AMP, VMPP, AMPP)) and obj.bnf_code is not None:
        has_prescribing = get_db().query_one(
            """
            SELECT EXISTS(
                SELECT 1 FROM presentation WHERE bnf_code=?
            )
            """,
            [obj.bnf_code],
        )[0]
    else:
        has_prescribing = False

    if isinstance(obj, VMPP):
        has_dt = TariffPrice.objects.filter(vmpp_id=id).exists()
    else:
        has_dt = False

    ctx = {
        "title": "{} {}".format(obj_type_human, id),
        "obj": obj,
        "obj_type": obj_type_human,
        "rows": rows,
        "has_prescribing": has_prescribing,
        "has_dt": has_dt,
    }
    ctx.update(_release_metadata())
    return render(request, "dmd/dmd_obj.html", ctx)


def vmp_relationships_view(request, vmp_id):
    bnf_codes = set()

    vmp = get_object_or_404(VMP, id=vmp_id)
    bnf_codes.add(vmp.bnf_code)

    vmpps = vmp.vmpp_set.order_by("nm")
    vmpp_ids = [vmpp.id for vmpp in vmpps]
    bnf_codes |= {vmpp.bnf_code for vmpp in vmpps}

    amps = vmp.amp_set.order_by("descr")
    amp_ids = [amp.id for amp in amps]
    bnf_codes |= {amp.bnf_code for amp in amps}

    ampps = AMPP.objects.filter(vmpp__vmp=vmp)
    bnf_codes |= {ampp.bnf_code for ampp in ampps}

    presentations = Presentation.objects.filter(bnf_code__in=bnf_codes).order_by(
        "bnf_code"
    )
    num_presentations = len(presentations)

    colours_hls = [
        ((ix * 1.0 / num_presentations), 0.85, 0.75) for ix in range(num_presentations)
    ]

    colours_rgb = [colorsys.hls_to_rgb(*hls) for hls in colours_hls]
    colours_hex = [
        "#{0:02x}{1:02x}{2:02x}".format(
            int(rgb[0] * 256), int(rgb[1] * 256), int(rgb[2] * 256)
        )
        for rgb in colours_rgb
    ]

    bnf_code_to_colour = {}

    for ix, presentation in enumerate(presentations):
        bnf_code_to_colour[presentation.bnf_code] = colours_hex[ix]
        presentation.colour = colours_hex[ix]

    # We can remove this if we're only showing objects with BNF codes
    bnf_code_to_colour[None] = "#FFFFFF"

    table = [[None for _ in range(len(vmpps) + 1)] for _ in range(len(amps) + 1)]

    for ix, vmpp in enumerate(vmpps):
        table[0][ix + 1] = {"obj": vmpp, "colour": bnf_code_to_colour[vmpp.bnf_code]}

    for ix, amp in enumerate(amps):
        table[ix + 1][0] = {"obj": amp, "colour": bnf_code_to_colour[amp.bnf_code]}

    for ampp in ampps:
        row_ix = amp_ids.index(ampp.amp_id) + 1
        col_ix = vmpp_ids.index(ampp.vmpp_id) + 1
        table[row_ix][col_ix] = {
            "obj": ampp,
            "colour": bnf_code_to_colour[ampp.bnf_code],
        }

    if vmp.bnf_code:
        vmp_presentation = Presentation.objects.get(bnf_code=vmp.bnf_code)
    else:
        vmp_presentation = None
    vmp_colour = bnf_code_to_colour[vmp.bnf_code]

    ctx = {
        "vmp": vmp,
        "num_vmpps": len(vmpps),
        "num_amps": len(amps),
        "table": table,
        "presentations": presentations,
        "vmp_presentation": vmp_presentation,
        "vmp_colour": vmp_colour,
    }

    return render(request, "dmd/vmp_relationships.html", ctx)


def bnf_code_relationships_view(request, bnf_code):
    presentation = get_object_or_404(Presentation, bnf_code=bnf_code)

    vmps = VMP.objects.filter(bnf_code=bnf_code)
    vmpps = VMPP.objects.filter(bnf_code=bnf_code)
    amps = AMP.objects.filter(bnf_code=bnf_code)
    ampps = AMPP.objects.filter(bnf_code=bnf_code).select_related("amp")

    ctx = {
        "bnf_code": bnf_code,
        "presentation": presentation,
        "vmps": vmps,
        "vmpps": vmpps,
        "amps": amps,
        "ampps": ampps,
    }

    return render(request, "dmd/bnf_code_relationships.html", ctx)


def search_view(request):
    if "q" in request.GET:
        # This is a request with a search query.
        form = SearchForm(request.GET)

        if form.is_valid():
            # Do the search and annotate the results.
            search_params = form.cleaned_data
            max_results_per_obj_type = (
                search_params.pop("max_results_per_obj_type") or 10
            )
            results = search(**search_params)
            _annotate_search_results(results, search_params, max_results_per_obj_type)

            if len(results) == 1:
                # There are only results for one type of object.
                if len(results[0]["objs"]) == 1:
                    # There's only one object in these results, so we redirect
                    # to that object.
                    obj = results[0]["objs"][0]
                    link = reverse("dmd_obj", args=[obj.obj_type, obj.id])
                    return redirect(link)

        else:
            # The form is not valid, so don't do the search!
            results = None

    else:
        # This is a request without a search query.  Render an empty form and
        # no search results.
        form = SearchForm()
        results = None

    ctx = {"form": form, "results": results}

    ctx.update(_release_metadata())
    return render(request, "dmd/search.html", ctx)


def _annotate_search_results(results, search_params, max_results_per_obj_type):
    """Add extra information to search results to be displayed to user.

    Additionally, if there are results for more than one type of object, the
    results are truncated, per object type.
    """
    for result in results:
        result["obj_type_human_plural"] = result["cls"]._meta.verbose_name_plural
        result["num_hits"] = len(result["objs"])

        if len(results) > 1:
            if len(result["objs"]) > max_results_per_obj_type:
                result["objs"] = result["objs"][:max_results_per_obj_type]
                new_search_params = copy(search_params)
                new_search_params["obj_types"] = [result["cls"].obj_type]
                querystring = urlencode(new_search_params, doseq=True)
                result["link_to_more"] = reverse("dmd_search") + "?" + querystring


def advanced_search_view(request, obj_type):
    cls = obj_type_to_cls[obj_type]

    objs = None
    rules = None
    too_many_results = False
    analyse_url = None

    if "search" in request.GET:
        form = AdvancedSearchForm(request.GET)
        if form.is_valid():
            search = json.loads(form.cleaned_data["search"])
            include = form.cleaned_data["include"]
            results = advanced_search(cls, search, include)
            objs = results["objs"]
            rules = results["rules"]
            too_many_results = results["too_many_results"]
            analyse_url = results["analyse_url"]
            if request.GET.get("format") == "csv":
                response = HttpResponse(content_type="text/csv")
                response["Content-Disposition"] = (
                    'attachment; filename="openprescribing-dmd-search.csv"'
                )
                writer = csv.writer(response)
                writer.writerow([f"{obj_type}_id", "name", "bnf_code", "invalid"])
                writer.writerows(
                    [obj.id, obj.title(), obj.bnf_code, 1 if obj.invalid else 0]
                    for obj in objs
                )
                return response
    else:
        form = AdvancedSearchForm()

    ctx = {
        "obj_type": obj_type,
        "obj_type_human_plural": cls._meta.verbose_name_plural,
        "form": form,
        "objs": objs,
        "rules": rules,
        "too_many_results": too_many_results,
        "analyse_url": analyse_url,
        "obj_types": ["vmp", "amp", "vmpp", "ampp"],
    }
    ctx.update(_release_metadata())
    return render(request, "dmd/advanced-search.html", ctx)


def search_filters_view(request, obj_type):
    """Return filters to build a QueryBuilder form for given obj_type.

    See https://querybuilder.js.org/#filters for details.

    This returns quite quickly (<100ms) but would be a good candidate to cache.
    """

    cls = obj_type_to_cls[obj_type]
    return JsonResponse({"filters": build_search_filters(cls)})


def _release_metadata():
    import_log = ImportLog.objects.latest_in_category("dmd")

    return {
        "trud_release": "NHSBSA_" + import_log.filename,
        "import_datetime": import_log.imported_at,
    }
