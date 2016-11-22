from contextlib import contextmanager
from os import environ

from django.core.exceptions import ImproperlyConfigured
from django import db


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
        for name in indexes.keys():
            cursor.execute("DROP INDEX %s" % name)
        print "Dropped indexes; running main command"

        yield

        # we're updating everything. This takes 52 minutes.
        # restore indexes
        print "Recreating indexes"
        for cmd in indexes.values():
            cursor.execute(cmd)

        print "Recreating constraints"
        # restore foreign key constraints
        for name, cmd in constraints.items():
            cmd = ("ALTER TABLE %s "
                   "ADD CONSTRAINT %s %s" % (table_name, name, cmd))
            cursor.execute(cmd)
