from contextlib import contextmanager
from os import environ
import hashlib
import logging
from titlecase import titlecase
import uuid

from django.core.exceptions import ImproperlyConfigured
from django import db

logger = logging.getLogger(__name__)


def nhs_abbreviations(word, **kwargs):
    if word.upper() in ('NHS', 'CCG', 'GP'):
        return word.upper()


def nhs_titlecase(words):
    return titlecase(words, callback=nhs_abbreviations)


def get_env_setting(setting, default=None):
    """ Get the environment setting.

    Return the default, or raise an exception if none supplied
    """
    try:
        return environ[setting]
    except KeyError:
        if default:
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
