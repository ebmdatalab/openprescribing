from matrixstore.build.import_practice_stats import (
    parse_practice_statistics_csv,
    write_practice_stats,
)
from matrixstore.build.import_prescribing import (
    parse_prescribing_csv,
    write_prescribing,
)
from matrixstore.build.init_db import SCHEMA_SQL, generate_dates, import_dates
from matrixstore.build.precalculate_totals import precalculate_totals_for_db
from matrixstore.build.update_bnf_map import (
    delete_presentations_with_no_prescribing,
    move_values_from_old_code_to_new,
)
from matrixstore.csv_utils import dicts_to_csv


def import_test_data_fast(sqlite_conn, data_factory, end_date, months=None):
    """
    Imports the data in `data_factory` into the supplied SQLite connection
    without touching any external services such as BigQuery or Google Cloud
    Storage (and indeed without touching disk, if the SQLite database is in
    memory).
    """
    dates = generate_dates(end_date, months=months)

    # Disable the sqlite module's magical transaction handling features because
    # we want to use our own transactions below
    previous_isolation_level = sqlite_conn.isolation_level
    sqlite_conn.isolation_level = None

    init_db(sqlite_conn, data_factory, dates)
    import_practice_stats(sqlite_conn, data_factory, dates)
    import_prescribing(sqlite_conn, data_factory, dates)
    update_bnf_map(sqlite_conn, data_factory)
    precalculate_totals_for_db(sqlite_conn)

    sqlite_conn.isolation_level = previous_isolation_level
    sqlite_conn.commit()


def init_db(sqlite_conn, data_factory, dates):
    sqlite_conn.executescript(SCHEMA_SQL)
    import_dates(sqlite_conn, dates)
    practice_codes = _get_active_practice_codes(data_factory, dates)
    sqlite_conn.executemany(
        "INSERT INTO practice (offset, code) VALUES (?, ?)", enumerate(practice_codes)
    )


def import_practice_stats(sqlite_conn, data_factory, dates):
    filtered_practice_stats = _filter_by_date(data_factory.practice_statistics, dates)
    filtered_practice_stats = list(filtered_practice_stats)
    if filtered_practice_stats:
        practice_statistics_csv = dicts_to_csv(filtered_practice_stats)
        # This blows up if we give it an empty CSV because it can't find the
        # headers it expects
        practice_statistics = parse_practice_statistics_csv(practice_statistics_csv)
    else:
        practice_statistics = []
    write_practice_stats(sqlite_conn, practice_statistics)


def import_prescribing(sqlite_conn, data_factory, dates):
    filtered_prescribing = _filter_by_date(data_factory.prescribing, dates)
    sorted_prescribing = sorted(
        filtered_prescribing, key=lambda p: (p["bnf_code"], p["practice"], p["month"])
    )
    prescribing_csv = dicts_to_csv(sorted_prescribing)
    prescribing = parse_prescribing_csv(prescribing_csv)
    write_prescribing(sqlite_conn, prescribing)


def update_bnf_map(sqlite_conn, data_factory):
    cursor = sqlite_conn.cursor()
    for item in data_factory.bnf_map:
        move_values_from_old_code_to_new(
            cursor, item["former_bnf_code"], item["current_bnf_code"]
        )
    delete_presentations_with_no_prescribing(cursor)


def _get_active_practice_codes(data_factory, dates):
    practice_codes = set()
    for prescription in _filter_by_date(data_factory.prescribing, dates):
        practice_codes.add(prescription["practice"])
    for practice_stat in _filter_by_date(data_factory.practice_statistics, dates):
        practice_codes.add(practice_stat["practice"])
    return sorted(practice_codes)


def _filter_by_date(items, dates):
    for item in items:
        if item["month"][:10] in dates:
            yield item
