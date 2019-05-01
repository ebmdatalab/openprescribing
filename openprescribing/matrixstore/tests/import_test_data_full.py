import csv
import tempfile

from django.conf import settings
from django.core.management import call_command

from frontend import bq_schemas as schemas
from gcutils.bigquery import Client


def import_test_data_full(sqlite_path, data_factory, end_date, months=None):
    """
    Imports the data in `data_factory` into the SQLfile at `sqlite_path` while
    exercising the entire matrixstore_build pipeline. This includes uploading
    data to BigQuery and exporting it to Google Cloud Storage and so it can
    take several minutes to run.
    """
    upload_to_bigquery(data_factory)
    call_command(
        'matrixstore_build',
        end_date,
        sqlite_path,
        months=months,
        quiet=True
    )


def upload_to_bigquery(data_factory):
    client = Client('hscic')
    assert_is_test_dataset(client)
    create_and_populate_bq_table(
        client,
        'presentation',
        schemas.PRESENTATION_SCHEMA,
        data_factory.presentations
    )
    create_and_populate_bq_table(
        client,
        'prescribing',
        schemas.PRESCRIBING_SCHEMA,
        data_factory.prescribing
    )
    create_and_populate_bq_table(
        client,
        'practice_statistics_all_years',
        schemas.PRACTICE_STATISTICS_SCHEMA,
        data_factory.practice_statistics
    )
    create_and_populate_bq_table(
        client,
        'bnf_map',
        schemas.BNF_MAP_SCHEMA,
        data_factory.bnf_map
    )


def assert_is_test_dataset(client):
    bq_nonce = getattr(settings, 'BQ_NONCE', None)
    if not bq_nonce or str(bq_nonce) not in client.dataset_id:
        raise RuntimeError('BQ_NONCE must be set')


def create_and_populate_bq_table(client, name, schema, table_data):
    table = client.get_or_create_table(name, schema)
    if not table_data:
        return
    with tempfile.NamedTemporaryFile() as f:
        writer = csv.writer(f)
        for item in table_data:
            writer.writerow(dict_to_row(item, schema))
        f.seek(0)
        table.insert_rows_from_csv(f.name)


def dict_to_row(dictionary, schema):
    row = [dictionary[field.name] for field in schema]
    if len(row) != len(schema):
        extra = set(dictionary) - set([field.name for field in schema])
        raise ValueError(
            'Dictionary has keys which are not in BigQuery schema: {}'
            .format(', '.join(extra))
        )
    return row
