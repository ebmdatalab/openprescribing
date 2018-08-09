import csv
import os
import tempfile

from django.db import connection


class TableDumper(object):
    def __init__(self, model, columns, transfomer=None):
        self.model = model
        self.columns = columns
        self.transfomer = transfomer or (lambda row: row)

    def dump_to_file(self, out_f):
        table_name = self.model._meta.db_table

        sql = "COPY %s(%s) TO STDOUT (FORMAT CSV, NULL '')" % (
            table_name, ",".join(self.columns))

        # We open the temporary file twice, because copy_expert expects to be
        # able to write bytes (the default for NamedTemporaryFile)...
        with tempfile.NamedTemporaryFile(delete=False) as tmp_f_b:
            with connection.cursor() as c:
                c.copy_expert(sql, tmp_f_b)
            tmp_f_b.seek(0)

        # ...while csv.reader expects to be able to read text (the default for
        # open).
        with open(tmp_f_b.name) as tmp_f_t:
            reader = csv.reader(tmp_f_t)
            writer = csv.writer(out_f)

            for row in reader:
                writer.writerow(self.transfomer(row))

        os.unlink(tmp_f_b.name)
