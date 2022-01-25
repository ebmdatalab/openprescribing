"""
This command:

    * deletes all prescribing data (both original data and extracts created by the matrixstore build) from:
      * the filesystem
      * BigQuery
      * Cloud Storage
    * resets the import pipeline so that the import may be re-run with correct data
"""

import json
import os

import networkx as nx
from django.conf import settings
from django.core.management import BaseCommand

from frontend.models import ImportLog
from gcutils.bigquery import Client as BQClient, NotFound
from gcutils.storage import Client as StorageClient
from pipeline.models import TaskLog
from pipeline.runner import load_import_records, dump_import_records


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("year")
        parser.add_argument("month")

    def handle(self, year, month, **kwargs):
        verify_year_month(year, month)
        delete_import_record(year, month)
        mark_task_logs_as_failed(year, month)
        delete_fetch_and_import_task_log(year, month)
        delete_import_logs(year, month)
        delete_prescribing_file_on_filesystem(year, month)
        delete_prescribing_file_in_storage(year, month)
        delete_temporary_prescribing_bq_table(year, month)
        remove_records_from_bq_table(year, month)
        delete_backup_from_storage(year, month)
        delete_matrixstore_bq_table(year, month)
        delete_matrixstore_storage_files(year, month)
        delete_matrixstore_download(year, month)


def verify_year_month(year, month):
    print("verify_year_month")
    log = ImportLog.objects.latest_in_category("prescribing")
    assert log.current_at.year == year
    assert log.current_at.month == int(month)


def delete_import_record(year, month):
    print("delete_import_record")
    import_records = load_import_records()
    logs = import_records["prescribing"]
    new_logs = [
        r for r in logs if f"prescribing_v2/{year}_{month}" not in r["imported_file"]
    ]
    assert len(logs) == len(new_logs) + 1
    import_records["prescribing"] = new_logs
    dump_import_records(import_records)


def mark_task_logs_as_failed(year, month):
    print("mark_task_logs_as_failed")
    with open(settings.PIPELINE_METADATA_DIR + "/tasks.json") as f:
        tasks = json.load(f)

    graph = nx.DiGraph()
    for task_name, task_def in tasks.items():
        for dependency_name in task_def.get("dependencies", []):
            graph.add_edge(dependency_name, task_name)

    fetch_task_log = TaskLog.objects.get(
        task_name="fetch_prescribing",
        year=year,
        month=month,
        status=TaskLog.SUCCESSFUL,
    )

    for task_name in nx.descendants(graph, "fetch_prescribing"):
        task_log = TaskLog.objects.get(
            task_name=task_name, year=year, month=month, status=TaskLog.SUCCESSFUL
        )
        assert task_log.started_at > fetch_task_log.started_at
        task_log.status = TaskLog.FAILED
        task_log.save()

    fetch_task_log.status = TaskLog.FAILED
    fetch_task_log.save()


def delete_fetch_and_import_task_log(year, month):
    print("delete_fetch_and_import_task_log")
    TaskLog.objects.get(task_name="fetch_and_import", year=year, month=month).delete()


def delete_import_logs(year, month):
    print("delete_import_logs")
    ImportLog.objects.get(
        category="prescribing", current_at=f"{year}-{month}-01"
    ).delete()
    ImportLog.objects.get(
        category="dashboard_data", current_at=f"{year}-{month}-01"
    ).delete()


def delete_prescribing_file_on_filesystem(year, month):
    print("delete_prescribing_file_on_filesystem")
    path = os.path.join(
        settings.PIPELINE_DATA_BASEDIR,
        "prescribing_v2",
        f"{year}_{month}",
        f"epd_{year}{month}.csv",
    )
    os.remove(path)


def delete_prescribing_file_in_storage(year, month):
    print("delete_prescribing_file_in_storage")
    _delete_file_from_storage("hscic/prescribing_v2/2021_10")


def delete_temporary_prescribing_bq_table(year, month):
    print("delete_temporary_prescribing_bq_table")
    try:
        _delete_table_from_bq("tmp_eu", f"raw_prescribing_data_{year}_{month}")
    except NotFound:
        # This is ok, as the table might already have been deleted
        pass


def remove_records_from_bq_table(year, month):
    print("remove_records_from_bq_table")
    client = BQClient("hscic")
    sql = (
        f"DELETE FROM ebmdatalab.hscic.prescribing_v2 WHERE month = '{year}-{month}-01'"
    )
    client.query(sql)


def delete_backup_from_storage(year, month):
    print("delete_backup_from_storage")
    _delete_file_from_storage("backups/prescribing_v2/2021_10")


def delete_matrixstore_bq_table(year, month):
    print("delete_matrixstore_bq_table")
    _delete_table_from_bq("prescribing_export", f"prescribing_{year}_{month}")


def delete_matrixstore_storage_files(year, month):
    print("delete_matrixstore_storage_files")
    _delete_file_from_storage(f"prescribing_exports/prescribing_{year}_{month}")


def delete_matrixstore_download(year, month):
    print("delete_matrixstore_download")
    path = os.path.join(
        settings.PIPELINE_DATA_BASEDIR,
        "matrixstore_import",
        f"{year}-{month}-01_prescribing.csv.gz",
    )
    os.remove(path)


def _delete_file_from_storage(path):
    client = StorageClient()
    bucket = client.get_bucket()
    for blob in bucket.list_blobs(prefix=path):
        blob.delete()


def _delete_table_from_bq(dataset_name, table_name):
    client = BQClient(dataset_name)
    client.delete_table(table_name)
