import pandas as pd
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from frontend.models import Chemical, Section
from frontend.views.views import _entity_type_human, _get_entity


def outliers_for_one_entity(request, entity_type, entity_code):
    entity = _get_entity(entity_type, entity_code)
    base_analyse_url = f"/analyse/#org={entity_type}&orgIds={entity_code}"
    bnf_code_to_name = dict(
        list(Chemical.objects.values_list("bnf_code", "chem_name"))
        + list(Section.objects.values_list("bnf_id", "name"))
    )
    try:
        df = pd.read_feather(
            settings.OUTLIERS_DATA_DIR / entity_type / f"{entity_code}.feather"
        )
    except FileNotFoundError:
        raise Http404("Data ingest in progress. Please check back in a few minutes.")
    df = df[~pd.isna(df["zscore"])]
    high_outliers = [
        _outlier_context(row, base_analyse_url, bnf_code_to_name)
        for row in df.sort_values("zscore", ascending=False)[:10].itertuples()
    ]
    low_outliers = [
        _outlier_context(row, base_analyse_url, bnf_code_to_name)
        for row in df.sort_values("zscore")[:10].itertuples()
    ]
    context = {
        "entity": entity,
        "entity_type": _entity_type_human(entity_type),
        "high_outliers": high_outliers,
        "low_outliers": low_outliers,
    }
    return render(request, "outliers_for_one_entity.html", context)


def _outlier_context(row, base_analyse_url, bnf_code_to_name):
    chemical = row.chemical
    subparagraph = chemical[:-2]
    analyse_url = f"{base_analyse_url}&numIds={chemical}&denomIds={subparagraph}"
    context = row._asdict()
    context.update(
        {
            "chemical_name": bnf_code_to_name[row.chemical],
            "subparagraph_name": bnf_code_to_name.get(subparagraph, "?"),
            "analyse_url": analyse_url,
        }
    )
    return context
