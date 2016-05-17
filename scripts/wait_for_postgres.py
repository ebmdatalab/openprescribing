"""Wait up to 30 seconds for postgres to be available.

This is useful when running in docker, as the first time we create a
postgres volume it takes a few seconds to become ready.

"""
import time
from os import environ
import psycopg2

if __name__ == '__main__':
    elapsed = 0
    while elapsed < 30:
        try:
            psycopg2.connect(
                host=environ['DB_HOST'],
                user=environ['DB_USER'],
                password=environ['DB_PASS'],
                database=environ['DB_NAME'])
            break
        except (psycopg2.OperationalError):
            if elapsed == 0:
                print "Waiting for postgres to start..."
            time.sleep(1)
            elapsed += 1
