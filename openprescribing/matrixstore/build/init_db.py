"""
Sets up a SQLite database ready to have prescribing data and practice
statistics imported into it.

Data on practices and presentations is obtained by connecting to BigQuery.
"""
import logging
import os
import sqlite3

from gcutils.bigquery import Client

from .common import get_temp_filename
from .dates import generate_dates


logger = logging.getLogger(__name__)


SCHEMA_SQL = """
    CREATE TABLE presentation (
        bnf_code TEXT,
        is_generic BOOLEAN,
        adq_per_quantity FLOAT,
        name TEXT,
        -- The below columns will contain the actual prescribing data as
        -- serialized matrices of shape (number of practices, number of months)
        items BLOB,
        quantity BLOB,
        actual_cost BLOB,
        net_cost BLOB,

        PRIMARY KEY (bnf_code)
    );

    CREATE TABLE practice_statistic (
        name TEXT,
        -- The "value" column will contain the actual statistics as serialized
        -- matrices of shape (number of practices, number of months)
        value BLOB,

        PRIMARY KEY (name)
    );

    -- Maps each practice code to its corresponding row offset in the data matrix
    CREATE TABLE practice (
        offset INTEGER,
        code TEXT UNIQUE,

        PRIMARY KEY (offset)
    );

    -- Maps each date to its corresponding column offset in the data matrix
    CREATE TABLE date (
        offset INTEGER,
        date TEXT UNIQUE,

        PRIMARY KEY (offset)
    );
"""


def init_db(end_date, sqlite_path, months=None):
    if os.path.exists(sqlite_path):
        raise RuntimeError('File already exists at: ' + sqlite_path)
    logger.info('Initialising SQLite database at %s', sqlite_path)
    sqlite_path = os.path.abspath(sqlite_path)
    temp_filename = get_temp_filename(sqlite_path)
    sqlite_conn = sqlite3.connect(temp_filename)
    bq_conn = Client('hscic')
    sqlite_conn.executescript(SCHEMA_SQL)
    dates = generate_dates(end_date, months=months)
    import_dates(sqlite_conn, dates)
    import_practices(bq_conn, sqlite_conn, dates)
    import_presentations(bq_conn, sqlite_conn)
    sqlite_conn.commit()
    sqlite_conn.close()
    os.rename(temp_filename, sqlite_path)


def import_dates(sqlite_conn, dates):
    sqlite_conn.executemany(
        'INSERT INTO date (offset, date) VALUES (?, ?)',
        enumerate(dates)
    )


def import_practices(bq_conn, sqlite_conn, dates):
    """
    Query BigQuery for the list of practice codes which prescribed during this
    time period and write them to SQLite
    """
    # We only create practice entries for practices which have prescribed in
    # the current date range.  The stored matrices are sparse, so having
    # "empty" practice rows doesn't make much difference there. But when we
    # start summing and processing these we use dense matrices and so it's
    # better to cut down the number of rows to a minimum.
    date_start = min(dates)
    date_end = max(dates)
    logger.info(
        'Querying practice codes which prescribed between %s and %s',
        date_start,
        date_end
    )
    sql = (
        """
        SELECT DISTINCT practice FROM {hscic}.prescribing
          WHERE month >= TIMESTAMP('%s') AND month <= TIMESTAMP('%s')
          ORDER BY practice
        """
    )
    result = bq_conn.query(sql % (date_start, date_end))
    practice_codes = [row[0] for row in result.rows]
    logger.info('Writing %s practice codes to SQLite', len(practice_codes))
    sqlite_conn.executemany(
        'INSERT INTO practice (offset, code) VALUES (?, ?)',
        enumerate(practice_codes)
    )


def import_presentations(bq_conn, sqlite_conn):
    """
    Query BigQuery for BNF codes and metadata on all presentations and insert
    into SQLite
    """
    # Unlike with practices above, it costs very little to have BNF codes in
    # the database which are not prescribed against. And we don't actually know
    # which codes are and aren't used until we apply the "BNF map" which
    # translates old codes into new codes.
    logger.info('Querying all presentation metadata')
    result = bq_conn.query(
        """
        SELECT bnf_code, is_generic, adq_per_quantity, name
          FROM {hscic}.presentation
          ORDER BY bnf_code
        """
    )
    rows = result.rows
    logger.info('Writing %s presentations to SQLite', len(rows))
    sqlite_conn.executemany(
        """
        INSERT INTO presentation
          (bnf_code, is_generic, adq_per_quantity, name)
          VALUES (?, ?, ?, ?)
        """,
        rows
    )
