import csv


# `csv.writer` wants a file-like object to write its output to, but we just
# want to grab each line of output as it's written. Rather than mess around
# with StringIO we can just give it an ordinary list, but with its `append`
# method aliased to `write` and then we can pop the lines off after
# `csv.writer` has written them
class ListFile(list):
    write = list.append


def dicts_to_csv(dicts):
    """
    Takes an interable of dictionaries (assumed to all have the same keys) and
    returns an iterable of strings in CSV format. The first line contains
    headers, which are the dictionary keys.
    """
    lines = ListFile()
    writer = None
    for dictionary in dicts:
        if not writer:
            fieldnames = dictionary.keys()
            writer = csv.DictWriter(lines, fieldnames)
            writer.writeheader()
            yield lines.pop()
        writer.writerow(dictionary)
        yield lines.pop()
