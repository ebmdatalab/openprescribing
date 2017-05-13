import errno
import argparse
import glob
import os


class BaseCommand(object):
    def __init__(self):
        self.base_parser = argparse.ArgumentParser(add_help=False)
        self.base_parser.add_argument(
            '--verbose', action='store_true')
        self.add_arguments(self.base_parser)
        self.args = self.base_parser.parse_args()

    def add_arguments(self, parser):
        """Override in subclasses as needed
        """
        pass

    def most_recent_file(self, path):
        return sorted(glob.glob("%s/*/*" % path))[-1]

    def extension_to_uppercase(self, path, suffix):
        for name in glob.glob("%s/*.%s" % (path, suffix.lower())):
            os.rename(
                name,
                "%s.%s" % (name[:-(len(suffix)+1)], suffix.upper())
            )

    def mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise
