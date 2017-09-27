import csv
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

        with tempfile.NamedTemporaryFile() as tmp_f:
            with connection.cursor() as c:
                c.copy_expert(sql, tmp_f)
            tmp_f.seek(0)

            reader = csv.reader(tmp_f)
            writer = csv.writer(out_f)

            for row in reader:
                writer.writerow(self.transfomer(row))
