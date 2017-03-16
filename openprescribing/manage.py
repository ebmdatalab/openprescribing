#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    settings = 'test' if 'test' in sys.argv else 'local'
    os.environ["DJANGO_SETTINGS_MODULE"] = (
        "openprescribing.settings.%s" % settings)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
