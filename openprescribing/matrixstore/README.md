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


## How data is structured

The [init_db](./build/init_db.py) contains the schema for the SQLite
files we create. This contains several columns of BLOB type, which are
designed to hold serialized matrices. These matrices may be of different
types (some integer, some floats, some sparse, some dense) but they will
all have the same shape which is: one row for each practice, and one
column for each date.

The row offset for each practice is stored in the `practice` table, and
the column offset for each date is stored in the `date` table.

So, as a simple illustration, the input data:

date | practice | quantity | items
-- | -- | -- | --
date 1 | practice 1 | 10 | 1
date 1 | practice 2 | 20 | 2
date 2 | practice 1 | 10 | 1
date 2 | practice 2 | 30 | 3

would become two matrices, `quantity` and `items`, like this:

  | practice 1 | practice 2
-- | -- | --
date 1 | 10 | 20
date 2 | 10 | 30

  | practice 1 | practice 2
-- | -- | --
date 1 | 1 | 2
date 2 | 1 | 3


### Worked example

Suppose you want to know how many items were prescribed for BNF code
010203040AAAAAA in practice ABC001 during 2018-06.

First, find the row in the `presentation` table with `bnf_code =
'010203040AAAAAA'` and get the binary blob stored in the `items` column.

Deserialize the binary blob into a matrix (using `matrixstore.serializer.deserialize`).

Next, find the row in the `practice` table with `code = 'ABC001'` and
get the value of the `offset` column. This is the row offset of that
practice within the matrix.

Then find the row in the `date` table with `date = '2018-06-01'` and get
the value in the `offset` column. This is the column offset for that
date within the matrix.

The value we want is then found at: `matrix[row_offset, column_offset]`

Of course, this seems like a very convoluted process for getting a
single value for a single practice on a single date. But usually we
don't want just a single value; we want the values for all practices
across all dates so we can compare values across the country and across
time. And for this use case, the matrix is an incredibly efficient means
of storing and accessing this data.


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


## Python 3 upgrade notes

When we upgrade to Python 3, various bits of this code can be simplified
or improved:
 * The various references to `sqlite3.Binary` can be removed. For
   whatever reason, the sqlite3 module in Python 3 can handle the
   buffer/bytes objects as they are.
 * We can remove the `to_pybytes` call in `serialize` for the same
   reason.
 * We can use the `uri` option to `sqlite3.connect` to open the file in
   immutable mode:
   ```python
   encoded_path = urllib.parse.quote(os.path.abspath(path))
   self.connection = sqlite3.connect(
       'file://{}?immutable=1&mode=ro'.format(encoded_path),
       uri=True,
       check_same_thread=False
   )
   ```
   This should improve performance a bit when we have lots of
   simultaneous requests, but more importantly it opens up the possiblity
   of allowing users to make arbitrary SQL queries through the web
   interface as it guarantees that the connection is read-only.
