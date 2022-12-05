# Create table in BQ with historical practice data in same format as hscic.practice_details.
#
# New table will be at research.practices_yyyy_mm
#
# Run with ./manage.py runscript create_historical_practice_table --script-args yyyy_mm.


import csv
import sys

from google.cloud import bigquery as gcbq
from google.cloud import storage as gcs
from google.cloud.exceptions import Conflict


def run(year_and_month):
    practice_schema = build_schema(
        ("code", "STRING"),
        ("name", "STRING"),
        ("address1", "STRING"),
        ("address2", "STRING"),
        ("address3", "STRING"),
        ("address4", "STRING"),
        ("address5", "STRING"),
        ("postcode", "STRING"),
        ("location", "STRING"),
        ("ccg_id", "STRING"),
        ("pcn_id", "STRING"),
        ("setting", "INTEGER"),
        ("close_date", "STRING"),
        ("join_provider_date", "STRING"),
        ("leave_provider_date", "STRING"),
        ("open_date", "STRING"),
        ("status_code", "STRING"),
    )

    project = "ebmdatalab"

    gcs_client = gcs.Client(project=project)
    gcbq_client = gcbq.Client(project=project)
    bucket = gcs_client.bucket(project)
    blob = bucket.get_blob(
        "hscic/practice_details/{}/epraccur.csv".format(year_and_month)
    )

    with open("epraccur_{}.csv".format(year_and_month), "wb") as f:
        blob.download_to_file(f)

    with open("epraccur_{}.csv".format(year_and_month)) as f:
        rows = list(csv.reader(f))

    new_rows = [
        [
            row[0],  # code
            row[1],  # name
            row[4],  # address1
            row[5],  # address2
            row[6],  # address3
            row[7],  # address4
            row[8],  # address5
            row[9],  # postcode
            None,  # location
            row[23].strip(),  # ccg_id
            None,  # pcn_id
            row[-2],  # setting
            parse_date(row[11]),  # close_date
            parse_date(row[15]),  # join_provider_date
            parse_date(row[16]),  # leave_provider_date
            parse_date(row[10]),  # open_date
            row[12],  # status_code
        ]
        for row in rows
    ]

    with open("epraccur_{}_restructured.csv".format(year_and_month), "w") as f:
        writer = csv.writer(f)
        writer.writerows(new_rows)

    dataset_ref = gcbq_client.dataset("research")
    dataset = gcbq.Dataset(dataset_ref)
    table_ref = dataset.table("practices_{}".format(year_and_month))
    table = gcbq.Table(table_ref, schema=practice_schema)
    try:
        gcbq_client.create_table(table)
    except Conflict:
        pass

    job_config = gcbq.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

    with open("epraccur_{}_restructured.csv".format(year_and_month), "rb") as f:
        job = gcbq_client.load_table_from_file(f, table_ref, job_config=job_config)
        print(job.result())


def build_schema(*fields):
    return [gcbq.SchemaField(*field) for field in fields]


def parse_date(d):
    if d:
        return "-".join([d[:4], d[4:6], d[6:]])


if __name__ == "__main__":
    year_and_month = sys.argv[1]
    run(year_and_month)
