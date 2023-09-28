# coding=utf8

import datetime
import logging
import re
from collections import defaultdict

import bs4
import requests
from django.core.management import BaseCommand
from django.db import transaction
from dmd.models import VMPP
from frontend.models import NCSOConcession
from gcutils.bigquery import Client

from openprescribing.slack import notify_slack

logger = logging.getLogger(__file__)

# This page is the newsletter archive for PSNC System Supplier emails. It extends
# further back in time than the RSS feed, hence it is useful for testing that we can
# import historical data but doesn't have a role in regular imports.
ARCHIVE_URL = (
    "https://us7.campaign-archive.com/home/?u=86d41ab7fa4c7c2c5d7210782&id=63383868f3"
)

# This is the RSS feed for the above mailing list. As it contains the email contents
# inline it's easier to work with this than that archive index.
RSS_URL = (
    "https://us7.campaign-archive.com/feed?u=86d41ab7fa4c7c2c5d7210782&id=63383868f3"
)

DEFAULT_HEADERS = {
    "User-Agent": "OpenPrescribing-Bot (+https://openprescribing.net)",
}


# Match strings like "March 2020 Price Concessions"
MONTH_DATE_RE = re.compile(
    r"""
    (?P<month>
        january | february | march | april | may | june | july | august |
        september | october | november | december
    )
    \s+
    (?P<year> 20\d\d)
    \s+ price \s+ concessions
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Match strings like "Concessions Announcement Wednesday 15th March 2023"
PUBLISH_DATE_RE = re.compile(
    r"""
    concessions \s+ announcement \s+
    (
      ( monday | tuesday | wednesday | thursday | friday | saturday | sunday )
      \s+
    ) ?
    (?P<day> \d+) \s* ( st | nd | rd | th )
    \s+
    (?P<month>
        january | february | march | april | may | june | july | august |
        september | october | november | december
    )
    \s+
    (?P<year> 20\d\d)
    """,
    re.VERBOSE | re.IGNORECASE,
)

UNPARSEABLE_URLS = {
    # Contains an announcement of a withdrawal and no tables
    "https://mailchi.mp/cpe/atomoxetine-18mg-capsules-updated-reimbursement-price-for-august-2023"
}

# Singleton to use for withdrawn concessions
WITHDRAWN = object()


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # Fetch and parse the concession data
        response = requests.get(RSS_URL, headers=DEFAULT_HEADERS)
        items = parse_concessions_from_rss(response.content)

        # Find matching VMPPs for each concession, where possible
        vmpp_id_to_name = get_vmpp_id_to_name_map()
        matched = match_concession_vmpp_ids(items, vmpp_id_to_name)

        # Where the PSNC announce corrections in non-standard channels we need to
        # incorporate these manually
        matched = add_manual_corrections(matched)

        # Insert into database
        inserted = insert_or_update(matched)

        # Upload to BigQuery
        Client("dmd").upload_model(NCSOConcession)

        # Report results
        msg = format_message(inserted)
        notify_slack(msg)


def parse_concessions_from_rss(feed_content):
    feed = bs4.BeautifulSoup(feed_content, "xml")
    for item in feed.find_all("item"):
        url = item.find("link").string
        item_content = item.find("content:encoded").string
        yield from parse_concessions_from_html(item_content, url=url)


def parse_concessions_from_archive():  # pragma: no cover
    archive_html = requests.get(ARCHIVE_URL).content
    doc = bs4.BeautifulSoup(archive_html, "html.parser")
    for li in doc.find_all("li", class_="campaign"):
        url = li.find("a")["href"]
        response = requests.get(url)
        yield from parse_concessions_from_html(response.content, url=response.url)


def parse_concessions_from_html(html, url=None):
    if url in UNPARSEABLE_URLS:
        return
    doc = bs4.BeautifulSoup(html, "html.parser")
    # Find the publication date
    publish_date = get_single_item(
        parse_date(f"{match['day']} {match['month']} {match['year']}")
        for match in PUBLISH_DATE_RE.finditer(doc.text)
    )
    # Find the month for which these concessions apply
    date = get_single_item(
        parse_date(f"1 {match['month']} {match['year']}")
        for match in MONTH_DATE_RE.finditer(doc.text)
    )
    # Find the table containing the "Pack Size" header
    table = get_single_item(
        td.find_parent("table")
        for td in doc.find_all("td")
        if (td.text or "").strip().lower() == "pack size"
    )
    rows = rows_from_table(table)
    headers = next(rows)
    assert [s.lower() for s in headers][:3] == [
        "drug",
        "pack size",
        "price concession",
    ]
    for row in rows:
        # Sometimes all-blank rows are used as spacers
        if all(v == "" for v in row):
            continue
        # Sometimes colspans are used to inject section headings
        if len(row) < 3:
            continue
        # After a section heading we usually see the column headings repeated again
        if row == headers:
            continue
        yield {
            "url": url,
            "date": date,
            "publish_date": publish_date,
            "drug": row[0],
            "pack_size": row[1],
            "price_pence": parse_price(row[2]),
            "supplied_vmpp_id": int(row[3]) if len(row) == 4 else None,
        }


def get_single_item(iterator):
    unique = set(iterator)
    assert len(unique) == 1, f"Expected exactly one item, got: {unique}"
    return list(unique)[0]


def parse_date(date_str):
    # Parses dates like "1 January 2020"
    return datetime.datetime.strptime(date_str, "%d %B %Y").date()


def rows_from_table(table):
    for tr in table.find_all("tr"):
        yield [fix_spaces(td.text or "") for td in tr.find_all("td")]


def fix_spaces(s):
    """Remove extra spaces and convert non-breaking spaces to normal ones."""

    s = s.replace("\xa0", " ")
    s = s.strip()
    s = re.sub(" +", " ", s)
    return s


def parse_price(price_str):
    # Correct typo. If these happen more regularly we'll need to take a different
    # approach but I want to be maximally conservative to begin with.
    if price_str == "11..35":
        price_str = "£11.35"
    match = re.fullmatch(r"£(\d+)\.(\d\d)", price_str)
    return int(match[1]) * 100 + int(match[2])


def match_concession_vmpp_ids(items, vmpp_id_to_name):
    # Build mapping from regularised names to VMPPs. Most such names map to just one
    # VMPP, but there are some ambiguous cases.
    regular_name_to_vmpp_ids = defaultdict(list)
    for vmpp_id, name in vmpp_id_to_name.items():
        regular_name_to_vmpp_ids[regularise_name(name)].append(vmpp_id)

    matched = []

    for item in items:
        supplied_name = f"{item['drug']} {item['pack_size']}"
        supplied_vmpp_name = vmpp_id_to_name.get(item["supplied_vmpp_id"])

        # If the names match then we assume that the supplied VMPP ID is correct
        if regularise_name(supplied_name) == regularise_name(supplied_vmpp_name):
            item["vmpp_id"] = item["supplied_vmpp_id"]
        else:
            # Otherwise we try to find other matches by names
            matched_vmpp_ids = regular_name_to_vmpp_ids[regularise_name(supplied_name)]
            # If there's an unambiguous match then we assume that is the correct VMPP
            if len(matched_vmpp_ids) == 1:
                item["vmpp_id"] = matched_vmpp_ids[0]
            # Finally, we check if we've previously manually reconciled this concession
            # to a VMPP then re-use that ID if so
            else:
                item["vmpp_id"] = get_vmpp_id_from_previous_concession(
                    item["drug"], item["pack_size"]
                )

        # Record the original names associated with both supplied and matched VMPP ID
        item["supplied_vmpp_name"] = supplied_vmpp_name
        item["vmpp_name"] = vmpp_id_to_name.get(item["vmpp_id"])

        matched.append(item)

    return matched


def get_vmpp_id_to_name_map():
    # Build mapping from ID to name for all valid VMPPs. We only want VMPPs which are
    # not marked as "invalid" and which we can match to prescribing data. See:
    # https://github.com/ebmdatalab/openprescribing/issues/3978
    return {
        vmpp_id: name
        for vmpp_id, name in VMPP.objects.filter(bnf_code__isnull=False)
        .exclude(invalid=True)
        .values_list("id", "nm")
    }


def regularise_name(name):
    if name is None:
        return

    # dm+d uses "microgram" or "micrograms", usually with these rules
    name = name.replace("mcg ", "microgram ")
    name = name.replace("mcg/", "micrograms/")

    # dm+d uses "microgram" rather than "0.X.mg"
    name = name.replace("0.5mg", "500microgram")
    name = name.replace("0.25mg", "250microgram")

    # dm+d uses "square cm"
    name = name.replace("sq cm", "square cm")

    # dm+d records measured in mg/ml have a space before the final "ml"
    # eg: Abacavir 20mg/ml oral solution sugar free 240 ml
    name = re.sub(r"(\d)ml$", r"\1 ml", name)

    # dm+d records have "gram$" not "g$"
    # eg: Estriol 0.01% cream 80 gram
    name = re.sub(r"(\d)g$", r"\1 gram", name)

    # Misc. common replacements
    name = name.replace("Oral Susp SF", "oral suspension sugar free")
    name = name.replace("gastro- resistant", "gastro-resistant")
    name = name.replace("/ml", "/1ml")

    # Strip leading asterisks which are sometimes used to indicate the presence of
    # additional notes
    name = re.sub(r"^\s*\*\s*", "", name)

    # Lowercase
    name = name.lower()

    # Remove spaces around slashes
    name = re.sub(" */ *", "/", name)

    # dm+d names often have the units appended after the pack size (e.g. "12 tablets"),
    # we want to remove the units leaving just the "12" so as to match the names we get
    # from the price concessions feed. Note that this can, in rare cases, result in
    # ambiguities. Where these arise we say that we are unable to find a matching name,
    # rather than arbitrarily picking one. See:
    # https://github.com/ebmdatalab/openprescribing/issues/3979
    name = re.sub(r"(\d+) [^\d]+$", r"\1", name)

    return name


def get_vmpp_id_from_previous_concession(drug, pack_size):
    previous_vmpp_ids = list(
        NCSOConcession.objects.filter(
            drug=drug, pack_size=pack_size, vmpp__isnull=False
        ).values_list("vmpp_id", flat=True)
    )
    if previous_vmpp_ids:
        return get_single_item(previous_vmpp_ids)


def add_manual_corrections(items):
    # Where the PSNC announce corrections in non-standard channels we need to
    # incorporate these manually
    if any(i["date"] == datetime.date(2023, 4, 1) for i in items):
        items.append(
            {
                "url": "https://psnc.org.uk/our-news/price-concession-update-for-april-2023-chlorphenamine-2mg-5ml-oral-solution/",
                "publish_date": datetime.date(2023, 5, 10),
                "date": datetime.date(2023, 4, 1),
                "vmpp_id": 1240211000001107,
                "supplied_vmpp_id": 1240211000001107,
                "drug": "Chlorphenamine 2mg/5ml oral solution",
                "pack_size": "150",
                "price_pence": 334,
            }
        )
    if any(i["date"] == datetime.date(2023, 7, 1) for i in items):
        items.append(
            {
                "url": "https://cpe.org.uk/our-news/price-improvement-for-atorvastatin-80mg-dispensed-in-july-2023/",
                "publish_date": datetime.date(2023, 8, 9),
                "date": datetime.date(2023, 7, 1),
                "vmpp_id": 1161411000001107,
                "supplied_vmpp_id": 1161411000001107,
                "drug": "Atorvastatin 80mg tablets",
                "pack_size": "28",
                "price_pence": 391,
            }
        )
    for item in items:
        if (
            item["date"] == datetime.date(2023, 6, 1)
            and item["vmpp_id"] == 1140011000001100
            and item["price_pence"] == 219
        ):
            item.update(
                {
                    "url": "https://cpe.org.uk/our-news/june-2023-price-concessions-2nd-update/",
                    "price_pence": 448,
                }
            )
    for item in items:
        if (
            item["date"] == datetime.date(2023, 8, 1)
            and item["vmpp_id"] == 7649311000001108
        ):
            item.update(
                {
                    "url": "https://mailchi.mp/cpe/atomoxetine-18mg-capsules-updated-reimbursement-price-for-august-2023",
                    "publish_date": datetime.date(2023, 8, 31),
                    "price_pence": WITHDRAWN,
                }
            )

    return items


def insert_or_update(items):
    # Sort by published date so most recent prices are always applied last
    items = sorted(items, key=lambda i: i["publish_date"])

    inserted = []
    with transaction.atomic():
        for item in items:
            if item["price_pence"] is WITHDRAWN:
                assert item["vmpp_id"] is not None
                NCSOConcession.objects.filter(
                    date=item["date"], vmpp_id=item["vmpp_id"]
                ).delete()
                created = False
            elif item["vmpp_id"] is not None:
                _, created = NCSOConcession.objects.update_or_create(
                    date=item["date"],
                    vmpp_id=item["vmpp_id"],
                    defaults=dict(
                        drug=item["drug"],
                        pack_size=item["pack_size"],
                        price_pence=item["price_pence"],
                    ),
                )
            else:
                # Unmatched concessions get inserted as placeholder entries, ready for
                # manual reconciliation
                _, created = NCSOConcession.objects.update_or_create(
                    date=item["date"],
                    drug=item["drug"],
                    pack_size=item["pack_size"],
                    vmpp_id=None,
                    defaults=dict(
                        price_pence=item["price_pence"],
                    ),
                )

            item["created"] = created
            inserted.append(item)
            if created:
                logger.info("Creating {drug} {pack_size} {price_pence}".format(**item))

    return inserted


def format_message(inserted):
    created = [i for i in inserted if i["created"]]
    unmatched = [i for i in inserted if i["vmpp_id"] is None]
    new_mismatched = [
        i
        for i in inserted
        if i["vmpp_id"] is not None
        and i["supplied_vmpp_id"] is not None
        and i["vmpp_id"] != i["supplied_vmpp_id"]
        and i["created"]
    ]

    msg = f"Fetched {len(inserted)} concessions. "

    if not created:
        msg += "Found no new concessions to import."
    else:
        msg += f"Imported {len(created)} new concessions."

    # We warn about cases where we couldn't match the drug name and pack size to a VMPP,
    # or where we could match it but the VMPP is different from the one supplied
    if unmatched:
        msg += (
            "\n\n"
            "We could not confirm that the following concessions have correct "
            "VMPP IDs:\n"
        )
        for item in unmatched:
            msg += (
                f"\n"
                f"Name: {item['drug']} {item['pack_size']}\n"
                f"VMPP: https://openprescribing.net/dmd/vmpp/{item['supplied_vmpp_id']}/\n"
                f"From: {item['url']}\n"
            )

    if new_mismatched:
        msg += (
            "\n\n"
            "The following concessions were supplied with incorrect VMPP IDs "
            "but have been automatically corrected:\n"
        )
        for item in new_mismatched:
            msg += (
                f"\n"
                f"Name: {item['drug']} {item['pack_size']}\n"
                f"Supplied VMPP: https://openprescribing.net/dmd/vmpp/{item['supplied_vmpp_id']}/\n"
                f"Matched VMPP: https://openprescribing.net/dmd/vmpp/{item['vmpp_id']}/\n"
                f"From: {item['url']}\n"
            )

    return msg
