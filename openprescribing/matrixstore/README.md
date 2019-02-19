# MatrixStore


## Overview

The MatrixStore is a slightly unusual data storage technique which
allows us to cram relatively large amounts of data into a SQLite file
and query it rapidly. This makes it possible to run certain queries live
in the web application which previously we had to pre-compute using
BigQuery.

As an illustration, storing 5 years of monthly prescribing data in a
traditional normalised form takes about 52GB in Postgres and about 22GB
in SQLite. In MatrixStore format the same data takes just under 4GB.

Furthermore, a typical "measure" query (which involves fetching values
for every practice and month over a certain set of presentations) takes
over a minute to run against a traditionally structured database, but
only a few hundred miliseconds using the MatrixStore.

The core idea of the MatrixStore is that we store some of our data in
numpy matrices which are then serialized and stored as binary blobs in
SQLite. We can then define custom SQL functions in SQLite which can
accept these serialized matrices and perform operations on them (e.g sum
them together). This allows us to write SQL queries which do large
amounts of number crunching very fast.

The [PyArrow](https://arrow.apache.org/docs/python/) library provides
very fast serialization and deserialization of numpy objects. We use
[SciPy sparse matrices](https://docs.scipy.org/doc/scipy/reference/sparse.html)
to reduce storage requirements where data is sparse. And we use the
[zstandard](https://github.com/indygreg/python-zstandard) compression
library to further reduce space on disk.


## Querying data

Look in the [init_db](./build/init_db.py) file for an overview of the
schema of the SQLite files we create.

To convert a binary blob back into a matrix, call `deserialize` on it:

```python
import sqlite3
from matrixstore.serializer import deserialize

conn = sqlite3.connect('matrixstore_file.sqlite')
results = conn.execute(
    'SELECT items FROM presentation WHERE items IS NOT NULL LIMIT 1'
)
value = list(results)[0][0]
matrix = deserialize(value)
print(matrix)
```


## Building a MatrixStore SQLite file

MatrixStore files are created by calling the management command:

```sh
./manage.py matrixstore_build 2018-10 my_matrixstore_file.sqlite
```

**Note**: this can take several hours to run.

All data to build the file is sourced entirely from BigQuery (the
command doesn't even connect to Postgres). This is done through a
multi-step process which involves downloading various bits of CSV to
disk. Files are split up by month and are kept around after the command
finishes so that we don't need to re-download 60 months of data each
time we build a new file.

For an overview of the process, see the source for
[matrixstore_build](./management/commands/matrixstore_build.py).
