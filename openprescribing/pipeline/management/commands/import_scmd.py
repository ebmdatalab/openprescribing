import csv
import re
import tempfile

import requests
from django.core.management import BaseCommand
from gcutils.bigquery import Client, build_schema
from google.cloud.exceptions import Conflict

SCHEMA = build_schema(
    ("file_type", "STRING"),
    ("year_month", "DATE"),
    ("ods_code", "STRING"),
    ("vmp_snomed_code", "STRING"),
    ("vmp_product_name", "STRING"),
    ("unit_of_measure_identifier", "STRING"),
    ("unit_of_measure_name", "STRING"),
    ("total_quanity_in_vmp_unit", "FLOAT"),
    ("indicative_cost", "FLOAT"),
)


class Command(BaseCommand):
    help = "Import any SCMD datasets missing from our BigQuery dataset"

    def ensure_dataset_exists(self, client):
        try:
            client.create_dataset()
        except Conflict:
            pass

    def handle(self, *args, **kwargs):
        s = requests.Session()

        # Get URLs keyed by the date (year-month) they're for
        urls = set(self.iter_dataset_urls(s))
        urls_by_month = dict(self.iter_months(urls))

        # set up the BigQuery client, dataset, and table
        client = Client(dataset_key="scmd")
        self.ensure_dataset_exists(client)
        table = client.get_or_create_table("scmd", schema=SCHEMA)

        # look for existing months in BigQuery
        sql = "SELECT DISTINCT year_month FROM {};".format(table.qualified_name)
        known_dates = [r[0] for r in client.query(sql).rows]

        # convert the datetime.dates the query gives us to strings since
        # that's what we're dealing with elsewhere.
        known_months = {d.strftime("%Y-%m") for d in known_dates}
        print(known_months)

        missing_months = set(urls_by_month.keys()) - known_months
        print("Missing months: {}".format(", ".join(sorted(missing_months))))
        pending_urls = {m: urls_by_month[m] for m in missing_months}

        # abort if there's nothing to get
        if not pending_urls:
            print("no pending urls, aborting")
            return

        # grab missing months
        for month, url in sorted(pending_urls.items()):
            print("{} | Getting: {}".format(month, url))
            r = s.get(url)
            r.raise_for_status()
            print("{} | Downloaded: {}".format(month, url))

            # read CSV into memory
            decoded_content = r.content.decode("utf-8")
            reader = csv.reader(decoded_content.splitlines(), delimiter=",")

            # remove headers
            next(reader)

            # use a tempfile so we can write the CSV to disk with necessary
            # changes (adding days to the year-month dates at time of writing),
            # before uploading from that file to BigQuery.
            with tempfile.NamedTemporaryFile(mode="w+") as f:
                writer = csv.writer(f, delimiter=",")
                for line in reader:
                    # Convert year-month dates to year-month-day
                    if len(line[0]) == 7:
                        line[0] = line[0] + "-01"
                    elif len(line[0]) == 6:
                        line[0] = line[0][:4] + "-" + line[0][4:6] + "-01"
                    else:
                        assert False, line[0]
                    writer.writerow(line)
                print("{} | Wrote: {}".format(month, f.name))

                # rewind the file so we can read it into BigQuery
                f.seek(0)

                # insert into BigQuery
                table.insert_rows_from_csv(
                    f.name, SCHEMA, write_disposition="WRITE_APPEND"
                )
                print("{} | Ingested into BigQuery".format(month))

    def iter_dataset_urls(self, session):
        """Extract CSV file URLs via the API"""
        dataset_name = "secondary-care-medicines-data-indicative-price"
        dataset_url = (
            f"https://opendata.nhsbsa.net/api/3/action/package_show?id={dataset_name}"
        )

        r = session.get(dataset_url)
        r.raise_for_status()

        data = r.json()
        resources = data["result"]["resources"]

        pattern = r"scmd_(final|provisional|wip)_[0-9]{6}\.csv"

        for resource in resources:
            if resource["format"].upper() == "CSV" and re.search(
                pattern, resource["url"].split("/")[-1]
            ):
                yield resource["url"]

    def iter_months(self, urls):
        """
        Extract a "month" and file type from each URL given.

        URLs are expected to end in the format `/scmd_<file_type>_<year><month>.csv`, from
        that we get the year and month, converting them to the format
        <year>-<month> and the file type.
        """
        pattern = r"scmd_(final|provisional|wip)_([0-9]{4})([0-9]{2})\.csv"
        for url in urls:
            match = re.search(pattern, url.split("/")[-1])
            if match:
                file_type, year, month = match.groups()
                # Split up dates with hyphens and add a day to match what we put
                # into BigQuery.
                yield f"{year}-{month}", file_type, url
            else:
                raise ValueError(f"Unexpected URL format: {url}")