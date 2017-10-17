from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from os import environ
from titlecase import titlecase
import argparse
import hashlib
import html2text
import logging
import re
import uuid

from django.core.exceptions import ImproperlyConfigured
from django import db

logger = logging.getLogger(__name__)


def nhs_abbreviations(word, **kwargs):
    if len(word) == 2 and word.lower() not in [
            'at', 'of', 'in', 'on', 'to', 'is', 'me', 'by', 'dr', 'st']:
        return word.upper()
    elif word.lower() in ['dr', 'st']:
        return word.title()
    elif word.upper() in ('NHS', 'CCG', 'PMS', 'SMA', 'PWSI', 'OOH', 'HIV'):
        return word.upper()
    elif '&' in word:
        return word.upper()
    elif ((word.lower() not in ['ptnrs', 'by', 'ccgs']) and
          (not re.match(r'.*[aeiou]{1}', word.lower()))):
        return word.upper()


def get_columns_for_select(measure, num_or_denom=None):
    """Parse measures definition for SELECT columns; add
    cost-savings-related columns when necessary.

    """
    assert num_or_denom in ['numerator', 'denominator']
    fieldname = "%s_columns" % num_or_denom
    cols = measure[fieldname][:]
    # Deal with possible inconsistencies in measure definition
    # trailing commas
    if cols[-1].strip()[-1] != ',':
        cols[-1] += ", "
    if measure['is_cost_based']:
        cols += ["SUM(items) AS items, ",
                 "SUM(actual_cost) AS cost, ",
                 "SUM(quantity) AS quantity "]
    # Deal with possible inconsistencies in measure definition
    # trailing commas
    if cols[-1].strip()[-1] == ',':
        cols[-1] = re.sub(r',\s*$', '', cols[-1])
    return cols


def nhs_titlecase(words):
    if words:
        title_cased = titlecase(words, callback=nhs_abbreviations)
        words = re.sub(r'Dr ([a-z]{2})', 'Dr \1', title_cased)
    return words


def email_as_text(html):
    text_maker = html2text.HTML2Text()
    text_maker.images_to_alt = True
    text_maker.asterisk_emphasis = True
    text_maker.wrap_links = False
    text_maker.pad_tables = True
    text_maker.ignore_images = True
    text = text_maker.handle(html)
    return text


def get_env_setting(setting, default=None):
    """ Get the environment setting.

    Return the default, or raise an exception if none supplied
    """
    try:
        return environ[setting]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = "Set the %s env variable" % setting
            raise ImproperlyConfigured(error_msg)


def under_test():
    return db.connections.databases['default']['NAME'].startswith("test_")


@contextmanager
def constraint_and_index_reconstructor(table_name):
    """A context manager that drops indexes and constraints on the
    specified table, yields, then recreates them.

    According to postgres documentation, when doing bulk loads, this
    should be faster than having the indexes update during the insert.

    See https://www.postgresql.org/docs/current/static/populate.html
    for more.

    """
    with db.connection.cursor() as cursor:

        # Record index and constraint definitions
        indexes = {}
        constraints = {}

        # Build lists of current constraints and indexes
        cursor.execute(
            "SELECT conname, pg_get_constraintdef(c.oid) "
            "FROM pg_constraint c "
            "JOIN pg_namespace n "
            "ON n.oid = c.connamespace "
            "WHERE contype IN ('f', 'p','c','u') "
            "AND conrelid = '%s'::regclass "
            "ORDER BY contype;" % table_name)
        for name, definition in cursor.fetchall():
            constraints[name] = definition
        cursor.execute(
            "SELECT indexname, indexdef "
            "FROM pg_indexes "
            "WHERE tablename = '%s';" % table_name)
        for name, definition in cursor.fetchall():
            if name not in constraints.keys():
                # UNIQUE constraints actuall create indexes, so
                # we mustn't attempt to handle them twice
                indexes[name] = definition

        # drop foreign key constraints
        for name in constraints.keys():
            cursor.execute(
                "ALTER TABLE %s DROP CONSTRAINT %s"
                % (table_name, name))

        # drop indexes
        logger.info("Dropping indexes")
        for name in indexes.keys():
            cursor.execute("DROP INDEX %s" % name)
            logger.info("Dropped index %s" % name)

        logger.info("Running wrapped command")
        yield

        # we're updating everything. This takes 52 minutes.
        # restore indexes
        logger.info("Recreating indexes")
        for name, cmd in indexes.items():
            cursor.execute(cmd)
            logger.info("Recreated index %s" % name)

        logger.info("Recreating constraints")
        # restore foreign key constraints
        for name, cmd in constraints.items():
            cmd = ("ALTER TABLE %s "
                   "ADD CONSTRAINT %s %s" % (table_name, name, cmd))
            cursor.execute(cmd)
            logger.info("Recreated constraint %s" % name)
        sql = """
        SELECT
          i.relname AS index_for_cluster
        FROM
          pg_index AS idx
        JOIN
          pg_class AS i
        ON
          i.oid = idx.indexrelid
        WHERE
          idx.indisclustered
          AND idx.indrelid::regclass = '%s'::regclass;
        """
        cursor.execute(sql % table_name)
        if cursor.fetchone():
            cursor.execute("CLUSTER %s" % table_name)
            logger.info("CLUSTERED %s" % table_name)


def google_user_id(user):
    if user:
        h = hashlib.md5()
        h.update(str(user.id))
        client_id = str(uuid.UUID(h.hexdigest()))
    else:
        client_id = None
    return client_id


def valid_date(s):
    """Validate ISO-formatted dates. For use in argparse arguments.
    """
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]
