import shutil

import pandas as pd
from django.conf import settings
from matrixstore.build.dates import generate_dates
from matrixstore.db import get_db, get_row_grouper


def build(end_date, months):
    """
    Creates, for each organisation type, a directory containing one feather file for
    each organisation.  This data is served by outliers.views.outliers_for_one_entity.

    These files contain a serialised pd.DataFrame, with one row per BNF chemical, and
    the following columns:

     - chemical
        - BNF code of chemical
     - chemical_items
        - the number of items of this chemical prescribed by this organisation in
          given time period
     - subparagraph
        - BNF code of chemical's subparagraph
     - subparagraph_items
        - the number of items of this subparagraph prescribed by this organisation in
          given time period
     - ratio
        - the ratio of chemical_items to subparagraph_items
     - mean
        - the mean of the ratios for all organisations of given type
     - std
        - the standard deviation of the ratios for all organisations of given type
     - zscore
        - this organisation's z-score for this chemical, against all organisations of
          given type
    """

    start_date, *_, end_date = generate_dates(end_date, months)

    for org_type in [
        "practice",
        "ccg",
        "pcn",
        "stp",
        "regional_team",
    ]:
        df = prescribing_for_orgs(start_date, end_date, org_type)
        dir_path = settings.OUTLIERS_DATA_DIR / org_type
        try:
            # This means that outliers data will be unavailable for a few minutes during
            # an import.  This is acceptable for a "labs" feature.
            shutil.rmtree(dir_path)
        except FileNotFoundError:
            pass
        dir_path.mkdir(parents=True)
        for org_code in df.index.get_level_values(0).unique():
            df.loc[org_code].reset_index().rename(
                columns={"index": "chemical"}
            ).to_feather(dir_path / f"{org_code}.feather")


def prescribing_for_orgs(start_date, end_date, org_type):
    """
    Returns a large pd.DataFrame, indexed by organisation and BNF chemical, with columns
    as described in prescribing_by_chemical.
    """
    chemicals = all_chemicals()
    df = pd.concat(
        (
            prescribing_by_chemical(start_date, end_date, org_type, chemical)
            for chemical in chemicals
        ),
        keys=chemicals,
    )
    return df.swaplevel().sort_index()


def prescribing_by_chemical(start_date, end_date, org_type, chemical):
    """
    Returns a pd.DataFrame, indexed by organisation, with colunms for the number of
    items prescribed in given time period for both the given BNF chemical and its BNF
    subparagraph, as well as the ratio between the two, the mean and standard deviation
    of the ratio, and the z-score for each organisation.
    """
    subparagraph = chemical[:-2]
    df = pd.DataFrame()
    df["chemical_items"] = prescribing_by_org(start_date, end_date, org_type, chemical)
    df["subparagraph_items"] = prescribing_by_org(
        start_date, end_date, org_type, subparagraph
    )
    df["ratio"] = df["chemical_items"] / df["subparagraph_items"]
    df["mean"] = df["ratio"].mean()
    df["std"] = df["ratio"].std()
    df["zscore"] = (df["ratio"] - df["mean"]) / df["std"]
    return df


def prescribing_by_org(start_date, end_date, org_type, bnf_prefix):
    """
    Returns a pd.Series, indexed by organisation, containing the total number of items
    with given BNF prefix, prescribed in given time period.
    """
    db = get_db()
    sql = f"select matrix_sum(items) from presentation where bnf_code like '{bnf_prefix}%'"
    results = list(db.query_one(sql))[0]
    from_offset = db.date_offsets[start_date]
    to_offset = db.date_offsets[end_date] + 1
    filtered_results = results[:, from_offset:to_offset]
    grouper_org_type = {
        "practice": "standard_practice",
        "ccg": "standard_ccg",
    }.get(org_type, org_type)
    grouper = get_row_grouper(grouper_org_type)
    return pd.Series(
        grouper.sum(filtered_results).sum(axis=1),
        index=grouper.offsets.keys(),
    )


def all_chemicals():
    """
    Returns list of all BNF chemicals up to and including chapter 17.
    """
    db = get_db()
    return sorted(
        {
            r[0][:9]
            for r in db.query("select bnf_code from presentation where bnf_code < '18'")
        }
    )
